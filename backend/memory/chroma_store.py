"""
ChromaDB-backed persistent agent memory.
Stores every hypothesis test result as a vector embedding.
Queries to prevent re-testing already-explored hypotheses.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional

CHROMA_PERSIST_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "chroma_db"
)
CHROMA_PERSIST_DIR = os.path.abspath(CHROMA_PERSIST_DIR)
COLLECTION_NAME = "hypothesis_memory"


class AgentMemory:
    """
    Persistent ChromaDB memory for the HypothesizerAgent.
    Each record = one tested hypothesis with its result.
    Embeddings allow semantic deduplication across sessions.
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._initialized = False

    def _init(self):
        """Lazy initialization — only imports chromadb when called."""
        if self._initialized:
            return
        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
            self._client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self._initialized = True
        except ImportError:
            print("[AgentMemory] chromadb not installed. Memory persistence disabled.")
        except Exception as e:
            print(f"[AgentMemory] ChromaDB init failed: {e}. Memory disabled.")

    def _make_id(self, dataset_name: str, hypothesis_title: str) -> str:
        """Stable unique ID for a (dataset, hypothesis) pair."""
        raw = f"{dataset_name}::{hypothesis_title.lower().strip()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _make_document(self, hypothesis: Dict, result: Dict) -> str:
        """Build a text document from hypothesis + result for embedding."""
        parts = [
            f"Dataset: {hypothesis.get('dataset_name', 'unknown')}",
            f"Hypothesis: {hypothesis.get('title', '')}",
            f"Statement: {hypothesis.get('statement', '')}",
            f"Test: {hypothesis.get('test_type', '')}",
            f"Independent: {hypothesis.get('independent_var', '')}",
            f"Dependent: {hypothesis.get('dependent_var', '')}",
            f"Status: {result.get('status', '')}",
            f"P-Value: {result.get('p_value', '')}",
            f"Effect Size: {result.get('effect_size', '')}",
        ]
        return " | ".join(parts)

    def store_result(
        self,
        dataset_name: str,
        hypothesis: Dict[str, Any],
        validated_finding: Dict[str, Any],
    ):
        """Persist a tested hypothesis result into ChromaDB."""
        self._init()
        if not self._initialized or self._collection is None:
            return

        try:
            doc_id = self._make_id(dataset_name, hypothesis.get("title", ""))
            hypothesis_with_ds = {**hypothesis, "dataset_name": dataset_name}
            document = self._make_document(hypothesis_with_ds, validated_finding)

            metadata = {
                "dataset_name": dataset_name,
                "hypothesis_id": hypothesis.get("id", ""),
                "title": hypothesis.get("title", "")[:500],
                "status": validated_finding.get("status", ""),
                "p_value": float(validated_finding.get("p_value", 1.0)),
                "effect_size": float(validated_finding.get("effect_size", 0.0)),
                "test_type": hypothesis.get("test_type", ""),
                "independent_var": hypothesis.get("independent_var", ""),
                "dependent_var": hypothesis.get("dependent_var", ""),
            }

            # Upsert so re-runs don't duplicate
            self._collection.upsert(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata],
            )
        except Exception as e:
            print(f"[AgentMemory] store_result error: {e}")

    def get_tested_hypotheses(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Return all previously tested hypotheses for this dataset."""
        self._init()
        if not self._initialized or self._collection is None:
            return []

        try:
            results = self._collection.get(
                where={"dataset_name": dataset_name},
                include=["metadatas", "documents"],
            )
            return results.get("metadatas", []) or []
        except Exception as e:
            print(f"[AgentMemory] get_tested_hypotheses error: {e}")
            return []

    def query_similar(
        self,
        query_text: str,
        dataset_name: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find semantically similar previously tested hypotheses."""
        self._init()
        if not self._initialized or self._collection is None:
            return []

        try:
            count = self._collection.count()
            if count == 0:
                return []

            results = self._collection.query(
                query_texts=[query_text],
                n_results=min(n_results, count),
                where={"dataset_name": dataset_name} if dataset_name else None,
                include=["metadatas", "distances"],
            )
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            return [
                {**m, "similarity_distance": d}
                for m, d in zip(metadatas, distances)
            ]
        except Exception as e:
            print(f"[AgentMemory] query_similar error: {e}")
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """Return stats about what's stored."""
        self._init()
        if not self._initialized or self._collection is None:
            return {"enabled": False, "total_records": 0}
        try:
            return {
                "enabled": True,
                "total_records": self._collection.count(),
                "persist_dir": CHROMA_PERSIST_DIR,
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# Singleton instance
_memory_instance: Optional[AgentMemory] = None


def get_memory() -> AgentMemory:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = AgentMemory()
    return _memory_instance
