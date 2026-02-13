import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.covariance import EllipticEnvelope
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv("api_behavior_features.csv")
df = df.dropna()  

print("Features loaded:", len(df))

model_cols = [
    "requests_per_min",
    "unique_ip_count",
    "endpoint_variety",
    "fail_ratio"
]


missing = [c for c in model_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")
 
X = df[model_cols]

# ---------- scale ----------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# small noise helps with duplicate vectors
X_scaled = X_scaled + np.random.normal(0, 0.01, X_scaled.shape)

# ---------- split ----------
X_train, X_test = train_test_split(
    X_scaled,
    test_size=0.2,
    random_state=42
)

# ---------- contamination estimate ----------
estimated_contamination = 0.1

print("Estimated contamination:", estimated_contamination)

# ---------- build model ----------
model = EllipticEnvelope(
    contamination=estimated_contamination,
    random_state=42
)

# ---------- train ----------
model.fit(X_train)

# ---------- test scoring ----------
test_flags = model.predict(X_test)
test_scores = model.decision_function(X_test)

print("Training on features:", model_cols)


df["anomaly_flag"] = model.predict(X_scaled)
df["anomaly_score"] = model.decision_function(X_scaled)

df["alert"] = df["anomaly_flag"].apply(lambda x: "ALERT" if x == -1 else "OK")

print("Anomaly detection complete")

df.to_csv("api_behavior_with_anomaly.csv", index=False)

joblib.dump(model, "elliptic_model.pkl")
joblib.dump(scaler, "feature_scaler.pkl")


print("\nAnomaly counts:")
print(df["anomaly_flag"].value_counts())

print("Anomaly percentage:",
      (df["anomaly_flag"] == -1).mean()*100)

def score_new_request(new_record_dict):
    row = pd.DataFrame([new_record_dict])[model_cols]
    new_scaled = scaler.transform(row)
    flag = model.predict(new_scaled)[0]
    score = model.decision_function(new_scaled)[0]
    return flag, score