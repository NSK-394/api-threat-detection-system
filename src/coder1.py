import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import sys
bot_ratio = int(sys.argv[1]) if len(sys.argv) > 1 else 30
print("BOT RATIO =", bot_ratio)

ENDPOINTS_NORMAL = [
    "/login",
    "/getProfile",
    "/getData",
    "/updateProfile",
    "/downloadReport"
]

ENDPOINTS_BOT_EXTRA = [
    "/admin",
    "/internal",
    "/config",
    "/debug"
]

NORMAL_IP_POOL = [f"192.168.1.{i}" for i in range(1, 25)]
BOT_IP_POOL = [f"10.0.0.{i}" for i in range(1, 255)]

START_TIME = datetime.now()


def random_spread_time(base, seconds):
    return base + timedelta(seconds=random.randint(0, seconds))

def burst_time_cluster(base, spread_seconds=20):
    return base + timedelta(seconds=random.randint(0, spread_seconds))


def generate_normal_log(api_key):
    return {
        "timestamp": random_spread_time(START_TIME, 7200),
        "api_key": api_key,
        "ip": random.choice(NORMAL_IP_POOL),
        "endpoint": random.choice(ENDPOINTS_NORMAL),
        "status": random.choices(
            ["SUCCESS", "FAIL"],
            weights=[0.9, 0.1]
        )[0],
        "response_time_ms": random.randint(80, 450),
        "traffic_type": "NORMAL"
    }

def generate_bot_log(api_key, burst_base, bot_ip_subset):
    endpoint = random.choice(ENDPOINTS_NORMAL + ENDPOINTS_BOT_EXTRA)

    return {
        "timestamp": burst_time_cluster(burst_base, 25),
        "api_key": api_key,
        "ip": random.choice(bot_ip_subset),
        "endpoint": endpoint,
        "status": random.choices(
            ["SUCCESS", "FAIL"],
            weights=[0.8, 0.2]
        )[0],
        "response_time_ms": random.randint(40, 160),
        "traffic_type": "BOT"
    }


def generate_logs(
    total_users=80,
    bot_percent=30,
    normal_logs_per_user=350,
    bot_logs_per_user=450,
):
    logs = []

    bot_users = int(total_users * bot_percent / 100)
    normal_users = total_users - bot_users

    print(f"Normal users: {normal_users}")
    print(f"Bot users: {bot_users}")
    for _ in range(normal_users):
        api_key = str(uuid.uuid4())

        for _ in range(normal_logs_per_user):
            logs.append(generate_normal_log(api_key))
            
    for _ in range(bot_users):
        api_key = str(uuid.uuid4())
        bot_ip_subset = random.sample(BOT_IP_POOL, 12)

        burst_windows = [
            START_TIME + timedelta(minutes=random.randint(0, 60))
            for _ in range(4)
        ]

        for _ in range(bot_logs_per_user):
            base = random.choice(burst_windows)
            logs.append(generate_bot_log(api_key, base, bot_ip_subset))

    df = pd.DataFrame(logs)

    df = df.sample(frac=1).reset_index(drop=True)
    df = df.sort_values("timestamp")

    return df

if __name__ == "__main__":

    bot_percent = 30

    if len(sys.argv) > 1:
        bot_percent = int(sys.argv[1])

    df = generate_logs(bot_percent=bot_percent)
    

    OUTPUT_FILE = "api_logs_simulated.csv"
    df.to_csv(OUTPUT_FILE, index=False)

    print("✅ Log simulation completed")
    print("Rows:", len(df))
    print(df.head())
