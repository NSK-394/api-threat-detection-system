from flask import Flask, jsonify, request
import pandas as pd
import subprocess
import os

app = Flask(__name__)

FEATURE_FILE = "api_behavior_features.csv"

def load_features():
    if os.path.exists("api_behavior_with_anomaly.csv"):
        return pd.read_csv("api_behavior_with_anomaly.csv")

    if os.path.exists("api_behavior_features.csv"):
        return pd.read_csv("api_behavior_features.csv")

    return None

@app.route("/run")
def run_pipeline():
    from flask import request
    import subprocess

    ratio = request.args.get("ratio", "30")
    print("\n=== PIPELINE START ===")
    print("Bot ratio:", ratio)

    print("Running coder1...")
    subprocess.run(["python", "coder1.py", ratio])

    print("Running coder2...")
    subprocess.run(["python", "coder2.py"])

    print("Running coder3...")
    subprocess.run(["python", "coder3.py"])

    print("=== PIPELINE END ===\n")

    return {"status": "ok"}


@app.route("/metrics")
def metrics():
    df = load_features()
    if df is None:
        return jsonify({})
    anomaly_percent = (df["decision"].isin(["BLOCK", "THROTTLE"]).mean()) * 100


    return jsonify({
    "total": len(df),
    "blocked": int((df["decision"] == "BLOCK").sum()),
    "monitor": int((df["decision"] == "MONITOR").sum()),
    "allowed": int((df["decision"] == "ALLOW").sum()),
    "throttle": int((df["decision"] == "THROTTLE").sum()),
    "anomaly_percent": anomaly_percent
    })
    



@app.route("/decisions")
def decisions():
    df = load_features()
    if df is None:
        return jsonify({})
    return df["decision"].value_counts().to_dict()


@app.route("/risk")
def risk_scores():
    df = load_features()
    if df is None or "anomaly_score" not in df.columns:
        return jsonify([])

    s = df["anomaly_score"]

    # normalize to -1 .. +1 for chart readability
    s_norm = (s - s.mean()) / (s.std() + 1e-6)

    return jsonify(s_norm.tolist())
@app.route("/table")
def table():
    df = load_features()
    if df is None:
        return jsonify([])
    return df.head(200).to_dict(orient="records")

@app.route("/traffic_split")
def traffic_split():
    import pandas as pd
    import os

    if not os.path.exists("api_behavior_with_anomaly.csv"):
        return {"normal": 0, "bot": 0}

    df = pd.read_csv("api_behavior_with_anomaly.csv")

    normal = int((df["true_type"] == "NORMAL").sum())
    bot = int((df["true_type"] == "BOT").sum())

    return {"normal": normal, "bot": bot}
@app.route("/alerts")
def alerts():
    df = load_features()
    if df is None:
        return []

    alerts = df[df["decision"].isin(["BLOCK","THROTTLE"])]
    alerts = alerts.sort_values("risk_score", ascending=False).head(10)

    return alerts[["api_key","decision","risk_score"]].to_dict("records")


from flask import render_template

@app.route("/")
def home():
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)

