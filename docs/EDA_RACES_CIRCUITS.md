# EDA `races` et `circuits` : constats et décisions

**F1 Smart Predictor · Propriétaire : P4 · Relecteur : P3 · Version mise à jour (décisions tranchées)**

Ce document résume l'EDA des tables `races` (1 172 lignes, 18 colonnes) et `circuits` (78 lignes, 9 colonnes). Il suit le tableau de constats du bloc 0 : constat, chiffre, cause probable, traitement. Tout ce qui est marqué « non prouvé » est une hypothèse, pas un fait tiré des données.

**Ce qui change par rapport à la première version**

| Sujet | Avant | Maintenant |
|---|---|---|
| Ligne 1184 (« Bahrain Grand Prix in Malaysia », `circuit_id` 2) | Incohérence nom / circuit, non tranchée | Nom et circuit **officiels** d'après le calendrier officiel 2026 : course déplacée à Sepang. **Aucune correction** |
| Course 1184 : date passée, pas de résultat | Non expliquée | Course **jouée** (podium Verstappen, Antonelli, Hamilton), mais résultat absent du dataset, qui est **final** |
| « 8 courses à venir » | Les 8 courses sans résultat étaient dites « à venir » | 1 course jouée (1184) + **7 réellement à venir** (manches 17 à 23) |
| Décisions 1 à 8 | À trancher | **Tranchées** (voir section 4), sauf l'annonce à l'équipe (décision 4) |
| Scripts | À écrire | **Écrits et testés** : `clean_races.py`, `clean_circuits.py` |

---

## 1. Constats sur `races`

### Lecture, types, valeurs manquantes

| Constat | Chiffre | Cause | Traitement |
|---|---|---|---|
| `date` et `time` lues en texte | 2 colonnes | lecture par défaut de pandas | convertir `date` en vraie date (sans `errors="coerce"`) ; garder `time` en texte HH:MM:SS |
| Colonnes sans aucune valeur manquante | `raceId`, `year`, `round`, `circuitId`, `name`, `date`, `url` : 0 sur 1 172 | colonnes complètes | aucun traitement |
| `time` vide | 731 sur 1 172 (62,4 %) | toutes les courses d'avant 2005 (prouvé) ; complète de 2005 à 2026 | garder, renommer `start_time`, vides conservés |
| `fp1`, `fp2`, `fp3`, `quali` (date et heure, 8 colonnes) | 88,3 à 92,5 % de vides | dates renseignées dès 2021, heures dès 2022 (prouvé) ; cause côté source du dataset (probable) | **supprimer**, justification écrite |
| `fp3` absente alors que `fp1` est présente | 30 cas = les 30 week-ends sprint | format du weekend (prouvé) | couvert par la suppression de `fp3` |
| `sprint_date` / `sprint_time` | 30 / 27 valeurs présentes (97,4 % et 97,7 % de vides) | le vide signifie « pas de sprint » ; 3, 3, 6, 6, 6, 6 sprints de 2021 à 2026, 0 avant (prouvé) | créer la colonne booléenne `is_sprint_weekend`, puis supprimer les deux colonnes brutes |
| Fuseau de `time` non précisé | 441 valeurs présentes | non documenté dans la source | documenter, ne pas en faire une feature tant que non clarifié |

### Doublons, clé, ordre des courses

| Constat | Chiffre | Cause | Traitement |
|---|---|---|---|
| Doublons (clé, lignes exactes, (`year`, `round`), (`date`, circuit)) | 0 | table sans doublon | aucune ligne supprimée (1 172 en sortie) |
| `round` continu dans chaque saison | 0 saison avec trou (77 saisons) | numérotation propre | aucun traitement |
| Tri par (`year`, `round`) cohérent avec la date | date croissante : vrai | numérotation propre | construire `race_order` par ce tri |
| `race_id` ne suit pas l'ordre des courses | 61 reculs | ids attribués hors ordre du calendrier (non prouvé) | ne jamais trier ni comparer par `race_id` |
| Date incohérente avec `year` | 0 ; dates de 1950-05-13 à 2026-12-06 | la borne haute est une course à venir | conserver, ne pas filtrer par date |

### Textes et valeurs bizarres

| Constat | Chiffre | Cause | Traitement |
|---|---|---|---|
| `name` : espaces en trop, entités HTML, doubles espaces | 0 sur 1 172 ; 56 noms distincts | texte propre | renommer `race_name`, rien d'autre |
| Caractères non standard dans `name` | 2 noms (`São Paulo`, `BarcelonaCatalunya`) | accent et tiret légitimes | conserver |
| `Indianapolis 500`, `70th Anniversary Grand Prix` | 11 et 1 courses | noms de course qui ne sont pas des pays | conserver |
| « Bahrain Grand Prix in Malaysia » avec `circuit_id` = 2 (Sepang) | 1 ligne : `raceId` 1184, manche 16 de 2026 | **nom officiel** d'après le calendrier officiel 2026 : le Grand Prix de Bahreïn se court à Sepang cette année-là. Sepang n'avait plus servi depuis 2017 | **conserver tel quel, aucune correction** |
| Pic d'heure à 12:00:00 | 115 courses sur 441 | heure réelle partagée, ou valeur par défaut de la source (non tranché) | signaler, conserver, vérification optionnelle reportée |

### Courses sans résultat

| Constat | Chiffre | Cause | Traitement |
|---|---|---|---|
| Courses sans résultat | 8 (`raceId` 1184 à 1191, manches 16 à 23 de 2026) | dataset **final**, non mis à jour. La **1184 est déjà jouée** (2026-10-04, podium Verstappen, Antonelli, Hamilton d'après le calendrier officiel) mais son résultat n'est pas dans `results.csv`. Les **7 autres** (manches 17 à 23) sont à venir | `has_results = False`, calculé depuis `results` |
| Courses avec résultat | 1 164 ; dernière : 2026-09-26 | conforme à l'attendu | `has_results = True` |

---

## 2. Constats sur `circuits`

| Constat | Chiffre | Cause | Traitement |
|---|---|---|---|
| Valeurs manquantes | 0 sur 78 lignes, 9 colonnes | table complète | aucun traitement |
| Doublons (clé, référence, nom, lignes exactes) | 0 | table sans doublon | aucune ligne supprimée (78 en sortie) |
| Types | `lat`, `lng` en décimal ; `alt` en entier | lecture correcte | aucun traitement |
| Coordonnées hors bornes | 0 ; `lat` de -37,85 à 57,27 ; `lng` de -118,19 à 144,97 | coordonnées cohérentes | aucun traitement |
| Textes (4 colonnes) : espaces, entités HTML, doubles espaces | 0 | texte propre | aucun traitement |
| Accents et tirets dans `name` et `location` | présents, aucun dans `country` | orthographe d'origine | conserver |
| `circuit_ref` avec tiret | 1 valeur (`ain-diab`) | écriture d'origine ; le snake_case du bloc 4 concerne les noms de colonnes, pas les valeurs | conserver |
| `alt` ≤ 0 | 3 lignes : Baku -7, Korea 0, Miami 0 | circuits bas ou côtiers (non prouvé) ; une altitude de 0 ne se distingue pas d'une valeur par défaut | signaler, conserver |
| `alt` = 1 126 pour Jacarepaguá (Rio de Janeiro) | 1 ligne (`circuit_id` 36) ; circuit utilisé de 1978 à 1989 (10 courses) | valeur incohérente avec le lieu, erreur de source probable (non prouvé) ; hors période de modélisation | signaler, conserver |
| `country` : `USA` et `United States` | 11 et 1 (`circuit_id` 80, Las Vegas) | deux conventions d'écriture pour le même pays (non prouvé) | **harmoniser en `USA`** (1 ligne corrigée) |
| Unité de `alt` | maximum 2 227 (Mexico), puis Kyalami 1 460 | cohérent avec des mètres | aucun traitement |

---

## 3. Cohérence entre tables

| Vérification | Résultat |
|---|---|
| `circuit_id` de `races` absents de `circuits` | 0 |
| Circuits sans aucune course | 0 |
| Circuits utilisés en 2014 et après | 33 sur 78 (les 78 lignes restent : les features utilisent tout l'historique) |
| `race_id` de `results` absents de `races` | 0 |

---

## 4. Décisions (toutes tranchées)

### Décidées par P4

| # | Sujet | Décision | Appui |
|---|---|---|---|
| 1 | Nom de la colonne sprint | `is_sprint_weekend`, vrai quand `sprint_date` est renseignée (et non `sprint_time`, car les 3 sprints de 2021 n'ont pas d'heure) | contrat bloc 4, règle 6 |
| 2 | `United States` (circuit 80) | Harmoniser en `USA`, règle écrite et comptée (« 1 ligne corrigée »). `country` n'est dans aucune feature prévue : enjeu faible | recommandation de l'EDA ; exception documentée au bloc 4 |
| 3 | Pic de `12:00:00` | Vérification **reportée** ; ne bloque pas le script car `start_time` est seulement conservée et documentée | EDA |

### Décidées avec l'équipe (P1, P2, P3)

| # | Sujet | Décision |
|---|---|---|
| 4 | Création de la colonne sprint | Ajoutée au contrat (bloc 4, règle 7 ; contrôle au bloc 5). **Reste à annoncer à l'équipe** avant la livraison de `races_clean`. Savoir si elle sert de feature se décidera dans le contrat features |
| 5 | Ligne 1184 | **Aucune correction** : nom et circuit officiels (calendrier officiel 2026). À signaler à l'équipe comme cas particulier : les features `driver_circuit_*` et `constructor_circuit_*` de cette course s'appuieront sur l'historique de Sepang, où peu de pilotes actuels ont couru (valeurs souvent vides, non imputées au nettoyage) |
| 6 | Course 1184 : date passée, pas de résultat | **Expliqué** : course jouée, résultat absent du dataset final. Le script n'est pas bloqué : `has_results` vient de `results` |
| 7 | Altitudes suspectes ou nulles | **Signaler et conserver**. Aucune n'entre dans une feature prévue |
| 8 | Fuseau de `start_time` | Aucune feature construite sur cette colonne tant que le fuseau n'est pas clarifié |

### Déjà décidé

- Supprimer les 8 colonnes `fp1`, `fp2`, `fp3`, `quali` (date et heure), avec justification écrite.
- Créer la colonne sprint, puis supprimer `sprint_date` et `sprint_time`.
- Garder `time` (renommée `start_time`) avec ses 731 vides, sans imputation.
- Convertir `date` en vraie date, sans `errors="coerce"`.
- Aucune ligne supprimée, aucun filtre par année.

---

## 5. Ce que font les scripts de nettoyage

### `clean_races.py`

- Lire avec `na_values=r"\N"` (`races.csv` et `results.csv`).
- Renommer `raceId`, `circuitId`, `name`, `time` en `race_id`, `circuit_id`, `race_name`, `start_time`.
- Créer `is_sprint_weekend`, puis supprimer `sprint_date` et `sprint_time`.
- Supprimer `url` et les colonnes `fp*` et `quali_*`.
- Convertir `date` en vraie date.
- Créer `race_order` : tri explicite par (`year`, `round`), puis numérotation de 1 à 1 172, jamais par `race_id`.
- Créer `has_results` : vrai si le `race_id` figure dans `results.csv` brut (1 164 vrai, 8 faux).
- Aucun filtre par année. En sortie : 1 172 lignes.

### `clean_circuits.py`

- Lire avec `na_values=r"\N"`.
- Renommer `circuitId`, `circuitRef`, `name` en `circuit_id`, `circuit_ref`, `circuit_name`.
- Supprimer `url`.
- Harmoniser `country` (« United States » devient « USA », 1 ligne).
- Aucune ligne supprimée, aucun nettoyage de texte (0 cas trouvé). En sortie : 78 lignes.

---

## 6. Ce qu'il reste à vérifier

- Pic de `12:00:00` : répartition par année et par circuit (optionnel).
- `has_results` calculé avec le **vrai** `results.csv` : fait (confirmé par P4) ; attendu 1 164 vrai et 8 faux.
- Contrôles de sortie du bloc 5 : lignes en entrée et en sortie, `race_order` croissant avec la date, `has_results` vrai pour 1 164 courses et faux pour 8, (`year`, `round`) unique.
- Relecture croisée : `races` et `circuits` sont relues par P3.
