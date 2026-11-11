"""clean_circuits.py : nettoyage de la table circuits (propriétaire P4, relecteur P3).
Entrée : data/raw/circuits.csv  ->  Sortie : data/clean/circuits_clean.csv
Lancer depuis la racine du dépôt : python src/cleaning/clean_circuits.py
"""
import pandas as pd

# 1. Lecture
circuits = pd.read_csv("data/raw/circuits.csv", na_values=r"\N")

# 2. Renommage et suppression de url
df = circuits.rename(columns={
    "circuitId": "circuit_id",
    "circuitRef": "circuit_ref",
    "name": "circuit_name",
}).drop(columns=["url"])

# 3. Harmonisation de country : "United States" -> "USA" (1 ligne attendue, circuit 80)
n = (df["country"] == "United States").sum()
df["country"] = df["country"].replace("United States", "USA")
print(n, "ligne corrigée (country)")

# 4. Contrôles simples
assert len(df) == len(circuits) == 78, "aucune ligne ne doit être supprimée"
assert df["circuit_id"].is_unique
assert df.isna().sum().sum() == 0

# 5. Sauvegarde
df.to_csv("data/clean/circuits_clean.csv", index=False)
print("circuits_clean.csv écrit :", len(df), "lignes")
