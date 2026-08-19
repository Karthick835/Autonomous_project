"""
HypothesizerAgent — generates testable scientific hypotheses.
- Uses the active LLMProvider (Gemini / GPT-4o / Claude)
- Queries ChromaDB memory to avoid repeating already-tested hypotheses
- Falls back to advanced statistical heuristic engine if LLM is not configured
"""

import json
import os
from typing import Dict, Any, List, Optional

from llm.provider import LLMProvider, LLMConfigurationError
from memory.chroma_store import get_memory


SYSTEM_PROMPT = """You are an expert lead scientist and statistician specializing in 
autonomous data analysis. You generate rigorous, testable scientific hypotheses 
from dataset profiles. Always respond with valid JSON only."""


class HypothesizerAgent:
    """
    Generates data-driven, domain-aware testable scientific hypotheses.
    Uses the LLMProvider for intelligent generation, with memory-based deduplication
    and a heuristic fallback engine.
    """

    def generate_hypotheses(
        self,
        profile: Dict[str, Any],
        domain_context: str = "",
        llm_provider: Optional[LLMProvider] = None,
        dataset_name: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Generate hypotheses. If llm_provider is set, uses real LLM.
        Queries ChromaDB memory to filter already-tested hypotheses.
        """
        # Get previously tested hypotheses from memory
        memory = get_memory()
        already_tested = []
        if dataset_name:
            already_tested = memory.get_tested_hypotheses(dataset_name)

        already_tested_titles = {
            r.get("title", "").lower().strip()
            for r in already_tested
        }

        # Try LLM generation
        if llm_provider is not None:
            try:
                candidates = self._generate_with_llm(profile, domain_context, llm_provider)
                filtered = self._filter_already_tested(candidates, already_tested_titles)
                if filtered:
                    return filtered
                print("[HypothesizerAgent] All LLM hypotheses already tested. Generating novel heuristics.")
            except LLMConfigurationError:
                raise  # Re-raise — user must fix their API key
            except Exception as e:
                print(f"[HypothesizerAgent] LLM generation failed ({e}). Using heuristic engine.")

        # Heuristic fallback
        candidates = self._generate_heuristics(profile, domain_context)
        return self._filter_already_tested(candidates, already_tested_titles)

    def _filter_already_tested(
        self,
        hypotheses: List[Dict],
        already_tested_titles: set,
    ) -> List[Dict]:
        """Remove hypotheses already in memory."""
        if not already_tested_titles:
            return hypotheses
        return [
            h for h in hypotheses
            if h.get("title", "").lower().strip() not in already_tested_titles
        ]

    def _generate_with_llm(
        self,
        profile: Dict[str, Any],
        domain_context: str,
        llm_provider: LLMProvider,
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses using the active LLM."""

        prompt = f"""You are an expert AI Lead Scientist analyzing a dataset.

Dataset Profile:
- Active Target Column: {profile.get('active_target')}
- Task Type: {profile.get('active_task')}
- Numerical Columns: {profile.get('numerical_columns')}
- Categorical Columns: {profile.get('categorical_columns')}
- Total Rows: {profile.get('num_rows')}
- Domain Context: {domain_context or 'General scientific exploration'}

High-Correlation Features Detected: {profile.get('high_correlations', [])[:5]}

Generate 5-7 diverse, testable scientific hypotheses. Make them specific to this dataset.
For each hypothesis, provide:
- id: string ("H001", "H002", etc.)
- title: string (concise, descriptive)
- statement: string (precise testable claim)
- category: one of ["Group Comparison", "Correlation", "Categorical Independence", "Predictive ML", "Negative Control"]
- independent_var: exact column name from the dataset (or "all_features" for ML)
- dependent_var: the target column name
- test_type: one of ["mann_whitney_u", "pearson_correlation", "chi_square", "anova", "random_forest_cv"]
- min_effect_size: float (0.30 for Cohen's d/r, 0.20 for Cramér's V, 0.70 for AUC, 0.30 for R²)
- rationale: string explaining the scientific reasoning

Rules:
- Use independent_var and dependent_var that actually exist as column names in the dataset
- For mann_whitney_u: target must be binary (0/1 or similar)
- Include exactly 1 Negative Control hypothesis (expected non-significant)
- Include 1 random_forest_cv ("all_features" as independent_var)
- Include at least 2 specific single-variable tests

Return ONLY a valid JSON array. No markdown, no code fences, no explanation."""

        return llm_provider.generate_json(prompt, system_prompt=SYSTEM_PROMPT)

    def _generate_heuristics(
        self, profile: Dict[str, Any], domain_context: str
    ) -> List[Dict[str, Any]]:
        """Advanced statistical heuristic hypothesis engine."""
        hypotheses = []
        target = profile.get("active_target")
        task_type = profile.get("active_task", "classification")
        num_cols = profile.get("numerical_columns", [])
        cat_cols = profile.get("categorical_columns", [])
        column_profiles = profile.get("column_profiles", {})

        # Filter out ID columns and the target itself
        valid_num_cols = [
            c for c in num_cols
            if c != target and not column_profiles.get(c, {}).get("is_id_column", False)
        ]
        valid_cat_cols = [
            c for c in cat_cols
            if c != target and not column_profiles.get(c, {}).get("is_id_column", False)
        ]

        h_count = 1

        if not target:
            if len(valid_num_cols) >= 2:
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Bivariate Correlation: {valid_num_cols[0]} & {valid_num_cols[1]}",
                    "statement": f"Significant linear correlation exists between '{valid_num_cols[0]}' and '{valid_num_cols[1]}'.",
                    "category": "Correlation",
                    "independent_var": valid_num_cols[0],
                    "dependent_var": valid_num_cols[1],
                    "test_type": "pearson_correlation",
                    "min_effect_size": 0.30,
                    "rationale": "Exploratory bivariate correlation across numeric features.",
                })
            return hypotheses

        # Strategy 1: Top numerical features vs target
        for n_col in valid_num_cols[:3]:
            if task_type == "classification":
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"{n_col.replace('_', ' ').title()} vs {target.replace('_', ' ').title()} Distribution Shift",
                    "statement": f"Higher values of '{n_col}' significantly differentiate target outcome '{target}'.",
                    "category": "Group Comparison",
                    "independent_var": n_col,
                    "dependent_var": target,
                    "test_type": "mann_whitney_u",
                    "min_effect_size": 0.30,
                    "rationale": f"Continuous feature '{n_col}' evaluated for group variance against binary target '{target}'.",
                })
            else:
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Linear Relationship: {n_col.replace('_', ' ').title()} → {target.replace('_', ' ').title()}",
                    "statement": f"Continuous feature '{n_col}' exhibits significant Pearson correlation with '{target}'.",
                    "category": "Correlation",
                    "independent_var": n_col,
                    "dependent_var": target,
                    "test_type": "pearson_correlation",
                    "min_effect_size": 0.30,
                    "rationale": f"Linear association between '{n_col}' and continuous target '{target}'.",
                })
            h_count += 1

        # Strategy 2: Categorical features vs target
        for c_col in valid_cat_cols[:2]:
            if task_type == "classification":
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Independence: {c_col.replace('_', ' ').title()} on {target.replace('_', ' ').title()}",
                    "statement": f"Categorical distribution of '{c_col}' is significantly associated with '{target}'.",
                    "category": "Categorical Independence",
                    "independent_var": c_col,
                    "dependent_var": target,
                    "test_type": "chi_square",
                    "min_effect_size": 0.20,
                    "rationale": f"Chi-square test for categorical independence between '{c_col}' and '{target}'.",
                })
            else:
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Group Variance (ANOVA): {c_col.replace('_', ' ').title()} vs {target.replace('_', ' ').title()}",
                    "statement": f"Mean of '{target}' varies significantly across distinct categories in '{c_col}'.",
                    "category": "Group Comparison",
                    "independent_var": c_col,
                    "dependent_var": target,
                    "test_type": "anova",
                    "min_effect_size": 0.25,
                    "rationale": f"One-way ANOVA across category levels in '{c_col}' for target '{target}'.",
                })
            h_count += 1

        # Strategy 3: Multi-feature ensemble model
        if len(valid_num_cols) + len(valid_cat_cols) >= 2:
            min_eff = 0.70 if task_type == "classification" else 0.30
            metric = "ROC-AUC > 0.70" if task_type == "classification" else "R² > 0.30"
            hypotheses.append({
                "id": f"H{h_count:03d}",
                "title": f"Multi-Feature Random Forest Model for {target.replace('_', ' ').title()}",
                "statement": f"Combined Random Forest ensemble non-trivially predicts '{target}' ({metric}).",
                "category": "Predictive ML",
                "independent_var": "all_features",
                "dependent_var": target,
                "test_type": "random_forest_cv",
                "min_effect_size": min_eff,
                "rationale": f"Evaluating multi-variable interactions across all features to predict '{target}'.",
            })
            h_count += 1

        # Strategy 4: Negative control
        noise_col = (
            valid_cat_cols[-1]
            if valid_cat_cols
            else (valid_num_cols[-1] if valid_num_cols else None)
        )
        if noise_col and len(hypotheses) < 6:
            test = (
                "chi_square" if noise_col in valid_cat_cols
                else ("mann_whitney_u" if task_type == "classification" else "pearson_correlation")
            )
            hypotheses.append({
                "id": f"H{h_count:03d}",
                "title": f"Negative Control: {noise_col.replace('_', ' ').title()}",
                "statement": f"Feature '{noise_col}' has no statistically significant relationship with '{target}'.",
                "category": "Negative Control",
                "independent_var": noise_col,
                "dependent_var": target,
                "test_type": test,
                "min_effect_size": 0.10,
                "rationale": "Baseline sensitivity check using an expected non-causal feature.",
            })

        return hypotheses
