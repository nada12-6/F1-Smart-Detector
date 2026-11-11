# F1 Smart Predictor

Prédire si un pilote de Formule 1 termine dans le **Top 3** d'une course (classification binaire, cible `top3`), à partir de ses caractéristiques et de celles de la course.

- **Données** : dataset Kaggle « Formula 1 World Championship » (Rohan Rao), 1950-2026.
- **Modèles prévus** : Logistic Regression (baseline), Random Forest (principal), éventuellement Gradient Boosting.
- **Évaluation** : split **chronologique** (jamais aléatoire), precision, recall, F1, matrice de confusion.
- **Période de modélisation** : saisons 2014 à 2026 (`YEAR_MIN = 2014` dans `src/config.py`).

> Phase actuelle : **nettoyage des tables** (voir `docs/CONTRAT_NETTOYAGE.md`). Le RAG et l'interface viendront après la phase ML.

## Équipe et tables

| Membre | Rôle | Tables à nettoyer | Relu par |
|---|---|---|---|
| P1 | grid / basic | `results`, `status` | P2 |
| P2 | driver form | `drivers`, (`qualifying`) | P1 |
| P3 | constructor form | `constructors` | P4 |
| P4 | circuit history | `races`, `circuits` | P3 |

Une table = un propriétaire. Un script n'est terminé qu'après relecture par une autre personne.

## Structure du dépôt

```
data/
  raw/          données brutes Kaggle (jamais modifiées, non versionnées)
  clean/        tables propres : <table>_clean.csv
  features/     tables de features
docs/           contrat de nettoyage, EDA, documents de nettoyage
notebooks/      EDA : eda_<table>_<prénom>.ipynb (dossier à part des scripts)
src/
  config.py     constantes partagées (YEAR_MIN)
  cleaning/     clean_<table>.py
  features/     calcul des features
requirements.txt
```

## Installation

```
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Télécharger le dataset Kaggle et déposer les CSV dans `data/raw/` (par exemple `data/raw/races.csv`, `data/raw/results.csv`). Les fichiers bruts ne sont pas versionnés et ne doivent jamais être modifiés.

## Lancer le nettoyage

Toujours depuis la racine du dépôt :

```
python src/cleaning/clean_races.py       # -> data/clean/races_clean.csv
python src/cleaning/clean_circuits.py    # -> data/clean/circuits_clean.csv
```

Ordre de livraison : `races_clean` en premier (elle contient `race_order`, dont dépendent toutes les features), puis `results_clean`, puis le reste en parallèle.

## Règles de travail (résumé du contrat)

- Fichiers bruts jamais modifiés ; nettoyage **par script**, relançable, qui redonne la même table.
- Rien n'est supprimé sans être compté et expliqué ; **aucune imputation** au nettoyage.
- Lecture avec `pd.read_csv(..., na_values=r"\N")`.
- **Aucun filtre par année dans les scripts de nettoyage** : tout l'historique est conservé, le filtre 2014+ se fait une seule fois, à la fusion finale.
- **Ne jamais trier ni comparer des courses par `race_id`** : utiliser `race_order` ou (`year`, `round`).
- Colonnes en `snake_case`, en anglais ; clés identiques partout (`race_id`, `driver_id`, `constructor_id`, `circuit_id`, `status_id`) ; colonnes `url` supprimées.
- Code en anglais, documentation en français.

### Git

- Une branche par table : `clean/<table>` (ex. `clean/races`, `clean/circuits`).
- Messages de commit : `<table> : ce qui a changé` (ex. `races : lire avec na_values`).
- Rien n'est fusionné sans relecture (pull request relue par le relecteur désigné).
- Un membre ne modifie jamais le script ou la table d'un autre : il le signale au propriétaire.

## Documentation

| Document | Contenu |
|---|---|
| [`docs/CONTRAT_NETTOYAGE.md`](docs/CONTRAT_NETTOYAGE.md) | Règles du nettoyage (blocs 0 à 5) : la référence de toute décision |
| [`docs/EDA_RACES_CIRCUITS.md`](docs/EDA_RACES_CIRCUITS.md) | EDA des tables `races` et `circuits` : constats et décisions |
| [`docs/DOC_FINAL_NETTOYAGE_RACES_CIRCUITS.md`](docs/DOC_FINAL_NETTOYAGE_RACES_CIRCUITS.md) | Résultat du nettoyage : transformations, dictionnaire des colonnes, contrôles |

## Avancement

| Table | Propriétaire | Statut |
|---|---|---|
| `races`, `circuits` | P4 | scripts écrits, en attente de relecture par P3 |
| `results`, `status` | P1 | à renseigner |
| `drivers`, `qualifying` | P2 | à renseigner |
| `constructors` | P3 | à renseigner |

## Points à connaître

- **`race_id` n'est pas chronologique** (61 cas contraires) : toujours `race_order`.
- **`has_results = False` signifie « sans résultat dans le dataset »**, pas « à venir ». Sur les 8 courses concernées (`race_id` 1184 à 1191), la 1184 (« Bahrain Grand Prix in Malaysia », Sepang) est déjà jouée, son nom et son circuit sont officiels ; les 7 autres sont à venir.
- **`is_sprint_weekend`** est une colonne créée par le nettoyage de `races` (30 weekends sprint).
