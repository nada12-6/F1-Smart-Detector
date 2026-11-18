
import pandas as pd


def calculer_circuit_avg_position(df_constructors, constructorid, circuitid, race_order):
    previous = df_constructors[
        (df_constructors["constructor_id"] == constructorid) &
        (df_constructors["circuit_id"] == circuitid) &
        (df_constructors["race_order"] < race_order)]
    if previous.empty:
        return 10.0
    return previous["position_order"].mean()


def calculer_circuit_top3_rate(df_constructors, constructorid, circuitid, race_order):
    previous = df_constructors[
        (df_constructors["constructor_id"] == constructorid) &
        (df_constructors["circuit_id"] == circuitid) &
        (df_constructors["race_order"] < race_order)
    ]

    if previous.empty:
        return 0.0
    return (previous["position_order"] <= 3).mean()


def build_constructor_circuit_features(df):

    df_constructors = df[["race_id", "driver_id", "race_order", "constructor_id", "circuit_id", "position_order"]].copy()

    df_constructors["constructor_circuit_avg_position"] = (
        df_constructors.apply(
            lambda row: calculer_circuit_avg_position(df_constructors,row["constructor_id"],row["circuit_id"],row["race_order"]),axis=1))
    df_constructors["constructor_circuit_top3_rate"] = (
        df_constructors.apply(
            lambda row: calculer_circuit_top3_rate(df_constructors,row["constructor_id"],row["circuit_id"],row["race_order"]), axis=1))

    return df_constructors


if __name__ == "__main__":
    df = pd.read_csv("data/processed/f1_merged_2014.csv")
    result = build_constructor_circuit_features(df)
    cols = [
        "race_id", "driver_id", "constructor_id",
        "constructor_circuit_avg_position",
        "constructor_circuit_top3_rate"
    ]
    result[cols].to_csv("data/processed/constructor_circuit_features.csv", index=False)
    print("constructor_circuit_features.csv généré !")
