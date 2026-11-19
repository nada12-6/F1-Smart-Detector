import os
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False   # on utilisera HistGradientBoosting (équivalent de sklearn) à la place

# ---------------------------------------------------------------
# 1. CONFIG : à adapter
# ---------------------------------------------------------------
DATA_PATH = "data/processed/f1_model_dataset.csv"   # dataset final (tous les features mergés)
N_TEST_SEASONS = 2                                   # nombre de dernières saisons gardées pour le test

# Uniquement des infos connues AVANT la course. Ajoutez ici les features des autres membres.
FEATURES = [
    "qualifying_position",
    "driver_avg_position_last_5",
    "driver_top_3_rate_last_5",
]

# ---------------------------------------------------------------
# 2. CHARGEMENT ET CIBLE
# ---------------------------------------------------------------
df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["is_podium"] = np.where(df["position_order"] <= 3, 1, 0)   # la cible y

# ---------------------------------------------------------------
# 3. SPLIT CHRONOLOGIQUE : les dernières saisons servent de test
# ---------------------------------------------------------------
years = sorted(df["year"].unique())
test_years = years[-N_TEST_SEASONS:]
train = df[~df["year"].isin(test_years)].copy()
test = df[df["year"].isin(test_years)].copy()

X_train, y_train = train[FEATURES], train["is_podium"]
X_test, y_test = test[FEATURES], test["is_podium"]
print(f"Train: {len(train)} lignes ({years[0]}-{years[-N_TEST_SEASONS-1]}) | "
      f"Test: {len(test)} lignes ({test_years})")
print(f"Taux de podium: train={y_train.mean():.3f}, test={y_test.mean():.3f}")

# ---------------------------------------------------------------
# 4. LES MODÈLES À COMPARER (même données, même split)
# ---------------------------------------------------------------
spw = (y_train == 0).sum() / (y_train == 1).sum()   # compense le déséquilibre des classes

models = {
    "LogisticRegression": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000)),
    ]),
    "RandomForest": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf", RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=10,
                                       class_weight="balanced", random_state=42, n_jobs=-1)),
    ]),
}
if HAS_XGB:
    models["XGBoost"] = Pipeline([
        ("clf", XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                              subsample=0.8, colsample_bytree=0.8, scale_pos_weight=spw,
                              eval_metric="logloss", random_state=42)),
    ])
else:
    models["HistGradientBoosting"] = Pipeline([
        ("clf", HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300,
                                               class_weight="balanced", random_state=42)),
    ])

# ---------------------------------------------------------------
# 5. BASELINE NAÏF : prédire les 3 premiers de la grille de qualification
# ---------------------------------------------------------------
if "qualifying_position" in test.columns:
    base = test[["race_id", "is_podium"]].copy()
    base["rank"] = test.groupby("race_id")["qualifying_position"].rank(method="first")
    base_hits = base[base["rank"] <= 3].groupby("race_id")["is_podium"].sum()
    print(f"\nBaseline (3 premiers de la quali): top-3 hit rate = {base_hits.mean() / 3:.3f}")

# ---------------------------------------------------------------
# 6. ENTRAÎNEMENT ET ÉVALUATION
# ---------------------------------------------------------------
rows = []
for name, model in models.items():
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    # métrique métier : dans chaque course, on garde les 3 plus fortes probabilités
    tmp = test[["race_id", "is_podium"]].copy()
    tmp["proba"] = proba
    tmp["rank"] = tmp.groupby("race_id")["proba"].rank(ascending=False, method="first")
    hits = tmp[tmp["rank"] <= 3].groupby("race_id")["is_podium"].sum()

    rows.append({
        "model": name,
        "roc_auc": roc_auc_score(y_test, proba),
        "avg_precision": average_precision_score(y_test, proba),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "top3_hit_rate": hits.mean() / 3,        # part des 3 podiums trouvés en moyenne
        "exact_podium": (hits == 3).mean(),      # part des courses avec les 3 bons pilotes
    })

results = pd.DataFrame(rows).set_index("model").round(3)
print("\nRésultats sur le test:\n", results.sort_values("top3_hit_rate", ascending=False))

# ---------------------------------------------------------------
# 7. INTERPRÉTATION DE LA RÉGRESSION LOGISTIQUE
# ---------------------------------------------------------------
coefs = models["LogisticRegression"].named_steps["clf"].coef_[0]
print("\nCoefficients (logistique, variables standardisées):")
print(pd.Series(coefs, index=FEATURES).sort_values().round(3))

# ---------------------------------------------------------------
# 8. SAUVEGARDE DU MEILLEUR MODÈLE (choisi sur le top-3 par course)
# ---------------------------------------------------------------
best_name = results["top3_hit_rate"].idxmax()
os.makedirs("models", exist_ok=True)
joblib.dump({"model": models[best_name], "features": FEATURES}, "models/podium_model.joblib")
print(f"\nMeilleur modèle: {best_name} -> sauvegardé dans models/podium_model.joblib")
