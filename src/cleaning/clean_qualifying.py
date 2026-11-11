import pandas as pd

"""def clean_qualifying():"""
qualifying=pd.read_csv("Data/Raw/qualifying.csv",na_values=r"\N")
qualifying=qualifying.rename(columns={
    "qualifyId":"qualify_id",
    "raceId":"race_id",
    "driverId":"driver_id",
    "constructorId":"constructor_id",
    "number":"car_number",
    "position":"qualifying_position"
 })
qualifying.to_csv("Data/Clean/qualifying_clean.csv",index=False)

 #if __name__=="__main__":
   #clean_qualifying()


