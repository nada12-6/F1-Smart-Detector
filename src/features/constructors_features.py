import pandas as pd
import numpy as np
MECHANICAL_STATUSES = {
    "Engine", "Gearbox", "Transmission", "Clutch",
    "Hydraulics", "Electrical", "Radiator", "Suspension",
    "Brakes", "Differential", "Overheating", "Mechanical",
    "Driveshaft", "Fuel pressure", "Water pressure",
    "Refuelling", "Throttle", "Steering", "Technical",
    "Electronics", "Heat shield fire", "Exhaust",
    "Oil leak", "Water leak", "Fuel pump", "Track rod",
    "Oil pressure", "Engine fire", "Engine misfire",
    "Out of fuel", "Wheel nut", "Pneumatics", "Handling",
    "Wheel bearing", "Fuel system", "Oil line",
    "Fuel rig", "Launch control", "Fuel", "Power loss",
    "Vibrations", "Drivetrain", "Ignition", "Battery",
    "Stalled", "Halfshaft", "Crankshaft", "Alternator",
    "Oil pump", "Fuel leak", "Injection", "Distributor",
    "Turbo", "CV joint", "Water pump", "Spark plugs",
    "Fuel pipe", "Oil pipe", "Axle", "Water pipe",
    "Magneto", "Supercharger", "Power Unit", "ERS",
    "Cooling system", "Vibration", "Safety switch"
}
ACCIDENT_STATUSES = {
    "Accident", "Collision", "Spun off",
    "Collision damage", "Fatal accident"
}
AMBIGUOUS_STATUSES = {
    "Retired", "Tyre", "Driver Seat", "Puncture",
    "Tyre puncture", "Front wing", "Broken wing",
    "Rear wing", "Undertray", "Damage", "Debris",
    "Wheel", "Wheel rim", "Fire", "Chassis",
    "Safety belt", "Brake duct", "Seat",
    "Not classified"
}

OTHER_STATUSES = {
    "Disqualified", "Withdrew", "107% Rule",
    "Did not qualify", "Did not prequalify",
    "Safety", "Injured", "Physical", "Injury",
    "Safety concerns", "Not restarted", "Underweight",
    "Excluded", "Driver unwell", "Eye injury", "Illness"
}


def classify_constructor_dnf(df_constructors):
    df_constructors = df_constructors.copy()
    finished = (df_constructors["status"].eq("Finished")| df_constructors["status"].str.match(r"^\+\d+ Laps?$", na=False))
    df_constructors["dnf_category"] = np.select([
            finished,df_constructors["status"].isin(MECHANICAL_STATUSES),df_constructors["status"].isin(ACCIDENT_STATUSES),
            df_constructors["status"].isin(AMBIGUOUS_STATUSES),df_constructors["status"].isin(OTHER_STATUSES)],
        ["Finished","Mechanical","Accident","Ambiguous","Other"],
        default="Unclassified")
    
#Var binaire : 1 = DNF mécanique identifié, 0 = sinon
#j'ai considéré seulement les dnf mecaniques pour montrer l'influence de la voiture de l'écurie
    df_constructors["is_mechanical_dnf"] = (df_constructors["dnf_category"] == "Mechanical").astype(int)
    return df_constructors


def calculer_mechanical_dnf_last5(df_constructors, constructorid, race_order):

    previous = df_constructors[
        (df_constructors["constructor_id"] == constructorid)
        & (df_constructors["race_order"] < race_order)
    ]
    last5 = (
        previous["race_order"]
        .drop_duplicates()
        .sort_values()
        .tail(5)
    )
    last5_results = previous[
        previous["race_order"].isin(last5)
    ]
    return last5_results["is_mechanical_dnf"].mean()



def calculer_avg_last5(df_constructors, constructorid, race_order):
    previous = df_constructors[
        (df_constructors["constructor_id"] == constructorid) &
        (df_constructors["race_order"] < race_order)
    ]
    last5 = (
        previous["race_order"]
        .drop_duplicates()
        .sort_values()
        .tail(5)
    )
    last5_results = previous[
        previous["race_order"].isin(last5)
    ]
    return last5_results["position_order"].mean()


def calculer_top3_last5(df_constructors, constructorid, race_order):
    previous = df_constructors[
        (df_constructors["constructor_id"] == constructorid) &
        (df_constructors["race_order"] < race_order)
    ]
    last5 = (
        previous["race_order"]
        .drop_duplicates()
        .sort_values()
        .tail(5)
    )
    last5_results = previous[
        previous["race_order"].isin(last5)
    ]
    return (last5_results["position_order"] <= 3).mean()


def build_constructor_features(df):
    df_constructors = df[
        ["race_id", "driver_id", "race_order", "constructor_id", "position_order", "status"]
    ].copy()
    df_constructors["constructor_avg_position_last5"] = (
        df_constructors.apply(
            lambda row: calculer_avg_last5(
                df_constructors,
                row["constructor_id"],
                row["race_order"]
            ),
            axis=1
        )
    )

    df_constructors["constructor_top3_rate_last5"] = (
        df_constructors.apply(
            lambda row: calculer_top3_last5(
                df_constructors,
                row["constructor_id"],
                row["race_order"]
            ),
            axis=1
        )
    )

    df_constructors = classify_constructor_dnf(df_constructors)
    df_constructors["constructor_mechanical_dnf_rate_last5"] = (
        df_constructors.apply(
            lambda row: calculer_mechanical_dnf_last5(
                df_constructors, row["constructor_id"], row["race_order"]
            ), axis=1
        )
    )

    return df_constructors


if __name__ == "__main__":
    df = pd.read_csv("data/processed/f1_merged_2014.csv")
    result = build_constructor_features(df)
    cols = [
        "race_id", "driver_id", "constructor_id",
        "constructor_avg_position_last5",
        "constructor_top3_rate_last5",
        "constructor_mechanical_dnf_rate_last5"
    ]
    result[cols].to_csv("data/processed/constructor_features.csv", index=False)
    print("constructor_features.csv généré !")
