"""
Natural Language Query Interpreter.
Uses the active LLM to parse a free-text scientific question
and extract: target column, task type, and investigation direction.
"""

import json
from typing import Dict, Any, Optional
from llm.provider import LLMProvider


SYSTEM_PROMPT = """You are an expert data scientist and statistician.
A user will provide a natural language question about a dataset.
Your job is to parse this question and identify the scientific investigation parameters.
Always respond with valid JSON only — no markdown, no explanation."""


def interpret_nl_query(
    query: str,
    profile: Dict[str, Any],
    llm_provider: LLMProvider,
) -> Dict[str, Any]:
    """
    Interpret a natural language scientific question into structured params.
    
    Returns:
        {
          "target_column": str,       # column name from the dataset
          "task_type": str,           # "classification" or "regression"
          "domain_context": str,      # refined investigation focus for hypothesizer
          "confidence": str,          # "high", "medium", "low"
          "explanation": str          # why this interpretation was chosen
        }
    """
    column_names = list(profile.get("column_profiles", {}).keys())
    num_cols = profile.get("numerical_columns", [])
    cat_cols = profile.get("categorical_columns", [])
    target_candidates = profile.get("target_candidates", [])

    prompt = f"""User Question: "{query}"

Dataset Information:
- All Columns: {column_names}
- Numerical Columns: {num_cols}
- Categorical Columns: {cat_cols}
- Suggested Target Candidates: {target_candidates}
- Dataset Rows: {profile.get('num_rows', 'unknown')}

Task: Parse the user's scientific question and return a JSON object with these fields:
- "target_column": the best column from the dataset to use as the dependent variable (must be an exact column name from the list above)
- "task_type": either "classification" or "regression" based on the target column type
- "domain_context": a refined 1-2 sentence scientific investigation description based on the question
- "confidence": "high" if the target is obvious, "medium" if inferred, "low" if ambiguous
- "explanation": 1-2 sentences explaining your interpretation

Return ONLY valid JSON. No markdown, no backticks."""

    try:
        result = llm_provider.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
        
        # Validate target_column is actually in the dataset
        if result.get("target_column") not in column_names:
            # Try to find closest match
            query_lower = query.lower()
            for col in column_names:
                if col.lower() in query_lower:
                    result["target_column"] = col
                    break
            else:
                # Fall back to first target candidate
                result["target_column"] = target_candidates[0] if target_candidates else column_names[-1]
                result["confidence"] = "low"

        # Ensure task_type is valid
        if result.get("task_type") not in ["classification", "regression"]:
            target = result.get("target_column", "")
            col_profile = profile.get("column_profiles", {}).get(target, {})
            result["task_type"] = (
                "regression"
                if col_profile.get("is_numeric") and col_profile.get("unique_count", 0) > 10
                else "classification"
            )

        return result

    except Exception as e:
        # Graceful degradation: return best guess without LLM
        best_target = target_candidates[0] if target_candidates else (column_names[-1] if column_names else "")
        col_profile = profile.get("column_profiles", {}).get(best_target, {})
        task = (
            "regression"
            if col_profile.get("is_numeric") and col_profile.get("unique_count", 0) > 10
            else "classification"
        )
        return {
            "target_column": best_target,
            "task_type": task,
            "domain_context": query,
            "confidence": "low",
            "explanation": f"LLM interpretation failed ({e}). Using heuristic fallback.",
        }
