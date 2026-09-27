import pandas as pd
import time
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "hour.csv"

df = pd.read_csv(DATA_PATH)

print("Shape:", df.shape)
print("Missing values:", df.isna().sum().sum())
print("Memory usage (MB):", df.memory_usage(deep=True).sum() / 1024**2)

df = df.sort_values(["dteday", "hr"])

X = df.drop(columns=[
    "instant",
    "dteday",
    "casual",
    "registered",
    "cnt"
])

y = df["cnt"]

split = int(len(df) * 0.8)

model = RandomForestRegressor(
    n_estimators=50,
    random_state=42,
    n_jobs=-1
)

start = time.perf_counter()

model.fit(X.iloc[:split], y.iloc[:split])

print("Training time:", time.perf_counter() - start)