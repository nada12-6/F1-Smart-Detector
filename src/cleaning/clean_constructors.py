import pandas as pd
import numpy as np
import os
constructors = pd.read_csv("data/raw/constructors.csv", na_values=r"\N")
print(constructors.dtypes)
print(constructors.shape)

constructors=constructors.drop(columns={"url"})


constructors = constructors.rename(columns={
    "constructorId":"constructor_id",
    "constructorRef":"constructor_ref",
    "name":"constructor_name",
    "nationality" :"constructor_nationality",
})

os.makedirs("data/clean", exist_ok=True)

constructors.to_csv("data/clean/constructors_clean.csv", index=False)

print("Fichier constructors_clean.csv enregistré avec succès !")