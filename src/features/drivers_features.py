import pandas as pd
import numpy as np

df=pd.read_csv("data/processed/f1_merged_2014.csv")
df["date"]=pd.to_datetime(df["date"])

#on tri le tableau afin d'utiliser shift et rolling qui necessite un ordre chronologique respecté
df=df.sort_values(["driver_id", "date", "round"]).reset_index(drop=True)
#on cree les variables qui aideront a la creation de nos features
df["is_podium"]=np.where(df["position_order"]<=3, 1, 0)
#prev position est position order shifté dune ligne vers le bas pour chaque driver
df["prev_position"]=df.groupby("driver_id")["position_order"].shift(1)
df["prev_podium"]=df.groupby("driver_id")["is_podium"].shift(1)
#creation de features
df["driver_avg_position_last_5"]=df.groupby("driver_id")["prev_position"].transform(
    lambda s: s.rolling(5, min_periods=1).mean()
)
df["driver_top_3_rate_last_5"]=df.groupby("driver_id")["prev_podium"].transform(
    lambda s:s.rolling(5, min_periods=1).mean()
)

df=df.drop(columns=["is_podium","prev_position","prev_podium"])
first_races = df.groupby("driver_id").head(1)
assert first_races["driver_avg_position_last_5"].isna().all()
assert first_races["driver_top_3_rate_last_5"].isna().all()
assert df["driver_top_3_rate_last_5"].dropna().between(0,1).all()

print("Missing values: \n", df[["driver_avg_position_last_5","driver_top_3_rate_last_5"]].isna().sum())

cols=["race_id","driver_id","driver_avg_position_last_5","driver_top_3_rate_last_5"]
df[cols].to_csv("data/processed/driver_features.csv", index=False)

