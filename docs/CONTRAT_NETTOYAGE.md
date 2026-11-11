# Contrat de nettoyage — F1 Smart Predictor

**Version mise à jour — blocs 0 à 5 rédigés, tables `races` et `circuits` nettoyées**

## Modifications de cette version

| Où | Modification | Raison |
|---|---|---|
| Bloc 1, courses sans résultat | Distinction entre la course 1184 (déjà courue, résultat absent du dataset) et les 7 courses réellement à venir | Calendrier officiel 2026 : la manche 16 a eu lieu les 2-4 octobre ; le dataset est final et ne sera pas mis à jour |
| Bloc 2, règle 3 et contrôles | « 8 courses à venir » devient « 8 courses sans résultat » | Même raison |
| Bloc 4, règle 7 | Ajout de `is_sprint_weekend` aux colonnes créées par le nettoyage | Colonne créée par `clean_races.py` |
| Bloc 4, textes | Exception documentée : `country` harmonisé (« United States » devient « USA », 1 ligne) | Décision 2 de l'EDA races et circuits |
| Bloc 4, correspondance races | Colonnes supprimées et créées indiquées | Lisibilité |
| Bloc 5, contrôles races et circuits | Ajout des contrôles `is_sprint_weekend`, `country`, ligne 1184 conservée | Nouveaux traitements |

| Bloc | Sujet | Statut |
|---|---|---|
| 0 | Explorer avant de nettoyer (EDA) | rédigé |
| 1 | Analyse et nettoyage | rédigé |
| 2 | Période du dataset | rédigé |
| 3 | Répartition des tables | rédigé |
| 4 | Nommage | rédigé |
| 5 | Checklist avant de livrer une table | rédigé |

---

## Bloc 0 : Explorer avant de nettoyer (EDA)

L'EDA (*Exploratory Data Analysis*) consiste à **regarder les données avant de les modifier**. Elle ne change aucun fichier : elle sert à découvrir les problèmes que le nettoyage réglera ensuite. Les règles de ce contrat doivent s'appuyer sur ce que vous avez constaté, pas sur des suppositions.

### Les 6 étapes, pour chaque table

| # | Étape | Ce qu'on cherche | Code de départ |
|---|---|---|---|
| 1 | Forme et aperçu | Nombre de lignes et de colonnes, noms qui ont du sens | `df.shape`, `df.head()`, `df.columns` |
| 2 | Types | Une colonne numérique lue comme texte est un signal d'alerte | `df.dtypes` |
| 3 | Valeurs manquantes | Combien par colonne, et **pourquoi** | `df.isna().sum()`, `df.isna().mean()` |
| 4 | Doublons et clé | Quelle colonne (ou paire) rend une ligne unique ? | `df.duplicated().sum()`, `df.duplicated(subset=[...]).sum()` |
| 5 | Distributions | Valeurs impossibles, codées ou extrêmes ; catégories mal écrites | `df.describe()`, `df["col"].value_counts()`, histogrammes |
| 6 | Cible et relations | Équilibre des classes ; lien entre une colonne et la cible | `y.value_counts(normalize=True)`, `df.groupby("col")["top3"].mean()` |

Lecture de départ pour toutes les tables :

```python
import pandas as pd
df = pd.read_csv("results.csv", na_values=r"\N")
```

Pour l'étape 6, la cible n'existe pas encore dans les fichiers. On la crée temporairement, juste pour explorer :

```python
results["top3"] = (results["positionOrder"] <= 3).astype(int)
```

**Contrôle entre tables** (à faire pour chaque identifiant) :

```python
(~results["driverId"].isin(drivers["driverId"])).sum()   # doit valoir 0
```

**Contrôle dans le temps** (utile pour choisir la période, bloc 2) :

```python
merged = results.merge(races[["raceId", "year"]], on="raceId")
merged.groupby("year").size()
merged.groupby("year")["top3"].mean()
```

### Ce que chacun produit

Pour chaque table, un petit tableau de constats :

| Constat | Chiffre | Cause probable | Idée de traitement |
|---|---|---|---|
| `position` vide | 10 953 lignes (39,7 %) | pilotes non classés | garder, utiliser `position_order` pour la cible |
| `grid = 0` | 1 638 lignes | non-qualifiés, départs des stands | signaler, décider ensuite |

Ces tableaux sont la matière des règles du bloc 1. L'EDA n'est utile que si elle laisse une trace écrite.

### Précautions

- **L'EDA ne modifie rien** : elle lit les données et affiche des résultats. Les corrections se font dans les scripts de nettoyage.
- Les **notebooks d'exploration** ne vont pas dans le même dossier que les scripts de nettoyage (ils se fusionnent mal dans Git).
- **Aucun calcul de remplacement** des valeurs manquantes (moyenne, médiane) pendant l'EDA.

---

## Bloc 1 : Analyse et nettoyage

### Règles générales

1. **Les fichiers bruts ne sont jamais modifiés.**
2. **Le nettoyage est fait par un script** que chacun peut relancer et qui redonne exactement la même table.
3. **Rien n'est supprimé sans avoir été compté et expliqué par écrit.**
4. **On n'impute pas** les valeurs manquantes : elles restent vides. Les remplacer (par une moyenne, par exemple) se fait plus tard, uniquement avec les données d'entraînement, pour éviter la fuite de données.

### Pour chaque table, on vérifie

- **Lecture** : fichiers lus avec `na_values=r"\N"`, aucune chaîne `\N` ne reste. Sans cette option, des colonnes comme `position` ou `number` sont lues comme du texte.
- **Types** : nombres, dates et textes corrects (par exemple, `drivers.dob` devient une vraie date).
- **Valeurs manquantes** : on compte, on cherche la cause, on décide. Une valeur manquante n'est pas toujours une erreur : `position` vide veut dire pilote non classé, on garde la ligne.
- **Doublons** : on compte. Les doublons exacts sont supprimés, les autres sont signalés à l'équipe.
- **Valeurs bizarres** : on les signale et on les conserve tant que l'équipe n'a pas décidé (exemples : `grid = 0`, un temps de qualification de `16:42.640`).
- **Textes** : espaces retirés, caractères parasites corrigés (exemple : `Lotus-Pratt &amp; Whitney`).
- **Cohérence entre tables** : chaque identifiant existe dans la table correspondante.
- **Colonnes inutiles** : supprimées avec une justification écrite (exemples : colonnes `url`, `fp1` à `fp3` et `quali` de `races`, vides à 88-93 %).

### Particularités de notre dataset

- **Ordre des courses** : `race_id` ne suit pas l'ordre des dates (61 cas contraires). Pour dire qu'une course vient avant une autre, on trie par (`year`, `round`), jamais par `race_id`.
- **Courses sans résultat** : `races` contient 8 courses de 2026 sans aucun résultat dans le dataset. Elles sont conservées et marquées (`has_results = False`). Le dataset est final et ne sera pas mis à jour. Parmi ces 8 courses :
  - la **manche 16** (`race_id` 1184, « Bahrain Grand Prix in Malaysia », circuit Sepang, 2026-10-04) **a déjà eu lieu** d'après le calendrier officiel 2026, mais son résultat n'est pas dans `results.csv`. Ce nom est le nom officiel, ce n'est pas une erreur : **aucune correction** ;
  - les **7 courses suivantes** (manches 17 à 23) sont réellement à venir.

  Ce sont ces courses que le modèle pourra prédire.

---

## Bloc 2 : Période du dataset

### Ce qu'on décide

Quelles saisons forment le dataset utilisé pour **entraîner et évaluer** le modèle.

**Décision de l'équipe : saisons 2014 à 2026.**

### Pourquoi choisir une période

Les données de 1950 et celles de 2024 ne décrivent pas le même sport : voitures, règlements, nombre de pilotes, système de qualification, fiabilité. Un modèle entraîné sur tout l'historique apprendrait des règles qui ne valent plus aujourd'hui. Mais plus on réduit la période, moins on a d'exemples. Il faut trouver un compromis.

### Ce que montrent vos données

| Début | Lignes | Courses | Positifs (`top3 = 1`) | Non-partants | Qualifying / pit stops |
|---|---|---|---|---|---|
| 1979 | 20 044 | 851 | 2 553 (12,7 %) | 1 092 | 533 / 612 courses sur 851 |
| 2005 | 9 099 | 433 | 1 299 (14,3 %) | 68 | 433 / 432 sur 433 |
| 2011 | 6 789 | 325 | 975 (14,4 %) | 47 | 325 / 324 sur 325 |
| **2014 (retenu)** | **5 435** | **267** | **801 (14,7 %)** | **38** | **267 / 266 sur 267** |

Ce qui joue en faveur de 2014 :

- **Données homogènes** : chaque course contient exactement 3 « top 3 », il n'y a aucun doublon (course, pilote), et les non-partants sont rares (38 lignes).
- **Informations complètes** : qualifying et temps au tour présents pour chaque course, arrêts aux stands pour 266 sur 267.
- **Époque cohérente** : 2014 marque le début de l'ère hybride (changement de motorisation), donc les performances avant et après ne sont pas comparables.

Ce qu'on accepte en échange : **5 435 lignes seulement** (801 positifs). Le jeu de données est petit, ce qui plaide pour des modèles simples et une évaluation prudente.

### Volume par saison

| Saison | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Courses | 19 | 19 | 21 | 20 | 21 | 21 | 17 | 22 | 22 | 22 | 24 | 24 | 15 |
| Lignes | 407 | 378 | 462 | 400 | 420 | 420 | 340 | 440 | 440 | 440 | 479 | 479 | 330 |

La saison **2026 est incomplète** : 15 courses sur 23 ont des résultats (dernière : Azerbaïdjan, 2026-09-26).

### Historique et filtre : deux usages différents des mêmes données

Le contrat garde **tout l'historique (1950-2026) pendant le nettoyage**, mais le modèle ne s'entraîne que sur **2014-2026**. Ce n'est pas contradictoire, car les deux étapes ont un rôle différent :

> **Le filtre sert à choisir quelles lignes le modèle étudie, alors que l'historique sert à calculer les features de ces lignes.** Ce sont deux usages différents des mêmes données.

```
Fichiers bruts (1950-2026)
        ↓
Nettoyage : toutes les années gardées
        ↓
Calcul des features : utilise tout l'historique
        ↓
Fusion en une seule table
        ↓
Filtre year >= 2014   ← seule étape où l'on filtre
        ↓
Table de modélisation (5 435 lignes)
```

**Exemple.** On veut calculer `driver_wins`, le nombre de victoires d'un pilote **avant** une course. Prenons un pilote qui dispute la première course de 2014 et qui a déjà gagné avant 2014 :

| Choix | Valeur de `driver_wins` |
|---|---|
| On supprime tout ce qui précède 2014 **dès le nettoyage** | `0`, ce qui est faux (le pilote est un vétéran) |
| On **garde l'historique**, puis on filtre à la fin | Le vrai nombre de victoires passées |

Il en va de même pour `driver_experience` (nombre de courses déjà disputées) et pour les moyennes sur les 5 dernières courses : pour les premières courses de 2014, il faut regarder des courses de 2013. Sans l'historique, les premières lignes de 2014 auraient des features fausses ou vides.

**Concrètement :**

- `results_clean` contient **toutes les lignes** (27 568), de 1950 à 2026.
- La table finale que le modèle verra en contient **5 435** (2014 à 2026).
- Les courses de 1950 à 2013 ne servent pas à entraîner le modèle : elles servent de **mémoire** pour calculer correctement les features des courses récentes.

**Règle à retenir** : aucun script de nettoyage ne filtre par année. Le filtre n'apparaît qu'une seule fois, au moment d'assembler la table finale.

### Règles

1. `YEAR_MIN = 2014`, défini **une seule fois** dans un fichier partagé `src/config.py`. Personne ne l'écrit à la main dans son propre script.
2. **Le nettoyage garde tout l'historique (1950-2026).** Le filtre `year >= YEAR_MIN` s'applique **uniquement à la table finale de modélisation**, après la fusion. Raison : les features de carrière (victoires, podiums, expérience) ont besoin des courses d'avant 2014. 21 des 59 pilotes de 2014-2024 avaient déjà couru avant.
3. **Les 8 courses sans résultat** (manches 16 à 23 de 2026) ne font pas partie des 5 435 lignes : elles n'ont pas de résultat, donc pas de cible. La manche 16 (déjà courue, résultat absent du dataset) et les 7 suivantes (à venir) servent à l'**inférence**.
4. **Le découpage entraînement / validation / test** n'est pas défini ici. Il sera fixé dans un contrat séparé. Il se fera **par saison**, jamais au hasard, et il faudra décider comment utiliser 2025 et 2026 (2026 étant incomplète).

### Contrôles du bloc 2

- ☐ `YEAR_MIN = 2014` est défini dans `src/config.py` et nulle part ailleurs.
- ☐ La table de modélisation contient **5 435 lignes** et **267 courses** (tout écart est à expliquer).
- ☐ Chaque course de la table de modélisation a exactement 3 lignes à `top3 = 1`.
- ☐ Le filtre par année n'est appliqué dans **aucun** script de nettoyage, seulement à la fusion.
- ☐ Les 8 courses sans résultat sont présentes dans `races_clean` avec `has_results = False`, et absentes de la table de modélisation.

---

## Bloc 3 : Répartition des tables

### Principe

La répartition du nettoyage s'appuie sur la répartition **future des features** : chaque membre nettoie les tables dont il aura besoin ensuite. Il connaît ainsi bien ses données avant de calculer ses features. **Une table = un propriétaire.**

Attention à ne pas confondre les deux étapes : le nettoyage prépare les tables (types, manquants, doublons), les features sont des colonnes calculées **après**. Pendant le nettoyage, personne ne calcule de moyenne glissante ni de taux.

### Qui utilise quelles tables

| Membre | Rôle (features futures) | Features prévues |
|---|---|---|
| P1 | grid / basic | `grid`, `driver_experience`, `driver_wins`, `driver_podiums` |
| P2 | driver form | `driver_avg_position_3`, `driver_avg_position_5`, `driver_points_5`, `driver_top3_rate_5` |
| P3 | constructor form | les mêmes indicateurs, calculés pour l'écurie |
| P4 | circuit history | `driver_circuit_avg_position`, `driver_circuit_top3_rate`, `constructor_circuit_avg_position`, `constructor_circuit_top3_rate` |

| Table nettoyée | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| `results` | ✅ | ✅ | ✅ | ✅ |
| `races` (ordre des courses) | ✅ | ✅ | ✅ | ✅ |
| `drivers` | | ✅ | | |
| `constructors` | | | ✅ | |
| `circuits` | | | | ✅ |

`results` **et** `races` **servent à tout le monde** : toutes les features se calculent à partir des résultats passés, dans l'ordre des courses. Ces deux tables sont donc critiques.

### Répartition

| Membre | Tables à nettoyer | Fichiers de sortie |
|---|---|---|
| **P1** : grid / basic | `results` (27 568 lignes), `status` (141) | `results_clean`, `status_clean` |
| **P2** : driver form | `drivers` (865), ☐ `qualifying` (11 298, optionnelle) | `drivers_clean`, (`qualifying_clean`) |
| **P3** : constructor form | `constructors` (214) | `constructors_clean` |
| **P4** : circuit history | `races` (1 172), `circuits` (78) | `races_clean`, `circuits_clean` |

**Tables hors v1** (non nettoyées pour l'instant) : `pit_stops`, `lap_times` (réservées au RAG), `driver_standings`, `constructor_standings`, `constructor_results`, `sprint_results`, `seasons`.

| Table | Raison |
|---|---|
| `pit_stops`, `lap_times` | Informations connues **pendant ou après** la course, donc inutilisables telles quelles pour prédire avant le départ. Réservées au RAG. `lap_times` est de plus très volumineuse (883 003 lignes) |
| `driver_standings`, `constructor_standings` | Classements **cumulés après chaque course** : ils contiennent déjà le résultat de la course à prédire, et se recalculent depuis `results` |
| `constructor_results` | Redondante avec `results`, et sa colonne `status` est vide à 99,9 % |
| `sprint_results` | Concerne seulement 29 courses, et son effet passe déjà par `grid` |
| `seasons` | Simple liste d'années, sans information utile |

« Hors v1 » ne veut pas dire « jamais » : `pit_stops` et `lap_times` seront nettoyées plus tard pour le RAG, et toute table peut être ajoutée au périmètre et attribuée à un membre si le modèle en a besoin.

### Équilibrer la charge

Le découpage par features rend la charge **inégale** :

- **P1** : la table la plus grosse et la plus délicate (valeurs manquantes, `grid = 0`, non-partants, doublons des anciennes saisons).
- **P4** : `races` est essentielle (ordre des courses, courses sans résultat). `circuits` est déjà propre.
- **P2 et P3** : tables légères (`drivers` n'a aucun doublon ni date invalide ; `constructors` demande surtout de corriger une entité HTML).

Pour compenser, P2 et P3 prennent des tâches transversales :

- **P2** : relit le script de `results` (P1) et vérifie les identifiants entre `results` et `drivers`. Il prend aussi `qualifying` si l'équipe la retient.
- **P3** : relit le script de `races` (P4) et vérifie les identifiants entre `results` et `constructors`.

### Relecture croisée

| Table (propriétaire) | Relue par |
|---|---|
| `results`, `status` (P1) | P2 |
| `drivers`, `qualifying` (P2) | P1 |
| `constructors` (P3) | P4 |
| `races`, `circuits` (P4) | P3 |

Un script n'est considéré comme terminé qu'après relecture par une autre personne.

### Ordre de livraison

1. **Dès le premier jour**, tout le monde fait l'EDA (bloc 0) de ses tables.
2. **`races_clean` (P4) en premier** : elle contient l'ordre des courses (`race_order`) dont dépendent toutes les features.
3. **`results_clean` (P1) ensuite.**
4. `drivers_clean`, `constructors_clean`, `circuits_clean` sont indépendantes et peuvent être livrées en parallèle.

### Règles de collaboration

- Un membre ne modifie **jamais** le script ou la table d'un autre. S'il trouve un problème, il le signale au propriétaire.
- Chaque membre travaille sur sa propre branche Git, et rien n'est fusionné sans relecture.
- Une colonne utile à un autre membre se demande au propriétaire de la table, elle ne s'ajoute pas soi-même.

### Contrôles du bloc 3

- ☐ Chaque table du périmètre a **un seul propriétaire** et **un relecteur**.
- ☐ `races_clean` est livrée avant que quiconque calcule des features.
- ☐ La décision sur `qualifying` (v1 ou plus tard) est prise.

---

## Bloc 4 : Nommage

### Pourquoi un style commun

Les tables propres seront **fusionnées** par les quatre membres. Si le même identifiant s'appelle `raceId` dans une table et `race_id` dans une autre, la jointure échoue. Si deux colonnes différentes portent le même nom (par exemple `name` dans `races` et dans `constructors`), pandas les renomme tout seul en `name_x` et `name_y`, et personne ne sait plus laquelle est laquelle. Un style commun évite ces deux problèmes.

### Règles pour les colonnes

1. `snake_case` : minuscules, mots séparés par `_`, pas d'espace ni d'accent (`position_order`, pas `positionOrder`).
2. **Colonnes et code en anglais, documentation en français.**
3. **Les clés gardent exactement le même nom dans toutes les tables** : `race_id`, `driver_id`, `constructor_id`, `circuit_id`, `status_id`.
4. **Une colonne ne porte jamais le même nom que dans une autre table**, sauf les clés. Quand il y a collision, on préfixe par l'entité. Dans votre dataset, ce sont `number`, `position`, `time`, `name` et `nationality`.
5. On ne renomme **que** pour passer en `snake_case` ou pour éviter une collision : les autres colonnes gardent leur nom (`grid`, `points`, `laps`...).
6. **Colonnes booléennes** : préfixe `is_` ou `has_` (`has_results`, `is_sprint_weekend`).
7. **Colonnes créées par le nettoyage** : nom explicite, en `snake_case` (`race_order`, `has_results`, `is_sprint_weekend`).
8. **Les colonnes `url` sont supprimées** des tables propres (elles restent dans le brut).

### Correspondance brut → nom commun

Seules les colonnes qui changent sont listées.

| Table | Changements |
|---|---|
| `results` | `resultId` → `result_id`, `raceId` → `race_id`, `driverId` → `driver_id`, `constructorId` → `constructor_id`, `statusId` → `status_id`, `positionText` → `position_text`, `positionOrder` → `position_order`, `fastestLap` → `fastest_lap`, `fastestLapTime` → `fastest_lap_time`, `fastestLapSpeed` → `fastest_lap_speed`, **`number` → `car_number`**, **`time` → `finish_time`** |
| `races` | `raceId` → `race_id`, `circuitId` → `circuit_id`, **`name` → `race_name`**, **`time` → `start_time`**. Supprimées : `url`, `fp1_*`, `fp2_*`, `fp3_*`, `quali_*`, `sprint_date`, `sprint_time`. Créées : `race_order`, `has_results`, `is_sprint_weekend` |
| `drivers` | `driverId` → `driver_id`, `driverRef` → `driver_ref`, **`number` → `driver_number`**, **`nationality` → `driver_nationality`** |
| `constructors` | `constructorId` → `constructor_id`, `constructorRef` → `constructor_ref`, **`name` → `constructor_name`**, **`nationality` → `constructor_nationality`** |
| `circuits` | `circuitId` → `circuit_id`, `circuitRef` → `circuit_ref`, **`name` → `circuit_name`**. Supprimée : `url` |
| `status` | `statusId` → `status_id` |
| `qualifying` (si retenue) | `qualifyId` → `qualify_id`, `raceId` → `race_id`, `driverId` → `driver_id`, `constructorId` → `constructor_id`, **`number` → `car_number`**, **`position` → `qualifying_position`** |

Les noms en gras sont des renommages **pour éviter une collision** : par exemple, `number` désigne le numéro de la voiture dans `results`, mais le numéro permanent du pilote dans `drivers`. Ce sont deux informations différentes.

### Règles pour les valeurs

- **Valeur manquante** : cellule vide (`NaN`). Jamais `-1`, `0`, `"N/A"` ou `"unknown"` pour représenter une absence.
- **Dates** : format `YYYY-MM-DD`.
- **Booléens** : `True` / `False`.
- **Textes** : on garde l'orthographe et les accents d'origine (Räikkönen), on retire seulement les espaces en trop et les caractères parasites. **Une seule exception, écrite et comptée** : dans `circuits`, `country` « United States » est harmonisé en « USA » (1 ligne, `circuit_id` 80, pour s'aligner sur les 11 autres circuits américains).

### Règles pour les features (à respecter dès maintenant)

Format : `<sujet>_<indicateur>_<fenêtre>`, avec ces conventions :

| Élément | Valeurs | Exemples |
|---|---|---|
| Sujet | `driver`, `constructor` | `driver_...`, `constructor_...` |
| Indicateur | `avg_position`, `top3_rate`, `points`, `wins`, `podiums`, `experience` | `driver_wins` |
| Fenêtre | `_3`, `_5` = nombre de courses récentes prises en compte | `driver_avg_position_5` |
| Sans suffixe | historique complet | `driver_podiums` |
| Spécifique à un circuit | `circuit` après le sujet | `driver_circuit_top3_rate` |

Le contrat features précisera comment sont définies ces fenêtres. Ici, on ne fixe que le **style des noms.**

### Règles pour les fichiers et le dépôt

| Élément | Convention | Exemple |
|---|---|---|
| Données brutes | nom d'origine, jamais modifiées | `data/raw/results.csv` |
| Tables propres | `<table>_clean.csv` | `data/clean/results_clean.csv` |
| Scripts de nettoyage | `clean_<table>.py` | `src/cleaning/clean_results.py` |
| Notebooks d'EDA | `eda_<table>_<prénom>.ipynb`, dans un dossier à part | `notebooks/eda_results_amina.ipynb` |
| Constantes partagées | `MAJUSCULES` dans `src/config.py` | `YEAR_MIN = 2014` |
| Branches Git | `clean/<table>` (minuscules, `/` après le préfixe) | `clean/results`, `clean/drivers` |
| Messages de commit | `<table> : ce qui a changé` | `results : lire avec na_values` |

### Contrôles du bloc 4

- ☐ Aucune colonne en `camelCase` dans les tables propres.
- ☐ Aucune colonne ne porte le même nom dans deux tables, à part les clés.
- ☐ Aucune colonne `url` dans les tables propres.
- ☐ Les fichiers et branches suivent les conventions du tableau ci-dessus.
- ☐ Les valeurs manquantes sont de vraies cellules vides, pas des codes.

---

## Bloc 5 : Checklist avant de livrer une table

Chaque propriétaire coche cette liste pour **chacune de ses tables**, puis le relecteur désigné (bloc 3) la vérifie à son tour. Une table n'est considérée comme terminée que lorsque tout est coché.

### Préparation

- ☐ L'EDA des six étapes est faite et les constats sont écrits (bloc 0).

### Lecture et types

- ☐ Le fichier est lu avec `na_values=r"\N"` : aucune chaîne `\N` ne reste.
- ☐ Les types sont corrects (`df.dtypes` vérifié) : identifiants entiers, dates en vraies dates, nombres en nombres.

### Contenu

- ☐ Les valeurs manquantes sont comptées et leur cause est cherchée. Aucune ligne n'est supprimée uniquement parce qu'une valeur est vide, et aucune valeur n'est imputée.
- ☐ Les doublons sont comptés : les doublons exacts sont supprimés, les autres sont signalés à l'équipe.
- ☐ Les valeurs bizarres sont signalées et conservées.
- ☐ Les textes sont nettoyés (espaces, caractères parasites comme `&amp;`).
- ☐ Chaque identifiant existe dans la table correspondante.
- ☐ Les colonnes inutiles sont supprimées avec une justification écrite.
- ☐ Le nombre de lignes avant et après nettoyage est expliqué : rien n'est supprimé en silence.

### Nommage (bloc 4)

- ☐ Toutes les colonnes sont en `snake_case`, avec la correspondance du bloc 4 appliquée.
- ☐ Aucune colonne ne porte le même nom que dans une autre table, sauf les clés.
- ☐ Aucune colonne `url` ne reste.
- ☐ Les noms de fichier, de script et de branche suivent les conventions.

### Période et ordre des courses (blocs 1 et 2)

- ☐ Le script ne filtre **pas** par année : tout l'historique est conservé.
- ☐ Aucun tri ni aucune comparaison de courses n'utilise `race_id` : on utilise (`year`, `round`) ou `race_order`.

### Reproductibilité et relecture

- ☐ Les fichiers bruts n'ont pas été modifiés.
- ☐ Le script relancé à zéro redonne exactement la même table.
- ☐ Le relecteur désigné a relu le script et validé la table.

### Contrôles propres à certaines tables

- ☐ `results` : 27 568 lignes en entrée ; le couple (`race_id`, `driver_id`) est unique à partir de 1979 (les 91 doublons de 1950-1978 sont documentés, pas supprimés).
- ☐ `races` : 1 172 lignes en entrée et en sortie ; (`year`, `round`) est unique ; `race_order` croît avec la date ; `has_results` vaut vrai pour 1 164 courses et faux pour 8 ; `is_sprint_weekend` vaut vrai pour 30 courses ; `sprint_date`, `sprint_time`, `fp*` et `quali_*` sont supprimées ; la ligne 1184 est conservée telle quelle.
- ☐ `circuits` : 78 lignes en entrée et en sortie ; aucune valeur manquante ; `country` : 1 ligne harmonisée (« United States » → « USA »).
- ☐ `constructors` : plus aucune entité HTML dans `constructor_name`.

---

## Reporté à d'autres contrats

- **Contrat features** : la cible `top3`, les colonnes connues seulement après la course, les fenêtres de calcul, le traitement des valeurs vides des features circuit (par exemple pour la course 1184, jouée à Sepang, circuit où peu de pilotes actuels ont couru).
- **Contrat du split** : découpage temporel, usage de 2025 et 2026.
