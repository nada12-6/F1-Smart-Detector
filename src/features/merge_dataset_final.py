import pandas as pd
from pathlib import Path


BASE_COLS=["driver_id","race_id","constructor_id","date","round","position_order"]

base = pd.read_csv("data/processed/f1_merged_2014.csv")
missing = [c for c in BASE_COLS if c not in base.columns]
assert not missing, f"Colonnes absentes de la base: {missing}"
base = base[BASE_COLS]
assert not base.duplicated(["race_id", "driver_id"]).any(), "Doublons dans la base"

blocks={
    "driver_features": ["race_id","driver_id"],
    "circuit_features": ["race_id","driver_id"],
    "constructor_circuit_features":["race_id","driver_id","constructor_id"],
    "constructor_features":["race_id","driver_id","constructor_id"],
    "grid_features":["race_id","driver_id"]
}

df=base.copy()
for name,keys in blocks.items():
    feat=pd.read_csv(f"data/processed/{name}.csv")
    missing_keys = [k for k in keys if k not in feat.columns]
    assert not missing_keys, f"{name}: clés absentes {missing_keys}, colonnes = {feat.columns.tolist()}"

    overlap = (set(feat.columns) & set(df.columns)) - set(keys)
    assert not overlap, f"{name}: colonnes déjà présentes (risque de _x/_y): {sorted(overlap)}"

    rows_before = len(df)
    df = df.merge(feat, on=keys, how="left", validate="many_to_one")
    assert len(df) == rows_before, f"{name}: le merge a dupliqué des lignes"
    print(f"{name}: +{len(feat.columns) - len(keys)} colonnes")

assert len(df) == len(base)
assert not df.duplicated(["race_id", "driver_id"]).any()
assert not [c for c in df.columns if c.endswith(("_x", "_y"))], "Colonnes _x/_y détectées"

print("\nShape finale:", df.shape)
print("Valeurs manquantes (colonnes concernées):")
print(df.isna().sum()[lambda s: s > 0])

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values(["date", "race_id", "driver_id"]).reset_index(drop=True)

output = Path("data/processed/f1_dataset_final.csv")
output.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output, index=False)

