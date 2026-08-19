"""
Autonomous AI Scientist — FastAPI Backend
Full multi-LLM, chart serving, ChromaDB memory, NL query, multi-dataset comparison.
Serves React frontend in production mode.
"""

import asyncio
import json
import os
import sys
import shutil
import uuid
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.orchestrator import ResearchOrchestrator
from agents.profiler import DataProfilerAgent
from agents.nl_interpreter import interpret_nl_query
from llm.provider import LLMProvider, LLMConfigurationError


# ── Directory Setup ────────────────────────────────────────────────────────────
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
WORKSPACE_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
UPLOADS_DIR = os.path.join(WORKSPACE_DIR, "uploads")
CHARTS_DIR = os.path.join(BACKEND_DIR, "charts")
FRONTEND_DIST = os.path.join(WORKSPACE_DIR, "frontend", "dist")

for d in [UPLOADS_DIR, CHARTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Autonomous AI Scientist API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve chart images as static files ────────────────────────────────────────
app.mount("/api/charts", StaticFiles(directory=CHARTS_DIR), name="charts")

# ── In-memory session store ────────────────────────────────────────────────────
sessions: Dict[str, Dict[str, Any]] = {}
event_queues: Dict[str, asyncio.Queue] = {}


# ── Request Models ─────────────────────────────────────────────────────────────
class InvestigateRequest(BaseModel):
    csv_filename: str
    domain_context: Optional[str] = ""
    target_column: Optional[str] = None
    task_type: Optional[str] = None
    llm_model: Optional[str] = "gemini"  # "gemini" | "gpt4o" | "claude"


class NLInterpretRequest(BaseModel):
    query: str
    csv_filename: str
    llm_model: Optional[str] = "gemini"


class CompareRequest(BaseModel):
    csv_filename_a: str
    csv_filename_b: str
    domain_context: Optional[str] = ""
    llm_model: Optional[str] = "gemini"


# ── Helper: resolve CSV path ───────────────────────────────────────────────────
def resolve_csv_path(filename: str) -> str:
    for base in [DATA_DIR, UPLOADS_DIR]:
        p = os.path.join(base, filename)
        if os.path.exists(p):
            return p
    raise HTTPException(status_code=404, detail=f"Dataset file '{filename}' not found.")


# ── Helper: build LLMProvider safely ──────────────────────────────────────────
def get_llm_provider(model_key: Optional[str]) -> Optional[LLMProvider]:
    if not model_key:
        return None
    try:
        return LLMProvider(model=model_key)
    except LLMConfigurationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── API: Status ────────────────────────────────────────────────────────────────
@app.get("/api/status")
def get_status():
    from memory.chroma_store import get_memory
    mem = get_memory()
    return {
        "status": "online",
        "system": "Autonomous AI Scientist Engine v2.0",
        "active_sessions": len(sessions),
        "memory": mem.get_memory_stats(),
        "available_models": LLMProvider.get_available_models(),
    }


# ── API: Available LLM Models ─────────────────────────────────────────────────
@app.get("/api/models")
def list_models():
    return {"models": LLMProvider.get_available_models()}


# ── API: Sample Datasets ───────────────────────────────────────────────────────
@app.get("/api/sample-datasets")
def list_sample_datasets():
    datasets = []
    if os.path.exists(DATA_DIR):
        for f in sorted(os.listdir(DATA_DIR)):
            if f.endswith(".csv"):
                fpath = os.path.join(DATA_DIR, f)
                datasets.append({
                    "name": f,
                    "size_bytes": os.path.getsize(fpath),
                    "path": fpath,
                })
    return {"samples": datasets}


# ── API: Dataset Preview ───────────────────────────────────────────────────────
@app.get("/api/dataset-preview/{filename:path}")
def get_dataset_preview(filename: str):
    csv_path = resolve_csv_path(filename)
    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(csv_path)
    return {"profile": profile}


# ── API: Upload CSV ────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    saved_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    saved_path = os.path.join(UPLOADS_DIR, saved_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(saved_path)

    return {
        "filename": saved_filename,
        "original_name": file.filename,
        "size_bytes": os.path.getsize(saved_path),
        "profile": profile,
    }


# ── API: Natural Language Query Interpretation ────────────────────────────────
@app.post("/api/nl-interpret")
async def nl_interpret(req: NLInterpretRequest):
    csv_path = resolve_csv_path(req.csv_filename)
    llm = get_llm_provider(req.llm_model)

    profiler = DataProfilerAgent()
    profile = profiler.profile_csv(csv_path)

    if llm is None:
        raise HTTPException(
            status_code=422,
            detail="An LLM model with a valid API key is required for natural language query interpretation."
        )

    result = interpret_nl_query(req.query, profile, llm)
    return result


# ── Background Task: Run Orchestrator ────────────────────────────────────────
def run_orchestrator_background(
    session_id: str,
    csv_path: str,
    domain_context: str,
    target_column: Optional[str],
    task_type: Optional[str],
    llm_model: Optional[str],
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
):
    def event_cb(event):
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    orchestrator = ResearchOrchestrator(
        working_dir=WORKSPACE_DIR,
        charts_dir=CHARTS_DIR,
    )

    # Build LLM provider in background thread (no HTTPException here)
    llm_provider = None
    if llm_model:
        try:
            llm_provider = LLMProvider(model=llm_model)
        except LLMConfigurationError as e:
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "stage": "ERROR",
                    "agent": "System",
                    "message": f"LLM Configuration Error: {e}",
                    "timestamp": time.time(),
                }),
                loop,
            )
            sessions[session_id]["status"] = "failed"
            sessions[session_id]["error"] = str(e)
            return
        except Exception as e:
            pass  # Fall back to heuristics

    try:
        results = orchestrator.run_investigation(
            csv_path,
            domain_context=domain_context,
            target_override=target_column,
            task_type_override=task_type,
            llm_provider=llm_provider,
            event_callback=event_cb,
        )
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["results"] = results
        asyncio.run_coroutine_threadsafe(
            queue.put({
                "stage": "COMPLETE",
                "agent": "System",
                "message": "Investigation completed successfully!",
                "timestamp": time.time(),
            }),
            loop,
        )
    except Exception as e:
        sessions[session_id]["status"] = "failed"
        sessions[session_id]["error"] = str(e)
        asyncio.run_coroutine_threadsafe(
            queue.put({
                "stage": "ERROR",
                "agent": "System",
                "message": f"Pipeline Error: {str(e)}",
                "timestamp": time.time(),
            }),
            loop,
        )


# ── API: Start Investigation ───────────────────────────────────────────────────
@app.post("/api/investigate")
async def start_investigation(req: InvestigateRequest, background_tasks: BackgroundTasks):
    csv_path = resolve_csv_path(req.csv_filename)

    session_id = uuid.uuid4().hex[:12]
    queue: asyncio.Queue = asyncio.Queue()
    event_queues[session_id] = queue

    sessions[session_id] = {
        "session_id": session_id,
        "status": "running",
        "csv_filename": req.csv_filename,
        "domain_context": req.domain_context,
        "target_column": req.target_column,
        "task_type": req.task_type,
        "llm_model": req.llm_model,
        "created_at": time.time(),
        "results": None,
    }

    loop = asyncio.get_event_loop()
    background_tasks.add_task(
        run_orchestrator_background,
        session_id,
        csv_path,
        req.domain_context or "",
        req.target_column,
        req.task_type,
        req.llm_model,
        queue,
        loop,
    )

    return {
        "session_id": session_id,
        "status": "running",
        "message": "Scientific investigation started.",
    }


# ── API: SSE Stream ────────────────────────────────────────────────────────────
@app.get("/api/stream/{session_id}")
async def stream_logs(session_id: str):
    if session_id not in event_queues:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = event_queues[session_id]

    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("stage") in ["COMPLETE", "ERROR"]:
                    break
            except asyncio.TimeoutError:
                yield 'data: {"stage": "PING", "message": "keep-alive"}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── API: Get Results ───────────────────────────────────────────────────────────
@app.get("/api/results/{session_id}")
def get_results(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


# ── API: Download Notebook ─────────────────────────────────────────────────────
@app.get("/api/download-notebook/{session_id}")
def download_notebook(session_id: str):
    if session_id not in sessions or not sessions[session_id].get("results"):
        raise HTTPException(status_code=404, detail="Results not ready.")

    nb_path = sessions[session_id]["results"].get("notebook_path")
    if not nb_path or not os.path.exists(nb_path):
        raise HTTPException(status_code=404, detail="Notebook file missing.")

    return FileResponse(
        nb_path,
        media_type="application/x-ipynb+json",
        filename=os.path.basename(nb_path),
    )


# ── API: Multi-Dataset Comparison ─────────────────────────────────────────────
def run_comparison_background(
    session_id: str,
    csv_path_a: str,
    csv_path_b: str,
    domain_context: str,
    llm_model: Optional[str],
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
):
    def event_cb(event):
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    orchestrator = ResearchOrchestrator(
        working_dir=WORKSPACE_DIR,
        charts_dir=CHARTS_DIR,
    )

    llm_provider = None
    if llm_model:
        try:
            llm_provider = LLMProvider(model=llm_model)
        except Exception:
            pass

    try:
        results = orchestrator.run_comparison(
            csv_path_a,
            csv_path_b,
            domain_context=domain_context,
            llm_provider=llm_provider,
            event_callback=event_cb,
        )
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["results"] = results
        asyncio.run_coroutine_threadsafe(
            queue.put({
                "stage": "COMPLETE",
                "agent": "System",
                "message": "Comparison complete!",
                "timestamp": time.time(),
            }),
            loop,
        )
    except Exception as e:
        sessions[session_id]["status"] = "failed"
        sessions[session_id]["error"] = str(e)
        asyncio.run_coroutine_threadsafe(
            queue.put({
                "stage": "ERROR",
                "agent": "System",
                "message": f"Comparison Error: {str(e)}",
                "timestamp": time.time(),
            }),
            loop,
        )


@app.post("/api/compare")
async def start_comparison(req: CompareRequest, background_tasks: BackgroundTasks):
    csv_path_a = resolve_csv_path(req.csv_filename_a)
    csv_path_b = resolve_csv_path(req.csv_filename_b)

    session_id = uuid.uuid4().hex[:12]
    queue: asyncio.Queue = asyncio.Queue()
    event_queues[session_id] = queue

    sessions[session_id] = {
        "session_id": session_id,
        "status": "running",
        "mode": "comparison",
        "csv_filename_a": req.csv_filename_a,
        "csv_filename_b": req.csv_filename_b,
        "created_at": time.time(),
        "results": None,
    }

    loop = asyncio.get_event_loop()
    background_tasks.add_task(
        run_comparison_background,
        session_id,
        csv_path_a,
        csv_path_b,
        req.domain_context or "",
        req.llm_model,
        queue,
        loop,
    )

    return {"session_id": session_id, "status": "running", "message": "Dataset comparison started."}


# ── API: Memory Stats ─────────────────────────────────────────────────────────
@app.get("/api/memory/stats")
def memory_stats():
    from memory.chroma_store import get_memory
    return get_memory().get_memory_stats()


@app.delete("/api/memory/clear")
def clear_memory():
    from memory.chroma_store import get_memory
    mem = get_memory()
    try:
        import chromadb
        mem._client.delete_collection("hypothesis_memory")
        mem._initialized = False
        mem._collection = None
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Production: Serve React Frontend ─────────────────────────────────────────
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend not built. Run: cd frontend && npm run build")


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5050"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
