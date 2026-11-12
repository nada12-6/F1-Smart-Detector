from pathlib import Path
import pandas as pd

# 1. Charger les tables nettoyées
folder = Path('data/clean')
results = pd.read_csv(folder / 'results_clean.csv', na_values=r'\N')
races = pd.read_csv(folder / 'races_clean.csv', na_values=r'\N')
circuits = pd.read_csv(folder / 'circuits_clean.csv', na_values=r'\N')
drivers = pd.read_csv(folder / 'drivers_clean.csv', na_values=r'\N')
constructors = pd.read_csv(folder / 'constructors_clean.csv', na_values=r'\N')
status = pd.read_csv(folder / 'status_clean.csv', na_values=r'\N')
qualifying = pd.read_csv(folder / 'qualifying_clean.csv', na_values=r'\N')

# 2. Renommer les colonnes communes qui ne sont pas des clés
# pour ne pas confondre les numéros et écuries des différentes tables.
drivers = drivers.rename(columns={'car_number': 'driver_permanent_car_number'})
qualifying = qualifying.rename(columns={
    'constructor_id': 'qualifying_constructor_id',
    'car_number': 'qualifying_car_number'
})

# 3. Fusionner : results est notre table de départ.
# how='left' conserve ses lignes, même sans qualification.
# validate='many_to_one' empêche une jointure de multiplier les lignes.
df = results.merge(races, on='race_id', how='left', validate='many_to_one')
df = df.merge(circuits, on='circuit_id', how='left', validate='many_to_one')
df = df.merge(drivers, on='driver_id', how='left', validate='many_to_one')
df = df.merge(constructors, on='constructor_id', how='left', validate='many_to_one')
df = df.merge(status, on='status_id', how='left', validate='many_to_one')
df = df.merge(qualifying, on=['race_id', 'driver_id'], how='left', validate='many_to_one')

# 4. Contrôler et sauvegarder
assert len(df) == len(results), 'La fusion a changé le nombre de lignes !'
assert df['result_id'].is_unique, 'Des result_id sont dupliqués !'
assert df['race_order'].notna().all(), 'Certaines courses sont introuvables !'

df = df.sort_values(['race_order', 'driver_id']).reset_index(drop=True)
output = Path('data/processed/f1_merged.csv')
output.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output, index=False)

print(f'Fusion terminée : {len(df)} lignes, {len(df.columns)} colonnes')
print(f'Fichier créé : {output}')
