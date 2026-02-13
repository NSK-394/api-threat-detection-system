import pandas as pd

def build_features(log_file="api_logs_simulated.csv"):

    df = pd.read_csv(log_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    g = df.groupby("api_key")

    features = g.agg(
        total_requests=("api_key", "count"),
        failed_requests=("status", lambda x: (x == "FAIL").sum()),
        unique_ip_count=("ip", "nunique"),
        endpoint_variety=("endpoint", "nunique"),
        first_seen=("timestamp", "min"),
        last_seen=("timestamp", "max")
    )

    features["active_seconds"] = (
        features["last_seen"] - features["first_seen"]
    ).dt.total_seconds().clip(lower=1)

    features["requests_per_min"] = (
        features["total_requests"] /
        (features["active_seconds"] / 60)
    )

    features["fail_ratio"] = (
        features["failed_requests"] /
        features["total_requests"]
    )

    features["hour_of_access"] = features["first_seen"].dt.hour

    features.reset_index(inplace=True)

    label_map = (
        df.groupby("api_key")["traffic_type"]
        .agg(lambda x: x.mode()[0])
    )

    features["true_type"] = features["api_key"].map(label_map)

    return features