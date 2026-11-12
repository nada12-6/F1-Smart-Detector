import pandas as pd
import os



df = pd.read_csv("data/raw/results.csv")
df = df.replace(r"\N" , pd.NA)

print("Doublons exacts :", df.duplicated().sum())
df = df.drop_duplicates()

numeric_columns = [
    "number",
    "grid",
    "position",
    "milliseconds",
    "fastestLap",
    "rank",
]
for column in numeric_columns :
    df[column] = pd.to_numeric(df[column],errors= "coerce").astype("Int64")

df["fastestLapSpeed"] = pd.to_numeric( df["fastestLapSpeed"], errors="coerce")

print("Types des colonnes :", df.dtypes)

column_mapping = {
    "resultId": "result_id",
    "raceId": "race_id",
    "driverId": "driver_id",
    "constructorId": "constructor_id",
    "statusId": "status_id",
    "number": "car_number",
    "position": "finish_position",
    "positionText": "position_text",
    "positionOrder": "position_order",
    "fastestLap": "fastest_lap",
    "fastestLapTime": "fastest_lap_time",
    "fastestLapSpeed": "fastest_lap_speed",
}

df = df.rename(columns=column_mapping)

rank_zero_count = df["rank"].eq(0).sum()

df.loc[df["rank"].eq(0), "rank"] = pd.NA
print("rank = 0 convertis en valeur manquante :", rank_zero_count)

print(
    "Lignes appartenant à une clé race_id/driver_id répétée :",
    df.duplicated(["race_id", "driver_id"], keep=False).sum()
)
print("Valeurs manquantes :\n", df.isna().sum())

os.makedirs("data/clean", exist_ok=True)
df.to_csv("data/clean/results_clean.csv", index=False)
print("Fichier results_clean.csv enregistré avec succès !")