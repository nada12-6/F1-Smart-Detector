"""clean_races.py : nettoyage de la table races (propriétaire P4, relecteur P3).
Entrée : data/raw/races.csv et data/raw/results.csv  ->  Sortie : data/clean/races_clean.csv
Lancer depuis la racine du dépôt : python src/cleaning/clean_races.py
"""
import pandas as pd

# 1. Lecture (na_values pour que \N devienne une vraie valeur vide)
races = pd.read_csv("data/raw/races.csv", na_values=r"\N")
results = pd.read_csv("data/raw/results.csv", na_values=r"\N")

# 2. Renommage (bloc 4)
df = races.rename(columns={
    "raceId": "race_id",
    "circuitId": "circuit_id",
    "name": "race_name",
    "time": "start_time",
})

# 3. Colonne sprint : vrai si sprint_date est renseignée (à faire AVANT la suppression)
df["is_sprint_weekend"] = df["sprint_date"].notna()

# 4. Suppression des colonnes inutiles (justification dans le document d'EDA)
df = df.drop(columns=[
    "url",
    "fp1_date", "fp1_time", "fp2_date", "fp2_time", "fp3_date", "fp3_time",
    "quali_date", "quali_time",
    "sprint_date", "sprint_time",
])

# 5. Types : date en vraie date, start_time reste du texte
df["date"] = pd.to_datetime(df["date"])

# 6. Ordre des courses : tri par (year, round), jamais par race_id
df = df.sort_values(["year", "round"]).reset_index(drop=True)
df["race_order"] = range(1, len(df) + 1)

# 7. Course avec résultat ou non (d'après results.csv)
# has_results = False veut dire "sans résultat dans le dataset" (dataset final, non mis à jour).
# Parmi les 8 courses concernées : la 1184 (« Bahrain Grand Prix in Malaysia », Sepang) est déjà
# courue ; son nom et son circuit sont officiels (calendrier 2026), donc AUCUNE correction.
# Les 7 autres (manches 17 à 23) sont à venir. Toutes sont conservées, sans filtre par année.
df["has_results"] = df["race_id"].isin(results["raceId"])

# 8. Colonnes dans un ordre lisible
df = df[["race_id", "race_order", "year", "round", "circuit_id", "race_name",
         "date", "start_time", "is_sprint_weekend", "has_results"]]

# 9. Contrôles simples
assert len(df) == len(races) == 1172, "aucune ligne ne doit être supprimée"
assert not df.duplicated(["year", "round"]).any(), "(year, round) doit être unique"
assert df["date"].is_monotonic_increasing, "race_order doit croître avec la date"
assert df["has_results"].sum() == 1164 and (~df["has_results"]).sum() == 8

# 10. Sauvegarde
df.to_csv("data/clean/races_clean.csv", index=False, date_format="%Y-%m-%d")
print("races_clean.csv écrit :", len(df), "lignes")
