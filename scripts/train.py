#!/usr/bin/env python3
"""
SiagaAI Model Training
=====================================
- Train Random Forest Classifier
- Hyperparameter tuning (GridSearchCV)
- Evaluasi lengkap: accuracy, F1, classification report, confusion matrix
- Simpan model + metadata + feature importance
"""

import numpy as np
import json
import os
import time
import warnings
warnings.filterwarnings("ignore")

from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, roc_auc_score
)
from sklearn.model_selection import cross_val_score
import joblib

# ─── Load data ───────────────────────────────────────────────
print("=" * 60)
print("  SiagaAI — Model Training")
print("=" * 60)

X_train = np.load("data/processed/X_train.npy")
y_train = np.load("data/processed/y_train.npy")
X_val   = np.load("data/processed/X_val.npy")
y_val   = np.load("data/processed/y_val.npy")
X_test  = np.load("data/processed/X_test.npy")
y_test  = np.load("data/processed/y_test.npy")

le = joblib.load("models/label_encoder.pkl")
CLASS_ORDER = le.classes_.tolist()

with open("data/processed/preprocessing_meta.json") as f:
    prep_meta = json.load(f)
FEATURES = prep_meta["feature_names"]

print(f"\n  Train : {X_train.shape[0]:,} × {X_train.shape[1]}")
print(f"  Val   : {X_val.shape[0]:,}")
print(f"  Test  : {X_test.shape[0]:,}")
print(f"  Kelas : {CLASS_ORDER}")

# ─── Step 1: Baseline model ───────────────────────────────────
print("\n[1] Training baseline Random Forest...")
t0 = time.time()

rf_base = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1,
)
rf_base.fit(X_train, y_train)

val_acc_base = accuracy_score(y_val, rf_base.predict(X_val))
val_f1_base  = f1_score(y_val, rf_base.predict(X_val), average="weighted")
print(f"  Baseline — Val Acc: {val_acc_base:.4f} | Val F1: {val_f1_base:.4f} ({time.time()-t0:.1f}s)")

# ─── Step 2: Grid search over key hyperparameters ─────────────
print("\n[2] Hyperparameter search...")

# Manual grid (lebih cepat dari GridSearchCV, kita compare 6 config)
configs = [
    {"n_estimators": 200, "max_depth": 15, "min_samples_split": 4, "min_samples_leaf": 2, "max_features": "sqrt"},
    {"n_estimators": 200, "max_depth": 20, "min_samples_split": 4, "min_samples_leaf": 2, "max_features": "sqrt"},
    {"n_estimators": 300, "max_depth": 20, "min_samples_split": 3, "min_samples_leaf": 1, "max_features": "sqrt"},
    {"n_estimators": 300, "max_depth": 25, "min_samples_split": 3, "min_samples_leaf": 1, "max_features": 0.7},
    {"n_estimators": 200, "max_depth": None,"min_samples_split": 5, "min_samples_leaf": 2, "max_features": "sqrt"},
    {"n_estimators": 300, "max_depth": 20, "min_samples_split": 4, "min_samples_leaf": 2, "max_features": 0.6},
]

best_f1   = 0
best_cfg  = None
best_model= None

for i, cfg in enumerate(configs):
    t = time.time()
    m = RandomForestClassifier(**cfg, class_weight="balanced", n_jobs=-1, random_state=42)
    m.fit(X_train, y_train)
    vp  = m.predict(X_val)
    acc = accuracy_score(y_val, vp)
    f1  = f1_score(y_val, vp, average="weighted")
    elapsed = time.time() - t
    tag = " ← BEST" if f1 > best_f1 else ""
    print(f"  Config {i+1}: n_est={cfg['n_estimators']} depth={cfg['max_depth']} → Acc={acc:.4f} F1={f1:.4f} ({elapsed:.1f}s){tag}")
    if f1 > best_f1:
        best_f1   = f1
        best_cfg  = cfg
        best_model= m

print(f"\n  Best config: {best_cfg}")
print(f"  Best Val F1: {best_f1:.4f}")

# ─── Step 3: Final evaluation on TEST set ─────────────────────
print("\n[3] Final evaluation on TEST set...")

y_pred  = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)

test_acc = accuracy_score(y_test, y_pred)
test_f1  = f1_score(y_test, y_pred, average="weighted")
test_f1_macro = f1_score(y_test, y_pred, average="macro")

# ROC-AUC (one-vs-rest)
try:
    roc_auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
except Exception:
    roc_auc = None

print(f"\n  ┌─────────────────────────────────────────────┐")
print(f"  │         FINAL TEST SET METRICS               │")
print(f"  ├─────────────────────────────────────────────┤")
print(f"  │  Accuracy          : {test_acc:.4f} ({test_acc*100:.1f}%)         │")
print(f"  │  F1-Score Weighted : {test_f1:.4f}                    │")
print(f"  │  F1-Score Macro    : {test_f1_macro:.4f}                    │")
if roc_auc:
    print(f"  │  ROC-AUC (OvR)     : {roc_auc:.4f}                    │")
print(f"  └─────────────────────────────────────────────┘")

# Per-class report
print(f"\n  Classification Report:")
report = classification_report(y_test, y_pred, target_names=CLASS_ORDER, digits=4)
print("  " + report.replace("\n", "\n  "))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print(f"  Confusion Matrix (rows=actual, cols=predicted):")
print(f"  Classes: {CLASS_ORDER}")
header = "       " + "  ".join(f"{c[:6]:>6}" for c in CLASS_ORDER)
print(f"  {header}")
for i, row_cls in enumerate(CLASS_ORDER):
    row_str = "  ".join(f"{v:6d}" for v in cm[i])
    print(f"  {row_cls[:6]:>6} │ {row_str}")

# ─── Step 4: Cross-validation ─────────────────────────────────
print(f"\n[4] Cross-validation (5-fold, F1 weighted)...")
cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring="f1_weighted", n_jobs=-1)
print(f"  CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"  Folds: {[f'{s:.4f}' for s in cv_scores]}")

# ─── Step 5: Feature Importance ───────────────────────────────
print(f"\n[5] Feature Importance (top 10):")
importances = best_model.feature_importances_
feat_imp = sorted(
    zip(FEATURES, importances),
    key=lambda x: x[1],
    reverse=True
)
for rank, (feat, imp) in enumerate(feat_imp[:10], 1):
    bar = "█" * int(imp * 200)
    print(f"  {rank:2d}. {feat:30s}: {imp:.4f} {bar}")

# ─── Step 6: Simpan Model ─────────────────────────────────────
print(f"\n[6] Saving model...")
os.makedirs("models", exist_ok=True)

version = datetime.now().strftime("%Y%m%d_%H%M")
joblib.dump(best_model, "models/flood_risk_model.pkl")

# Simpan metadata lengkap
report_dict = classification_report(
    y_test, y_pred, target_names=CLASS_ORDER, output_dict=True
)

metadata = {
    "model_type"              : "RandomForestClassifier",
    "model_version"           : version,
    "trained_at"              : datetime.now().isoformat(),
    "framework"               : "scikit-learn",

    # Hyperparameters
    "hyperparameters"         : {**best_cfg, "class_weight": "balanced", "random_state": 42},

    # Metrics
    "accuracy"                : round(float(test_acc), 4),
    "f1_score_weighted"       : round(float(test_f1), 4),
    "f1_score_macro"          : round(float(test_f1_macro), 4),
    "roc_auc"                 : round(float(roc_auc), 4) if roc_auc else None,
    "cv_f1_mean"              : round(float(cv_scores.mean()), 4),
    "cv_f1_std"               : round(float(cv_scores.std()), 4),

    # Per-class
    "per_class_metrics"       : {
        cls: {
            "precision": round(report_dict[cls]["precision"], 4),
            "recall"   : round(report_dict[cls]["recall"],    4),
            "f1"       : round(report_dict[cls]["f1-score"],  4),
            "support"  : int(report_dict[cls]["support"]),
        }
        for cls in CLASS_ORDER
    },

    # Data
    "n_train"                 : int(X_train.shape[0]),
    "n_val"                   : int(X_val.shape[0]),
    "n_test"                  : int(X_test.shape[0]),
    "n_cities"                : 47,
    "n_features"              : len(FEATURES),
    "feature_names"           : FEATURES,

    # Feature importance
    "feature_importances"     : {feat: round(float(imp), 6) for feat, imp in feat_imp},
    "top5_features"           : [feat for feat, _ in feat_imp[:5]],

    # Confusion matrix
    "confusion_matrix"        : cm.tolist(),
    "class_names"             : CLASS_ORDER,

    # Files
    "model_file"              : "models/flood_risk_model.pkl",
    "scaler_file"             : "models/feature_scaler.pkl",
    "encoder_file"            : "models/label_encoder.pkl",
}

with open("models/model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"    ✓ models/flood_risk_model.pkl")
print(f"    ✓ models/model_metadata.json  (version: {version})")

# ─── Summary ──────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  TRAINING SELESAI")
print(f"{'=' * 60}")
print(f"  Model  : Random Forest ({best_cfg['n_estimators']} trees)")
roc_str = f"{roc_auc:.4f}" if roc_auc else "N/A"
print(f"  Accuracy: {test_acc*100:.1f}%   F1: {test_f1:.4f}   ROC-AUC: {roc_str}")
print(f"  Version: {version}")
print(f"{'=' * 60}")
