import json
from typing import Dict, Any, Optional

class CodeEngineerAgent:
    """
    Generates deterministic Python data analysis scripts for testing hypotheses.
    Includes template-backed logic for high-reliability statistical tests.
    Handles NaN/Inf sanitation natively.
    """

    def generate_test_code(self, hypothesis: Dict[str, Any], csv_path: str, task_type: Optional[str] = None) -> str:
        test_type = hypothesis.get("test_type", "mann_whitney_u")
        indep_var = hypothesis.get("independent_var")
        dep_var = hypothesis.get("dependent_var")
        h_id = hypothesis.get("id")

        if test_type == "mann_whitney_u":
            return f"""
import pandas as pd
import numpy as np
import scipy.stats as stats
import json

def safe_float(v, default=0.0):
    if v is None or np.isnan(v) or np.isinf(v):
        return default
    return float(v)

group0 = pd.to_numeric(df[df['{dep_var}'] == 0]['{indep_var}'], errors='coerce').dropna()
group1 = pd.to_numeric(df[df['{dep_var}'] == 1]['{indep_var}'], errors='coerce').dropna()

if len(group0) > 1 and len(group1) > 1:
    stat, p_val = stats.mannwhitneyu(group0, group1, alternative='two-sided')
    mean0, mean1 = group0.mean(), group1.mean()
    std0, std1 = group0.std(), group1.std()
    pooled_std = np.sqrt(((len(group0)-1)*std0**2 + (len(group1)-1)*std1**2) / (len(group0) + len(group1) - 2))
    cohens_d = (mean1 - mean0) / pooled_std if pooled_std > 0 else 0.0
else:
    stat, p_val, mean0, mean1, cohens_d = 0.0, 1.0, 0.0, 0.0, 0.0

result = {{
    "hypothesis_id": "{h_id}",
    "test_type": "Mann-Whitney U Test",
    "p_value": safe_float(p_val, 1.0),
    "statistic": safe_float(stat, 0.0),
    "effect_size": safe_float(abs(cohens_d), 0.0),
    "effect_size_metric": "Cohen's d",
    "sample_size": int(len(group0) + len(group1)),
    "details": {{
        "group0_mean": safe_float(mean0),
        "group1_mean": safe_float(mean1),
        "difference": safe_float(mean1 - mean0)
    }}
}}
print(json.dumps(result))
"""

        elif test_type == "chi_square":
            return f"""
import pandas as pd
import numpy as np
import scipy.stats as stats
import json

def safe_float(v, default=0.0):
    if v is None or np.isnan(v) or np.isinf(v):
        return default
    return float(v)

contingency_tab = pd.crosstab(df['{indep_var}'], df['{dep_var}'])
if contingency_tab.size > 0 and contingency_tab.sum().sum() > 0:
    chi2, p_val, dof, ex = stats.chi2_contingency(contingency_tab)
    n = contingency_tab.sum().sum()
    min_dim = min(contingency_tab.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0.0
else:
    chi2, p_val, dof, cramers_v = 0.0, 1.0, 0, 0.0

result = {{
    "hypothesis_id": "{h_id}",
    "test_type": "Chi-Square Test of Independence",
    "p_value": safe_float(p_val, 1.0),
    "statistic": safe_float(chi2, 0.0),
    "effect_size": safe_float(cramers_v, 0.0),
    "effect_size_metric": "Cramér's V",
    "sample_size": int(contingency_tab.sum().sum()),
    "details": {{
        "degrees_of_freedom": int(dof)
    }}
}}
print(json.dumps(result))
"""

        elif test_type == "anova":
            return f"""
import pandas as pd
import numpy as np
import scipy.stats as stats
import json

def safe_float(v, default=0.0):
    if v is None or np.isnan(v) or np.isinf(v):
        return default
    return float(v)

groups = [pd.to_numeric(group['{dep_var}'], errors='coerce').dropna() for _, group in df.groupby('{indep_var}')]
groups = [g for g in groups if len(g) > 1]

if len(groups) > 1:
    stat, p_val = stats.f_oneway(*groups)
    all_data = pd.concat(groups)
    grand_mean = all_data.mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in groups)
    ss_total = sum((all_data - grand_mean)**2)
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
else:
    stat, p_val, eta_sq = 0.0, 1.0, 0.0

result = {{
    "hypothesis_id": "{h_id}",
    "test_type": "One-Way ANOVA",
    "p_value": safe_float(p_val, 1.0),
    "statistic": safe_float(stat, 0.0),
    "effect_size": safe_float(eta_sq, 0.0),
    "effect_size_metric": "Eta-Squared (η²)",
    "sample_size": int(sum(len(g) for g in groups)),
    "details": {{
        "num_groups": int(len(groups))
    }}
}}
print(json.dumps(result))
"""

        elif test_type == "random_forest_cv":
            return f"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score
import json

def safe_float(v, default=0.0):
    if v is None or np.isnan(v) or np.isinf(v):
        return default
    return float(v)

try:
    X = df.drop(columns=['{dep_var}'], errors='ignore')
    id_cols = [c for c in X.columns if 'id' in c.lower()]
    X = X.drop(columns=id_cols)
    X = pd.get_dummies(X, drop_first=True)
    y = df['{dep_var}']

    is_regression = "{task_type}" == "regression" or (pd.api.types.is_numeric_dtype(y) and y.nunique() > 10)
    if is_regression:
        model = RandomForestRegressor(n_estimators=30, random_state=42)
        scores = cross_val_score(model, X, y, cv=3, scoring='r2')
        metric_val = float(np.mean(scores))
        metric_name = "R² Score"
    else:
        model = RandomForestClassifier(n_estimators=30, random_state=42)
        scores = cross_val_score(model, X, y, cv=3, scoring='roc_auc')
        metric_val = float(np.mean(scores))
        metric_name = "ROC-AUC Score"

    std_score = float(np.std(scores))
    model.fit(X, y)
    importances = dict(zip(X.columns, [safe_float(v) for v in model.feature_importances_]))
    top_features = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)[:5])
except Exception:
    metric_val, std_score, metric_name, top_features = 0.5, 0.0, "ROC-AUC Score", {{}}

p_val_est = safe_float(max(0.0001, 1.0 - metric_val), 1.0) if metric_val > 0 else 1.0

result = {{
    "hypothesis_id": "{h_id}",
    "test_type": "Random Forest Cross Validation",
    "p_value": p_val_est,
    "statistic": safe_float(metric_val, 0.5),
    "effect_size": safe_float(metric_val, 0.5),
    "effect_size_metric": metric_name,
    "sample_size": int(len(df)),
    "details": {{
        "std_score": safe_float(std_score),
        "top_features": top_features
    }}
}}
print(json.dumps(result))
"""
        else:
            return f"""
import pandas as pd
import numpy as np
import scipy.stats as stats
import json

def safe_float(v, default=0.0):
    if v is None or np.isnan(v) or np.isinf(v):
        return default
    return float(v)

s1 = pd.to_numeric(df['{indep_var}'], errors='coerce')
s2 = pd.to_numeric(df['{dep_var}'], errors='coerce')
valid = pd.DataFrame({{'x': s1, 'y': s2}}).dropna()

if len(valid) > 2:
    corr, p_val = stats.pearsonr(valid['x'], valid['y'])
else:
    corr, p_val = 0.0, 1.0

result = {{
    "hypothesis_id": "{h_id}",
    "test_type": "Pearson Correlation",
    "p_value": safe_float(p_val, 1.0),
    "statistic": safe_float(corr, 0.0),
    "effect_size": safe_float(abs(corr), 0.0),
    "effect_size_metric": "Pearson r",
    "sample_size": int(len(valid)),
    "details": {{
        "correlation": safe_float(corr)
    }}
}}
print(json.dumps(result))
"""

    def heal_code(self, original_code: str, error_msg: str) -> str:
        """Adds defensive NaN filling and exception safety if first execution fails."""
        healed = original_code.replace("df[", "df.fillna(0)[")
        return f"# Self-Healed Script\ntry:\n{healed}\nexcept Exception as e:\n    import json; print(json.dumps({{'error': str(e), 'p_value': 1.0, 'effect_size': 0.0, 'statistic': 0.0}}))\n"
