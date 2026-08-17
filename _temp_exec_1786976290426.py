import pandas as pd
import numpy as np
import scipy.stats as stats
import json
df = pd.read_csv('C:/Users/admin/Desktop/llm and ml project/data/sample_churn.csv')

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score
import json

# Preprocess features
y = df['total_charges']
X = df.drop(columns=['total_charges'], errors='ignore')

# Drop ID columns & handle missing values
id_cols = [c for c in X.columns if ('id' in c.lower() or 'uuid' in c.lower() or 'code' in c.lower())]
X = X.drop(columns=id_cols)
X = pd.get_dummies(X, drop_first=True)
X = X.fillna(X.median(numeric_only=True)).fillna(0)

# Check classification vs regression
is_classification = y.nunique() <= 10 or not pd.api.types.is_numeric_dtype(y)

if is_classification:
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    scores = cross_val_score(clf, X, y, cv=min(5, max(2, len(df)//5)), scoring='accuracy')
    metric_name = "CV Accuracy"
    mean_score = float(np.mean(scores))
    clf.fit(X, y)
    importances = dict(zip(X.columns, [float(round(v, 4)) for v in clf.feature_importances_]))
else:
    y = y.fillna(y.median())
    reg = RandomForestRegressor(n_estimators=50, random_state=42)
    scores = cross_val_score(reg, X, y, cv=min(5, max(2, len(df)//5)), scoring='r2')
    metric_name = "R² Score"
    mean_score = float(np.mean(scores))
    reg.fit(X, y)
    importances = dict(zip(X.columns, [float(round(v, 4)) for v in reg.feature_importances_]))

top_features = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)[:5])

result = {
    "hypothesis_id": "H006",
    "test_type": "Random Forest Cross Validation",
    "p_value": float(round(max(0.0001, 1.0 - max(0, mean_score)), 6)),
    "statistic": float(round(mean_score, 4)),
    "effect_size": float(round(max(0, mean_score), 4)),
    "effect_size_metric": metric_name,
    "sample_size": int(len(df)),
    "details": {
        "cv_scores": [float(round(s, 4)) for s in scores],
        "top_features": top_features
    }
}
print(json.dumps(result))
