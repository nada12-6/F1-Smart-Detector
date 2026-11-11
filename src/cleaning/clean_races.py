from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent

csv_path = PROJECT_DIR / "data" / "raw" / "races.csv"
results_path = PROJECT_DIR / "data" / "raw" / "results.csv"
csv_clean = PROJECT_DIR / "data" / "clean" / "races_clean.csv"


races = pd.read_csv(csv_path, na_values=r"\N")
results = pd.read_csv(results_path, na_values=r"\N")

df = races.rename(columns={
    "raceId": "race_id",
    "circuitId": "circuit_id",
    "name": "race_name",
    "time": "start_time",
})

df["is_sprint_weekend"] = df["sprint_date"].notna()

df = df.drop(columns=[
    "url",
    "fp1_date", "fp1_time", "fp2_date", "fp2_time", "fp3_date", "fp3_time",
    "quali_date", "quali_time",
    "sprint_date", "sprint_time",
])


df["date"] = pd.to_datetime(df["date"])

df = df.sort_values(["year", "round"]).reset_index(drop=True)
df["race_order"] = range(1, len(df) + 1)

# 7. Course avec résultat ou non (d'après results.csv)
# has_results = False veut dire "sans résultat dans le dataset" (dataset final, non mis à jour).
# Parmi les 8 courses concernées : la 1184 (« Bahrain Grand Prix in Malaysia », Sepang) est déjà
# courue ; son nom et son circuit sont officiels (calendrier 2026), donc AUCUNE correction.
# Les 7 autres (manches 17 à 23) sont à venir. Toutes sont conservées, sans filtre par année.
df["has_results"] = df["race_id"].isin(results["raceId"])


df = df[["race_id", "race_order", "year", "round", "circuit_id", "race_name",
         "date", "start_time", "is_sprint_weekend", "has_results"]]

assert len(df) == len(races) == 1172, "aucune ligne ne doit être supprimée"
assert not df.duplicated(["year", "round"]).any(), "(year, round) doit être unique"
assert df["date"].is_monotonic_increasing, "race_order doit croître avec la date"
assert df["has_results"].sum() == 1164 and (~df["has_results"]).sum() == 8

# 10. Sauvegarde
df.to_csv(csv_clean, index=False, date_format="%Y-%m-%d")
print("races_clean.csv écrit :", len(df), "lignes")