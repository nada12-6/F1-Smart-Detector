# F1 Smart Predictor — Notes de validation de `results.csv`

**Document de discussion pour l’équipe — audit en lecture seule, 11 novembre 2026**

## 1. Périmètre vérifié

- Fichier brut : `data/raw/results.csv` ; saison reliée depuis `races.csv` avec `raceId`.
- Le filtre étudié est **année ≥ 2014**. Il donne 5 457 lignes dans la copie actuelle.
- La copie contient des résultats 2026 seulement jusqu’au round 16 : 2026 est donc une saison partielle dans ce fichier.
- Les données brutes et le notebook EDA n’ont pas été modifiés. Les chiffres ci-dessous sont des vérifications, pas un nettoyage déjà appliqué.

## 2. Constats, signification et choix à discuter

| Sujet | Constat vérifié | Signification | Choix proposé à l’équipe |
|---|---|---|---|
| Doublons `(raceId, driverId)` | 85 clés répétées sur toute l’histoire ; **0 à partir de 2014**. | Les répétitions historiques viennent notamment d’anciens cas de partage de voiture. Dans cet échantillon récent, chaque pilote n’a qu’une ligne par course. | Refaire le contrôle après nettoyage et conserver une vérification d’unicité. Ne pas supprimer les lignes historiques automatiquement. |
| Valeurs manquantes | Depuis 2014 : `milliseconds` 2 557 (46,86 %), `fastestLap` 274 (5,02 %), `rank` 57 (1,04 %), `fastestLapSpeed` 1 048 (19,20 %), `position` 721 (13,21 %). | Le filtre réduit plusieurs manquants, mais `milliseconds` reste souvent absent. Les absences dépendent du champ et de l’issue de la course ; elles ne signifient pas toutes la même chose. | Garder les valeurs manquantes et les analyser par statut avant toute imputation ou suppression. La note « presque 100 % rempli » ne correspond pas à `milliseconds` dans ce fichier. |
| `grid = 0` | 79 lignes depuis 2014 : **72 ont au moins un tour**, 7 ont zéro tour. Pour ces 7, `positionText` vaut `W` dans 6 cas et `R` dans 1 cas ; `position` est manquante. Le statut détaillé varie (retrait, moteur, batterie, freins, système carburant). La convention Ergast indique `grid = 0` pour un départ depuis la pit lane. | Pour les 7 cas, on sait qu’aucun tour n’est enregistré et que le résultat porte le code « withdrew » ou « retired ». On ne peut pas déduire uniquement de ces champs si la voiture a quitté la voie des stands ou s’est immobilisée avant de boucler un tour. | Garder ces lignes dans la table nettoyée et conserver `grid = 0`. Pour un modèle limité aux pilotes ayant participé à la course, exclure ces 7 lignes du jeu d’entraînement avec une règle explicite (`laps = 0` et `positionText` W/R), puis vérifier les autres cas au besoin. Ne pas remplacer zéro par le nombre de partants. |
| `rank = 0` | 217 lignes depuis 2014 ; dans ces 217 lignes, `fastestLap`, `fastestLapTime` et `fastestLapSpeed` sont absents. | Zéro sert ici de code sans rang de meilleur tour renseigné, pas de véritable rang. `rank` est une donnée connue après la course. | Dans la table nettoyée, convertir `rank = 0` en valeur manquante et documenter la règle. Ne jamais utiliser le `rank` de la course à prédire comme variable d’entrée. |
| `position` | 721 valeurs manquantes depuis 2014. | Classement officiel numérique lorsqu’il est disponible ; les pilotes non classés peuvent avoir un code texte séparé dans `positionText`. | Conserver les deux colonnes pour audit. Examiner les cas particuliers avant d’écarter l’une d’elles du jeu final. |
| `positionText` | Valeurs numériques en texte et codes tels que `R`, `F`, `W`, `N`, `D`, `E`. | Texte de classement ou code de statut : Retired, Failed to qualify, Withdrew, Not classified, Disqualified, Excluded. `N` signifie non classé ; son critère exact peut dépendre des règles de l’époque. | Préserver les valeurs brutes. Ne pas fusionner les codes sans besoin défini et vérification de leur sens. |
| `positionOrder` | Pas de valeur manquante dans le fichier ; utilisé dans l’EDA pour créer `Top 3 = positionOrder <= 3`. | Ordre final de résultat, y compris les pilotes non classés ordonnés après les classés. C’est un résultat post-course. | Peut servir à créer la cible Top 3 ; ne pas l’utiliser comme variable d’entrée pour prédire cette même course. Confirmer que la cible est bien le podium parmi les partants. |

## 3. Règles sportives à retenir pour l’analyse

- Le barème Top 10 actuel est 25–18–15–12–10–8–6–4–2–1. En 2014, Abu Dhabi attribuait des points doublés, ce qui explique le maximum de 50 observé dans l’EDA.
- Le point du meilleur tour a été réintroduit en 2019, sous condition de finir dans le Top 10, puis supprimé à partir de 2025. Il ne faut donc pas interpréter `points` de la même façon pour toutes les saisons. [F1 : règle du point du meilleur tour](https://www.formula1.com/en/latest/article/bonus-point-to-be-awarded-for-fastest-lap-in-2019.4gwBT6QW1NR1AlrlzAkKSP.html) · [Suppression en 2025](https://www.formula1.com/en/latest/article/fastest-lap-point-to-be-scrapped-in-2025-after-latest-fia-world-motor-sport.4pUjDzWnGRN7KVWENLc1BY)
- 2022 et 2026 sont des changements réglementaires importants ; la FIA décrit les nouvelles règles 2026 comme un changement majeur. Les performances passées peuvent donc devenir moins représentatives après une nouvelle réglementation. [FIA : règles 2026](https://www.fia.com/news/new-era-competition-fia-showcases-future-focused-formula-1-regulations-2026-and-beyond)

## 4. Précautions pour le modèle

- Pour prédire avant la course, exclure les résultats de la course prédite : `position`, `positionOrder`, `points`, `laps`, `time`, `milliseconds`, `fastestLap`, `rank`, `statusId`, etc. Ils peuvent servir à construire la cible ou des historiques antérieurs, pas comme informations déjà connues.
- Calculer toute forme récente sur les courses précédentes uniquement : trier chronologiquement et décaler les agrégats (`shift`) avant de les rattacher à la course prédite. Fenêtre de 3 à 5 courses : **proposition à valider**, pas décision acquise.
- Ne pas normaliser `results.milliseconds` par le meilleur temps comme s’il s’agissait d’un temps de qualification. Le champ de résultat n’est pas automatiquement une mesure de rythme comparable.
- Préférer une validation chronologique (saisons futures en test) à un découpage aléatoire. Décider si 2026 partiel est inclus dans l’entraînement ou réservé à une analyse séparée.

### Sources de définition des champs

- [Guide de la base Ergast — convention `grid = 0`](https://ru.scribd.com/document/729031114/f1db-user-guide)
- [Jolpica/Ergast — champs des résultats de course](https://github.com/jolpica/jolpica-f1/blob/main/docs/endpoints/results.md)
- [Implémentation compatible Ergast — rang zéro converti en absence de rang](https://deepwiki.com/jolpica/jolpica-f1/5.1-ergast-api%3A-compatibility-and-design)
