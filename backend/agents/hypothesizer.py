import json
import os
from typing import Dict, Any, List, Optional

class HypothesizerAgent:
    """
    Generates data-driven, domain-aware testable scientific hypotheses
    based on dataset profiling. Supports Gemini LLM calls when API key is configured,
    with automatic fallback to advanced statistical heuristic generation.
    """

    def generate_hypotheses(self, profile: Dict[str, Any], domain_context: str = "") -> List[Dict[str, Any]]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key and os.getenv("GEMINI_API_KEY"):
            try:
                return self._generate_with_gemini(profile, domain_context, api_key)
            except Exception as e:
                print(f"[HypothesizerAgent] LLM generation failed ({e}). Falling back to statistical heuristic engine.")

        return self._generate_heuristics(profile, domain_context)

    def _generate_with_gemini(self, profile: Dict[str, Any], domain_context: str, api_key: str) -> List[Dict[str, Any]]:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
You are an expert AI Lead Scientist analyzing a dataset.
Dataset Profile:
- Active Target: {profile.get('active_target')}
- Task Type: {profile.get('active_task')}
- Numerical Columns: {profile.get('numerical_columns')}
- Categorical Columns: {profile.get('categorical_columns')}
- Domain Context: {domain_context}

Generate 4-6 testable scientific hypotheses in strict JSON array format.
For each hypothesis include:
- id: string ("H001", "H002", etc.)
- title: string
- statement: string
- category: string ("Group Comparison", "Correlation", "Categorical Independence", "Predictive ML", "Negative Control")
- independent_var: string (column name or "all_features")
- dependent_var: string (target column name)
- test_type: string ("mann_whitney_u", "pearson_correlation", "chi_square", "anova", "random_forest_cv")
- min_effect_size: float (e.g. 0.30 for Cohen's d or r, 0.70 for AUC/R2)
- rationale: string

Return ONLY valid JSON array with no markdown backticks.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(text)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed
        raise ValueError("Invalid LLM response format")

    def _generate_heuristics(self, profile: Dict[str, Any], domain_context: str) -> List[Dict[str, Any]]:
        hypotheses = []
        target = profile.get("active_target")
        task_type = profile.get("active_task", "classification")
        num_cols = profile.get("numerical_columns", [])
        cat_cols = profile.get("categorical_columns", [])
        column_profiles = profile.get("column_profiles", {})

        # Filter out ID columns
        valid_num_cols = [c for c in num_cols if c != target and not column_profiles.get(c, {}).get("is_id_column", False)]
        valid_cat_cols = [c for c in cat_cols if c != target and not column_profiles.get(c, {}).get("is_id_column", False)]

        h_count = 1

        if not target:
            # Exploratory fallback if no target
            if len(valid_num_cols) >= 2:
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Bivariate Correlation: {valid_num_cols[0]} & {valid_num_cols[1]}",
                    "statement": f"Significant continuous linear correlation exists between '{valid_num_cols[0]}' and '{valid_num_cols[1]}'.",
                    "category": "Correlation",
                    "independent_var": valid_num_cols[0],
                    "dependent_var": valid_num_cols[1],
                    "test_type": "pearson_correlation",
                    "min_effect_size": 0.30,
                    "rationale": "Exploratory continuous correlation analysis across numeric features."
                })
            return hypotheses

        # Strategy 1: Numerical feature vs Target
        for n_col in valid_num_cols[:3]:
            if task_type == "classification":
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"{n_col.title()} vs {target.title()} Distribution Shift",
                    "statement": f"Higher values of '{n_col}' significantly differentiate target outcome '{target}'.",
                    "category": "Group Comparison",
                    "independent_var": n_col,
                    "dependent_var": target,
                    "test_type": "mann_whitney_u",
                    "min_effect_size": 0.30,
                    "rationale": f"Continuous feature '{n_col}' evaluated for group variance against target '{target}'."
                })
            else: # regression
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Linear Relationship: {n_col.title()} -> {target.title()}",
                    "statement": f"Continuous feature '{n_col}' exhibits significant correlation with continuous target '{target}'.",
                    "category": "Correlation",
                    "independent_var": n_col,
                    "dependent_var": target,
                    "test_type": "pearson_correlation",
                    "min_effect_size": 0.30,
                    "rationale": f"Linear association evaluation between continuous predictor '{n_col}' and target '{target}'."
                })
            h_count += 1

        # Strategy 2: Categorical feature vs Target
        for c_col in valid_cat_cols[:2]:
            if task_type == "classification":
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Independence Check: {c_col.title()} on {target.title()}",
                    "statement": f"Categorical distribution of '{c_col}' is significantly associated with '{target}'.",
                    "category": "Categorical Independence",
                    "independent_var": c_col,
                    "dependent_var": target,
                    "test_type": "chi_square",
                    "min_effect_size": 0.20,
                    "rationale": f"Discrete categories in '{c_col}' show probability skew towards '{target}'."
                })
            else: # regression ANOVA
                hypotheses.append({
                    "id": f"H{h_count:03d}",
                    "title": f"Group Variance (ANOVA): {c_col.title()} vs {target.title()}",
                    "statement": f"Mean target value of '{target}' varies significantly across distinct categories in '{c_col}'.",
                    "category": "Group Comparison",
                    "independent_var": c_col,
                    "dependent_var": target,
                    "test_type": "anova",
                    "min_effect_size": 0.25,
                    "rationale": f"One-way ANOVA variance analysis across category levels in '{c_col}'."
                })
            h_count += 1

        # Strategy 3: Multi-Feature Ensemble Model
        if len(valid_num_cols) + len(valid_cat_cols) >= 2:
            test_t = "random_forest_cv"
            min_eff = 0.70 if task_type == "classification" else 0.30 # AUC vs R2
            metric_label = "ROC-AUC > 0.70" if task_type == "classification" else "R² Score > 0.30"
            hypotheses.append({
                "id": f"H{h_count:03d}",
                "title": f"Multi-Feature Machine Learning Model for {target.title()}",
                "statement": f"Combined Random Forest ensemble non-trivially predicts '{target}' ({metric_label}).",
                "category": "Predictive ML",
                "independent_var": "all_features",
                "dependent_var": target,
                "test_type": test_t,
                "min_effect_size": min_eff,
                "rationale": f"Evaluating multi-variable interactions across numerical & categorical features to predict '{target}'."
            })
            h_count += 1

        # Strategy 4: Negative Control
        noise_col = valid_cat_cols[-1] if valid_cat_cols else (valid_num_cols[-1] if valid_num_cols else None)
        if noise_col and len(hypotheses) < 5:
            hypotheses.append({
                "id": f"H{h_count:03d}",
                "title": f"Negative Control Check: {noise_col.title()}",
                "statement": f"Feature '{noise_col}' exhibits no statistically significant relationship with '{target}'.",
                "category": "Negative Control",
                "independent_var": noise_col,
                "dependent_var": target,
                "test_type": "chi_square" if noise_col in valid_cat_cols else ("mann_whitney_u" if task_type == "classification" else "pearson_correlation"),
                "min_effect_size": 0.10,
                "rationale": "Validating baseline sensitivity by testing an expected non-causal noise feature."
            })

        return hypotheses

