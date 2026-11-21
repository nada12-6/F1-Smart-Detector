import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/f1_merged_2014.csv")
df = df.sort_values(["driver_id", "race_order"]).copy()


#feature 1: grid_position
# Les 7 non-partants identifiés
DNS_cases = [
    (926, 822),    # Bottas 2015
    (927, 829),    # Stevens 2015
    (983, 8),      # Räikkönen 2017
    (1065, 852),   # Tsunoda 2021
    (1075, 854),   # Schumacher 2022
    (1113, 840),   # Stroll 2023
    (1118, 844)    # Leclerc 2023
]

df["grid_position"]=df["grid"].astype("Float64")
df["is_dns"] = False

max_grid = df.groupby("race_id")["grid"].transform("max")
df.loc[df["grid"]==0, "grid_position"] = max_grid + 1

for race_id , driver_id in DNS_cases:
    mask= ((df["race_id"]==race_id) & (df["driver_id"] == driver_id))
    df.loc[mask,"is_dns"] = True

df.loc[df["is_dns"],"grid_position"] = pd.NA

#feature 2 : driver_p1_starts

df["is_starter"] = 1
df.loc[df["position_text"] == "W", "is_starter"] = 0
df.loc[df["is_dns"] , "is_starter"] =0

df["is_p1_starts"] = ((df["grid"]==1) & (df["is_starter"] == 1)).astype("int")
df["driver_p1_starts"] =(df.groupby("driver_id")["is_p1_starts"].transform(lambda x : x.cumsum().shift(1).fillna(0)).astype("int"))

#feature 3 : driver_dnf_rate

# 2. Initialiser les colonnes
#df["is_starter"] = 1
df["is_dnf"] = pd.NA

# 3. Identifier les non-partants
# W = retrait avant le départ dans nos données
#df.loc[df["position_text"] == "W", "is_starter"] = 0


# 4. Pilotes ayant terminé la course
finished = (
    (df["status"] == "Finished")
    | df["status"].str.match(r"^\+\d+ Laps?$", na=False)
)

df.loc[finished, "is_dnf"] = 0

# 5. Pilotes ayant abandonné
# Tous les autres statuts sont considérés comme DNF
# sauf les disqualifications, traitées ensuite
df.loc[
    ~finished & (df["is_starter"] == 1),
    "is_dnf"
] = 1

# 6. Disqualifications après avoir terminé
df.loc[
    df["status"].isin(["Disqualified", "Excluded", "Underweight"])
    & ~(
        (df["year"] == 2024)
        & (df["race_id"] == 1138)
        & (df["driver_surname"] == "Hülkenberg")
    ),
    "is_dnf"
] = 0

# 7. Hülkenberg, São Paulo 2024 :
# disqualifié pendant la course
df.loc[
    (df["year"] == 2024)
    & (df["race_name"] == "São Paulo Grand Prix")
    & (df["driver_surname"] == "Hülkenberg"),
    "is_dnf"
] = 1

# 8. Exclure les non-partants
df.loc[df["is_starter"] == 0, "is_dnf"] = pd.NA

# 9. Convertir les types
df["is_dnf"] = df["is_dnf"].astype("Int64")

# 10. Cumuls des départs précédents
df["previous_starts"] = (
    df.groupby("driver_id")["is_starter"]
      .transform(lambda x: x.cumsum().shift(1).fillna(0))
)

# 11. Cumuls des DNF précédents
df["previous_dnfs"] = (
    df.groupby("driver_id")["is_dnf"]
      .transform(lambda x: x.fillna(0).cumsum().shift(1).fillna(0))
)

# 12. Calculer le taux de DNF
df["driver_dnf_rate"] = (
    df["previous_dnfs"] / df["previous_starts"].replace(0,np.nan)
)

print("Valeurs manquantes :")
print(
    df[
        ["grid_position", "driver_p1_starts", "driver_dnf_rate"]
    ].isna().sum()
)

print("\nNombre de non-partants identifiés :")
print((df["is_starter"] == 0).sum())

print("\nVérification du DNF rate :")
print(
    df["driver_dnf_rate"].dropna().between(0, 1).all()
)

assert not df.duplicated(["race_id", "driver_id"]).any()

assert (
    df["driver_dnf_rate"].isna().sum()
    == (df["previous_starts"] == 0).sum()
)


df = df.drop(
    columns=[
        "is_starter",
        "is_dnf",
        "previous_starts",
        "previous_dnfs",
        "is_p1_starts"
    ]
)


cols = [
    "race_id", "driver_id",
    "grid_position", "driver_p1_starts", "driver_dnf_rate"
]
df[cols].to_csv("data/processed/grid_features.csv", index=False)
