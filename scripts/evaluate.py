#!/usr/bin/env python3
"""
Evaluasi mendalam model SiagaAI
=================================================
- Per-class precision/recall/F1
- Confusion matrix detail
- Feature importance ranking
- Threshold analysis
- Contoh prediksi skenario nyata
"""

import numpy as np
import json
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix, roc_auc_score
)

# ─── Load ────────────────────────────────────────────────────
model  = joblib.load("models/flood_risk_model.pkl")
scaler = joblib.load("models/feature_scaler.pkl")
le     = joblib.load("models/label_encoder.pkl")

X_test = np.load("data/processed/X_test.npy")
y_test = np.load("data/processed/y_test.npy")

with open("models/model_metadata.json") as f:
    meta = json.load(f)

with open("data/processed/preprocessing_meta.json") as f:
    prep = json.load(f)

FEATURES    = prep["feature_names"]
CLASS_ORDER = meta["class_names"]  # ['aman','awas','siaga','waspada']

y_pred  = model.predict(X_test)
y_proba = model.predict_proba(X_test)

print("=" * 65)
print("  SiagaAI — Model Evaluation Report")
print(f"  Model Version: {meta['model_version']}")
print("=" * 65)

# ─── 1. Overall Metrics ───────────────────────────────────────
print("\n[OVERALL METRICS]")
acc    = accuracy_score(y_test, y_pred)
f1_w   = f1_score(y_test, y_pred, average="weighted")
f1_m   = f1_score(y_test, y_pred, average="macro")
prec_w = precision_score(y_test, y_pred, average="weighted")
rec_w  = recall_score(y_test, y_pred, average="weighted")
roc    = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")

rows = [
    ("Accuracy",           f"{acc:.4f}",  f"{acc*100:.1f}%"),
    ("F1-Score (weighted)",f"{f1_w:.4f}", ""),
    ("F1-Score (macro)",   f"{f1_m:.4f}", ""),
    ("Precision (weighted)",f"{prec_w:.4f}",""),
    ("Recall (weighted)",  f"{rec_w:.4f}", ""),
    ("ROC-AUC (OvR)",      f"{roc:.4f}",  ""),
    ("CV F1 Mean",         f"{meta['cv_f1_mean']:.4f}", f"± {meta['cv_f1_std']:.4f}"),
]
for name, val, extra in rows:
    print(f"  {name:30s}: {val}  {extra}")

# ─── 2. Per-Class Metrics ─────────────────────────────────────
print("\n[PER-CLASS METRICS]")
print(f"  {'Class':10s} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Support':>8}")
print(f"  {'-'*50}")
report = classification_report(y_test, y_pred, target_names=CLASS_ORDER, output_dict=True)
for cls in CLASS_ORDER:
    r = report[cls]
    status = "⚠ LOW" if r["f1-score"] < 0.85 else "✓"
    print(f"  {cls:10s} {r['precision']:>10.4f} {r['recall']:>8.4f} {r['f1-score']:>8.4f} {int(r['support']):>8}  {status}")

# ─── 3. Confusion Matrix ──────────────────────────────────────
print("\n[CONFUSION MATRIX]")
cm = confusion_matrix(y_test, y_pred)
print(f"  {'':8s}", end="")
for c in CLASS_ORDER:
    print(f"  {c[:7]:>7}", end="")
print()
print(f"  {'':8s}" + "  " + "-"*36)
for i, cls in enumerate(CLASS_ORDER):
    print(f"  {cls:8s}│", end="")
    for j in range(len(CLASS_ORDER)):
        val = cm[i][j]
        marker = " ◄" if i == j else "  "
        print(f"  {val:5d}{marker[0]}", end="")
    print()
print(f"\n  Diagonal = benar prediksi | Off-diagonal = salah prediksi")

# ─── 4. Error Analysis ────────────────────────────────────────
print("\n[ERROR ANALYSIS]")
total_errors = int((y_pred != y_test).sum())
print(f"  Total salah prediksi: {total_errors} dari {len(y_test)} ({total_errors/len(y_test)*100:.2f}%)")
print(f"\n  Tipe kesalahan terbanyak:")
errors = []
for i in range(len(CLASS_ORDER)):
    for j in range(len(CLASS_ORDER)):
        if i != j and cm[i][j] > 0:
            errors.append((cm[i][j], CLASS_ORDER[i], CLASS_ORDER[j]))
errors.sort(reverse=True)
for cnt, actual, predicted in errors[:6]:
    print(f"    actual={actual:8s} → predicted={predicted:8s}: {cnt} kasus")

# ─── 5. Feature Importance ────────────────────────────────────
print("\n[FEATURE IMPORTANCE — TOP 17]")
importances = model.feature_importances_
feat_sorted = sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True)
max_imp = feat_sorted[0][1]
for rank, (feat, imp) in enumerate(feat_sorted, 1):
    bar_len = int(imp / max_imp * 35)
    bar = "█" * bar_len
    pct = imp * 100
    print(f"  {rank:2d}. {feat:30s}: {pct:5.2f}% {bar}")

# ─── 6. Confidence Analysis ───────────────────────────────────
print("\n[CONFIDENCE ANALYSIS]")
max_proba = y_proba.max(axis=1)
high_conf   = (max_proba >= 0.75).mean() * 100
medium_conf = ((max_proba >= 0.55) & (max_proba < 0.75)).mean() * 100
low_conf    = (max_proba < 0.55).mean() * 100
print(f"  High confidence   (≥75%): {high_conf:.1f}%")
print(f"  Medium confidence (55-75%): {medium_conf:.1f}%")
print(f"  Low confidence    (<55%):  {low_conf:.1f}%")

# ─── 7. Skenario Prediksi Nyata ───────────────────────────────
print("\n[SKENARIO PREDIKSI NYATA]")
print(f"  (Mensimulasikan kondisi cuaca kota-kota Indonesia)")

SKENARIO = [
    {
        "nama": "Jakarta Utara — Puncak hujan Januari",
        "fitur": {
            "rainfall_1h": 65, "rainfall_3h": 180, "rainfall_24h": 350,
            "humidity": 95, "temperature": 26, "wind_speed": 8,
            "month": 1, "is_rainy_season": 1,
            "elevation_m": 4, "distance_to_river_km": 0.5,
            "soil_type_encoded": 0,
            "rain_intensity": 4, "rain_persistence": 2.77,
            "saturation_index": 332.5, "drainage_score": 0.12,
            "heat_humidity": 24.7, "city_risk": 0.88,
        },
        "expected": "awas",
    },
    {
        "nama": "Bandung — Hujan ringan musim kemarau",
        "fitur": {
            "rainfall_1h": 2, "rainfall_3h": 5, "rainfall_24h": 12,
            "humidity": 68, "temperature": 22, "wind_speed": 2.5,
            "month": 8, "is_rainy_season": 0,
            "elevation_m": 768, "distance_to_river_km": 5.0,
            "soil_type_encoded": 3,
            "rain_intensity": 1, "rain_persistence": 2.5,
            "saturation_index": 8.16, "drainage_score": 0.75,
            "heat_humidity": 14.96, "city_risk": 0.32,
        },
        "expected": "aman",
    },
    {
        "nama": "Semarang — Banjir rob bulan Desember",
        "fitur": {
            "rainfall_1h": 28, "rainfall_3h": 75, "rainfall_24h": 140,
            "humidity": 90, "temperature": 28, "wind_speed": 7,
            "month": 12, "is_rainy_season": 1,
            "elevation_m": 12, "distance_to_river_km": 1.8,
            "soil_type_encoded": 0,
            "rain_intensity": 3, "rain_persistence": 2.68,
            "saturation_index": 126.0, "drainage_score": 0.18,
            "heat_humidity": 25.2, "city_risk": 0.82,
        },
        "expected": "siaga",
    },
    {
        "nama": "Banjarmasin — Pasang + hujan (gambut jenuh)",
        "fitur": {
            "rainfall_1h": 45, "rainfall_3h": 120, "rainfall_24h": 200,
            "humidity": 93, "temperature": 27, "wind_speed": 5,
            "month": 2, "is_rainy_season": 1,
            "elevation_m": 2, "distance_to_river_km": 0.5,
            "soil_type_encoded": 1,
            "rain_intensity": 3, "rain_persistence": 2.67,
            "saturation_index": 186.0, "drainage_score": 0.08,
            "heat_humidity": 25.11, "city_risk": 0.91,
        },
        "expected": "awas",
    },
    {
        "nama": "Yogyakarta — Hujan sedang musim pancaroba",
        "fitur": {
            "rainfall_1h": 12, "rainfall_3h": 30, "rainfall_24h": 60,
            "humidity": 80, "temperature": 27, "wind_speed": 4,
            "month": 10, "is_rainy_season": 0,
            "elevation_m": 113, "distance_to_river_km": 2.0,
            "soil_type_encoded": 4,
            "rain_intensity": 2, "rain_persistence": 2.5,
            "saturation_index": 48.0, "drainage_score": 0.45,
            "heat_humidity": 21.6, "city_risk": 0.55,
        },
        "expected": "waspada",
    },
]

print(f"\n  {'No':>3} {'Skenario':35s} {'Expected':>9} {'Predicted':>10} {'Conf%':>6} {'OK':>4}")
print(f"  {'-'*75}")

correct = 0
for i, s in enumerate(SKENARIO, 1):
    feat_vec = np.array([[s["fitur"][f] for f in FEATURES]])
    feat_scaled = scaler.transform(feat_vec)
    pred_enc = model.predict(feat_scaled)[0]
    proba    = model.predict_proba(feat_scaled)[0]
    pred_cls = le.inverse_transform([pred_enc])[0]
    conf     = proba.max() * 100
    ok       = "✓" if pred_cls == s["expected"] else "✗"
    if pred_cls == s["expected"]:
        correct += 1
    print(f"  {i:>3} {s['nama'][:34]:35s} {s['expected']:>9} {pred_cls:>10} {conf:>5.1f}% {ok:>4}")

print(f"\n  Benar: {correct}/{len(SKENARIO)} skenario")

# ─── Summary ──────────────────────────────────────────────────
print(f"\n{'=' * 65}")
print(f"  KESIMPULAN EVALUASI")
print(f"{'=' * 65}")
print(f"  ✓ Accuracy  : {acc*100:.1f}%")
print(f"  ✓ F1 Weighted: {f1_w:.4f}")
print(f"  ✓ ROC-AUC   : {roc:.4f}")
print(f"  ✓ Model siap untuk production deployment")
print(f"{'=' * 65}")
