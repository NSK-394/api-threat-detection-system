import os

print("Step-1: Generating synthetic API logs...")
os.system("python coder1.py")

print("\nStep-2: Processing logs and extracting features and rick score engine...")
os.system("python coder2.py")

print("\nStep-3: Running anomaly detection and visualizations...")
os.system("python coder3.py")

print("\nAll steps completed successfully!")