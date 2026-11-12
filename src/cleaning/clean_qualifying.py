import pandas as pd

"""def clean_qualifying():"""
qualifying=pd.read_csv("data/raw/qualifying.csv",na_values=r"\N")
qualifying=qualifying.rename(columns={
    "qualifyId":"qualify_id",
    "raceId":"race_id",
    "driverId":"driver_id",
    "constructorId":"constructor_id",
    "number":"car_number",
    "position":"qualifying_position"
 })
qualifying.to_csv("data/clean/qualifying_clean.csv",index=False)

 #if __name__=="__main__":
   #clean_qualifying()


