import subprocess
import pandas as pd
import os

ratios = [5, 10, 20, 30, 40, 50]

results = []

for r in ratios:
    print(f"\nRunning pipeline with {r}% bot traffic")

    subprocess.run(["python", "coder1.py", str(r)])
    subprocess.run(["python", "coder2.py"])
    subprocess.run(["python", "coder3.py"])

    if not os.path.exists("api_behavior_features.csv"):
        print("Missing features file, skipping")
        continue

    df = pd.read_csv("api_behavior_features.csv")

    # ----- metrics -----

    total = len(df)

    detected = (df["decision"] == "BLOCK").sum()
    monitored = (df["decision"] == "MONITOR").sum()

    detection_rate = (detected + monitored) / total

    false_positive_rate = (
        df[(df["decision"] != "ALLOW") & (df["is_bot"] == 0)].shape[0]
        / df[df["is_bot"] == 0].shape[0]
        if "is_bot" in df.columns else 0
    )

    results.append({
        "ratio": r,
        "detection": round(detection_rate, 3),
        "false_positive": round(false_positive_rate, 3)
    })

# ----- save experiment results -----

exp_df = pd.DataFrame(results)
exp_df.to_csv("ratio_results.csv", index=False)

print("\nExperiment complete → ratio_results.csv created")