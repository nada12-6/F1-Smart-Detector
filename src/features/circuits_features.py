
import pandas as pd
df = pd.read_csv("data/processed/f1_merged_2014.csv")

# Trier chronologiquement les participations
# pour chaque pilote sur chaque circuit
df = df.sort_values(
    ["driver_id", "circuit_id", "race_order"]
).reset_index(drop=True)

# Identifier les podiums (1 = Top 3, 0 = hors Top 3)
df["is_podium"] = (df["position_order"] <= 3).astype(int)

# Nombre de participations précédentes du pilote
# sur ce circuit depuis 2014
df["previous_circuit_races"] = (
    df.groupby(["driver_id", "circuit_id"]).cumcount()
)

# Moyenne des positions précédentes sur ce circuit
# Les abandons sont inclus via position_order
df["driver_circuit_avg_position"] = (
    df.groupby(["driver_id", "circuit_id"])["position_order"]
      .transform(
          lambda s: s.shift(1).expanding().mean()
      )
)

# Proportion des podiums précédents sur ce circuit
df["driver_circuit_top3_rate"] = (
    df.groupby(["driver_id", "circuit_id"])["is_podium"]
      .transform(
          lambda s: s.shift(1).expanding().mean()
      )
)


# 0 = aucune participation précédente sur ce circuit
# 1 = au moins une participation précédente
df["driver_circuit_has_history"] = (
    (df["previous_circuit_races"] > 0).astype(int)
)


features = [
    "driver_circuit_avg_position",
    "driver_circuit_top3_rate",
    "driver_circuit_has_history"
]

print("\nNombre total de lignes :", len(df))

print("\nValeurs manquantes par feature :")
print(df[features].isna().sum())

print("\nPourcentage de NaN :")
print((df[features].isna().mean() * 100).round(2))

print("\nRépartition des NaN par année :")
print(
    df.groupby("year")[features]
      .apply(lambda x: x.isna().sum())
)

print("\nRépartition de l'indicateur :")
print(df["driver_circuit_has_history"].value_counts())

# Vérifier les premières participations
assert df.loc[
    df["driver_circuit_has_history"] == 0,
    ["driver_circuit_avg_position", "driver_circuit_top3_rate"]
].isna().all().all()

# Vérifier les participations avec historique
assert df.loc[
    df["driver_circuit_has_history"] == 1,
    ["driver_circuit_avg_position", "driver_circuit_top3_rate"]
].notna().all().all()

# Vérifier que les taux sont compris entre 0 et 1
assert df["driver_circuit_top3_rate"].dropna().between(0, 1).all()


cols = [
    "race_id",
    "driver_id",
    "driver_circuit_avg_position",
    "driver_circuit_top3_rate",
    "driver_circuit_has_history"
]

df[cols].to_csv(
    "data/processed/circuit_features.csv",
    index=False
)

print("\nFichier circuit_features.csv généré avec succès !")
