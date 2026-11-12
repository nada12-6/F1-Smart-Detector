import pandas as pd
import os

df = pd.read_csv("data/raw/status.csv")
df = df.rename(columns={"statusId": "status_id"})


print("Doublons exacts :", df.duplicated().sum())
print("Identifiants status_id répétés :", df["status_id"].duplicated().sum())
print("Valeurs manquantes :\n", df.isna().sum())

os.makedirs("data/clean", exist_ok=True)
df.to_csv("data/clean/status_clean.csv", index=False)
print("Fichier status_clean.csv enregistré avec succès !")
