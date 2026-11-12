import html
import pandas as pd

def clean_drivers():
 drivers=pd.read_csv("data/raw/drivers.csv",na_values=r"\N")


 drivers=drivers.rename(columns={
    "driverId":"driver_id",
    "driverRef":"driver_ref",
    "number":"car_number",
    "code":"driver_code",
    "forename":"driver_forname",
    "surname":"driver_surname",
    "dob":"driver_dob",
    "nationality":"driver_nationality",
  })

 drivers=drivers.drop(columns=["url"])

 drivers["driver_dob"]=pd.to_datetime(drivers["driver_dob"])

 drivers["car_number"]=pd.to_numeric(drivers["car_number"])

 for col in ["driver_ref","driver_code","driver_forname","driver_surname","driver_nationality"]:
    drivers[col]=drivers[col].str.strip().map(
        lambda x: html.unescape(x) if isinstance(x,str) else x
    )

 assert drivers["driver_id"].is_unique

 drivers.to_csv("data/clean/drivers_clean.csv", index=False)

if __name__=="__main__":
    clean_drivers()






