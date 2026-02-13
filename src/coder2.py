import pandas as pd

LOG_FILE = "api_logs_simulated.csv"
OUT_FILE = "api_behavior_features.csv"

# -----------------------------
# LOAD LOGS
# -----------------------------
df = pd.read_csv(LOG_FILE)
df["timestamp"] = pd.to_datetime(df["timestamp"])

print("Logs loaded:", len(df))
print("Columns:", list(df.columns))

# -----------------------------
# BUILD BEHAVIOR FEATURES
# -----------------------------
g = df.groupby("api_key")

features = g.agg(
    total_requests=("api_key", "count"),
    failed_requests=("status", lambda x: (x == "FAIL").sum()),
    unique_ip_count=("ip", "nunique"),
    endpoint_variety=("endpoint", "nunique"),
    first_seen=("timestamp", "min"),
    last_seen=("timestamp", "max")
)

# active duration window
features["active_seconds"] = (
    features["last_seen"] - features["first_seen"]
).dt.total_seconds().clip(lower=1)

# rates
features["requests_per_min"] = (
    features["total_requests"] / (features["active_seconds"] / 60)
)

features["fail_ratio"] = (
    features["failed_requests"] / features["total_requests"]
)

features["hour_of_access"] = features["first_seen"].dt.hour

features.reset_index(inplace=True)

print("Feature table created:", len(features))

# -----------------------------
# RISK + EXPLAINABILITY
# -----------------------------
def compute_risk_and_reasons(row):
    score = 0
    reasons = []

    # ---- traffic intensity ----
    if row.requests_per_min > 120:
        score += 4
        reasons.append("Extreme RPM")
    elif row.requests_per_min > 80:
        score += 3
        reasons.append("High RPM")
    elif row.requests_per_min > 50:
        score += 1
        reasons.append("Elevated RPM")

    # ---- failure behavior ----
    if row.fail_ratio > 0.5:
        score += 4
        reasons.append("Mass failures")
    elif row.fail_ratio > 0.3:
        score += 3
        reasons.append("High fail ratio")
    elif row.fail_ratio > 0.15:
        score += 1
        reasons.append("Some failures")

    # ---- IP spread ----
    if row.unique_ip_count > 10:
        score += 3
        reasons.append("Wide IP spread")
    elif row.unique_ip_count > 6:
        score += 2
        reasons.append("Many IPs")

    # ---- endpoint probing ----
    if row.endpoint_variety > 10:
        score += 3
        reasons.append("Endpoint scanning")
    elif row.endpoint_variety > 6:
        score += 2
        reasons.append("High endpoint variety")

    # ---- odd hour usage ----
    if row.hour_of_access < 5 or row.hour_of_access > 23:
        score += 1
        reasons.append("Odd hour access")

    if not reasons:
        reasons.append("Normal pattern")

    return score, ", ".join(reasons)


risk_out = features.apply(compute_risk_and_reasons, axis=1)
features["risk_score"] = risk_out.apply(lambda x: x[0])
features["reasons"] = risk_out.apply(lambda x: x[1])

# -----------------------------
# DECISION ENGINE (BALANCED)
# -----------------------------
def decide(score):  
    if score >=6:
        return "BLOCK"
    elif score >=5:
        return "THROTTLE"
    elif score >= 2:
        return "MONITOR"
    else:
        return "ALLOW"


features["decision"] = features["risk_score"].apply(decide)

# -----------------------------
# TRUE LABEL (for demo accuracy)
# -----------------------------
if "traffic_type" in df.columns:
    label_map = (
        df.groupby("api_key")["traffic_type"]
          .agg(lambda x: x.mode()[0])
    )
    features["true_type"] = features["api_key"].map(label_map)
else:
    features["true_type"] = "UNKNOWN"

# -----------------------------
# DEMO METRICS
# -----------------------------
if "traffic_type" in df.columns:
    detected_bot = features["decision"].isin(["THROTTLE", "BLOCK"])
    actual_bot = features["true_type"] == "BOT"
    accuracy = (detected_bot == actual_bot).mean()
    print("\nDemo Detection Accuracy:", round(accuracy * 100, 2), "%")

# -----------------------------
# DEBUG INSIGHT (VERY USEFUL)
# -----------------------------
print("\nRisk score distribution:")
print(features["risk_score"].describe())

print("\nDecision Counts:")
print(features["decision"].value_counts())

# -----------------------------
# SAVE FOR DASHBOARD
# -----------------------------
features.to_csv(OUT_FILE, index=False)

print("\nSaved →", OUT_FILE)
print("coder2 pipeline complete.")
print(features[["risk_score","decision","reasons"]].head(10))