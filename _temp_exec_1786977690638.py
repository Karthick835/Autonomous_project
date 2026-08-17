import pandas as pd
import numpy as np
import scipy.stats as stats
import json
df = pd.read_csv('C:/Users/admin/Desktop/llm and ml project/data/sample_churn.csv')

import pandas as pd
import numpy as np
import scipy.stats as stats
import json

def safe_float(v, default=0.0):
    if v is None or np.isnan(v) or np.isinf(v):
        return default
    return float(v)

group0 = pd.to_numeric(df[df['churned'] == 0]['monthly_charges'], errors='coerce').dropna()
group1 = pd.to_numeric(df[df['churned'] == 1]['monthly_charges'], errors='coerce').dropna()

if len(group0) > 1 and len(group1) > 1:
    stat, p_val = stats.mannwhitneyu(group0, group1, alternative='two-sided')
    mean0, mean1 = group0.mean(), group1.mean()
    std0, std1 = group0.std(), group1.std()
    pooled_std = np.sqrt(((len(group0)-1)*std0**2 + (len(group1)-1)*std1**2) / (len(group0) + len(group1) - 2))
    cohens_d = (mean1 - mean0) / pooled_std if pooled_std > 0 else 0.0
else:
    stat, p_val, mean0, mean1, cohens_d = 0.0, 1.0, 0.0, 0.0, 0.0

result = {
    "hypothesis_id": "H003",
    "test_type": "Mann-Whitney U Test",
    "p_value": safe_float(p_val, 1.0),
    "statistic": safe_float(stat, 0.0),
    "effect_size": safe_float(abs(cohens_d), 0.0),
    "effect_size_metric": "Cohen's d",
    "sample_size": int(len(group0) + len(group1)),
    "details": {
        "group0_mean": safe_float(mean0),
        "group1_mean": safe_float(mean1),
        "difference": safe_float(mean1 - mean0)
    }
}
print(json.dumps(result))
