from pathlib import Path
import pandas as pd

folder = Path("data/processed")
keys = ["race_id", "driver_id"]

files = [
    "grid_features.csv",
    "driver_features.csv",
    "circuit_features.csv",
    "constructor_features.csv",
    "constructor_circuit_features.csv",
]

all_features = None

for filename in files:
    path = folder / filename
    df = pd.read_csv(path)

    # Chaque table doit avoir une seule ligne par course et pilote.
    if df.duplicated(keys).any():
        raise ValueError(f"Doublons sur {keys} dans {filename}")

    # constructor_id sert à identifier l'écurie, ce n'est pas une feature.
    df = df.drop(columns=["constructor_id"], errors="ignore")

    if all_features is None:
        all_features = df
    else:
        all_features = all_features.merge(
            df,
            on=keys,
            how="outer",
            validate="one_to_one",
        )

output = folder / "all_features.csv"
all_features.to_csv(output, index=False)

print(f"Fichier créé : {output}")
print(f"Dimensions : {all_features.shape}")
print("Valeurs manquantes par colonne :")
print(all_features.isna().sum())