import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class DataProfilerAgent:
    """
    Analyzes raw datasets to extract statistical properties, detect column types,
    determine target candidates (classification vs regression), compute distribution bins
    for UI visualizations, and flag potential data leakage risks.
    """

    def profile_csv(self, csv_path: str, target_override: Optional[str] = None, task_type_override: Optional[str] = None) -> Dict[str, Any]:
        df = pd.read_csv(csv_path)
        num_rows, num_cols = df.shape

        column_profiles = {}
        numerical_cols = []
        categorical_cols = []
        target_candidates = []
        leakage_warnings = []

        for col in df.columns:
            col_data = df[col]
            missing_count = int(col_data.isnull().sum())
            missing_pct = round(missing_count / num_rows * 100, 2)
            num_unique = int(col_data.nunique())
            dtype_str = str(col_data.dtype)

            # Detect ID columns or potential leakage keys
            is_id = False
            col_lower = str(col).lower()
            if ('id' in col_lower or 'uuid' in col_lower or 'number' in col_lower or 'code' in col_lower) and num_unique > 0.8 * num_rows:
                is_id = True
                leakage_warnings.append(f"Column '{col}' appears to be an ID/Primary Key (cardinality: {num_unique}/{num_rows}).")

            # Detect target candidates & problem type (classification vs regression)
            is_numeric = pd.api.types.is_numeric_dtype(col_data)
            suggested_task = "classification" if (not is_numeric or num_unique <= 10) else "regression"

            if col_lower in ['churn', 'churned', 'target', 'label', 'outcome', 'disease', 'response', 'status', 'price', 'salary', 'rating']:
                target_candidates.insert(0, {"name": col, "suggested_task": suggested_task, "num_unique": num_unique})
            elif 2 <= num_unique <= 20 or (is_numeric and not is_id and col != df.columns[0]):
                target_candidates.append({"name": col, "suggested_task": suggested_task, "num_unique": num_unique})

            stats = {
                "name": col,
                "dtype": dtype_str,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": num_unique,
                "is_id_column": is_id,
                "is_numeric": is_numeric
            }

            if is_numeric:
                numerical_cols.append(col)
                clean_col = col_data.dropna()
                if len(clean_col) > 0:
                    min_v, max_v = float(clean_col.min()), float(clean_col.max())
                    mean_v, std_v = float(clean_col.mean()), float(clean_col.std())
                    stats.update({
                        "mean": round(mean_v, 4),
                        "std": round(std_v, 4),
                        "min": round(min_v, 4),
                        "max": round(max_v, 4),
                        "median": round(float(clean_col.median()), 4),
                        "skew": round(float(clean_col.skew()), 4) if len(clean_col) > 2 else 0.0
                    })
                    # Generate 5-bin histogram distribution for UI preview
                    try:
                        counts, bin_edges = np.histogram(clean_col, bins=min(5, max(2, num_unique)))
                        stats["histogram"] = [
                            {"bin": f"{round(bin_edges[k],1)}-{round(bin_edges[k+1],1)}", "count": int(counts[k])}
                            for k in range(len(counts))
                        ]
                    except Exception:
                        stats["histogram"] = []
            else:
                categorical_cols.append(col)
                top_counts = col_data.value_counts().head(5).to_dict()
                stats["top_categories"] = {str(k): int(v) for k, v in top_counts.items()}

            column_profiles[col] = stats

        # Determine active target column
        active_target = target_override if (target_override and target_override in df.columns) else (target_candidates[0]["name"] if target_candidates else None)
        
        # Determine active task type (classification vs regression)
        if task_type_override and task_type_override in ["classification", "regression"]:
            active_task = task_type_override
        elif active_target and active_target in column_profiles:
            active_task = "classification" if (not column_profiles[active_target]["is_numeric"] or column_profiles[active_target]["unique_count"] <= 10) else "regression"
        else:
            active_task = "classification"

        # Correlation analysis among numerical columns
        correlations = []
        if len(numerical_cols) >= 2:
            corr_matrix = df[numerical_cols].corr()
            for i in range(len(numerical_cols)):
                for j in range(i + 1, len(numerical_cols)):
                    c1, c2 = numerical_cols[i], numerical_cols[j]
                    val = corr_matrix.loc[c1, c2]
                    if not np.isnan(val) and abs(val) >= 0.4:
                        correlations.append({
                            "col1": c1,
                            "col2": c2,
                            "correlation": round(float(val), 4)
                        })
                        if abs(val) >= 0.95 and c1 != active_target and c2 != active_target:
                            leakage_warnings.append(f"Near-perfect multicollinearity between '{c1}' and '{c2}' (r = {round(val, 3)}).")

        return {
            "num_rows": num_rows,
            "num_cols": num_cols,
            "numerical_columns": numerical_cols,
            "categorical_columns": categorical_cols,
            "target_candidates": [t["name"] for t in target_candidates],
            "target_candidates_detailed": target_candidates,
            "active_target": active_target,
            "active_task": active_task,
            "column_profiles": column_profiles,
            "high_correlations": correlations,
            "leakage_warnings": leakage_warnings,
            "preview_rows": df.head(10).to_dict(orient="records")
        }

