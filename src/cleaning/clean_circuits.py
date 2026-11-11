from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent

csv_path = PROJECT_DIR / "data" / "raw" / "circuits.csv"
csv_clean = PROJECT_DIR / "data" / "clean" / "circuits_clean.csv"


circuits = pd.read_csv(csv_path)

df = circuits.rename(columns={
    "circuitId": "circuit_id",
    "circuitRef": "circuit_ref",
    "name": "circuit_name",
}).drop(columns=["url"])

n = (df["country"] == "United States").sum()
df["country"] = df["country"].replace("United States", "USA")
print(n, "ligne corrigée (country)")

assert len(df) == len(circuits) == 78
assert df["circuit_id"].is_unique
assert df.isna().sum().sum() == 0

df.to_csv(csv_clean,sep=",", encoding="utf-8" , index=False)
print("circuits_clean.csv écrit :", len(df), "lignes")