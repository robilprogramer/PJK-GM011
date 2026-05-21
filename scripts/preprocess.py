#!/usr/bin/env python3
"""
Data Preprocessing
==============================================
- Cleaning & capping outliers
- Feature engineering
- Label encoding
- Class balancing (SMOTE)
- Train / Val / Test split
Output: data/processed/
"""

import pandas as pd
import numpy as np
import json, os, warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.utils import resample
import joblib

# ─── Load Raw ────────────────────────────────────────────────
print("=" * 60)
print("  SiagaAI — Data Preprocessing Pipeline")
print("=" * 60)

df = pd.read_csv("data/raw/flood_indonesia_raw.csv")
print(f"\n[1] Data loaded: {len(df):,} baris, {df.shape[1]} kolom")

# ─── Step 1: Cleaning ─────────────────────────────────────────
print("\n[2] Cleaning...")

# Hapus duplikat
before = len(df)
df.drop_duplicates(inplace=True)
print(f"    Duplikat dihapus: {before - len(df)}")

# Capping outliers rainfall (cap di persentil 99.5)
for col in ["rainfall_1h", "rainfall_3h", "rainfall_24h"]:
    cap = df[col].quantile(0.995)
    n_capped = (df[col] > cap).sum()
    df[col] = df[col].clip(upper=cap)
    print(f"    {col}: capped {n_capped} outliers → max {cap:.1f}mm")

# Clip wind speed (max 30 m/s = kategori badai tropis)
df["wind_speed"] = df["wind_speed"].clip(upper=30)

# Memastikan tidak ada NaN
assert df.isnull().sum().sum() == 0, "Ada NaN di dataset!"
print(f"    Missing values: 0 ✓")
print(f"    Baris setelah cleaning: {len(df):,}")

# ─── Step 2: Feature Engineering ──────────────────────────────
print("\n[3] Feature Engineering...")

# 2a. Rainfall intensity category (ordinal encoding)
def rain_category(r1):
    if r1 == 0:   return 0  # tidak hujan
    elif r1 < 5:  return 1  # hujan ringan
    elif r1 < 20: return 2  # hujan sedang
    elif r1 < 50: return 3  # hujan lebat
    else:         return 4  # hujan sangat lebat

df["rain_intensity"] = df["rainfall_1h"].apply(rain_category)
print("    + rain_intensity (0-4)")

# 2b. Rainfall accumulation ratio (3h/1h — menunjukkan persistensi hujan)
df["rain_persistence"] = np.where(
    df["rainfall_1h"] > 0,
    (df["rainfall_3h"] / (df["rainfall_1h"] + 0.1)).clip(0, 10).round(2),
    0
)
print("    + rain_persistence (rasio 3h/1h)")

# 2c. Rainfall to saturation index (24h × kelembaban)
df["saturation_index"] = (df["rainfall_24h"] * df["humidity"] / 100).round(2)
print("    + saturation_index (rainfall_24h × humidity)")

# 2d. Effective drainage (kombinasi elevasi + soil + jarak sungai)
# Semakin tinggi → semakin susah banjir
soil_drain = {0: 0.2, 1: 0.1, 2: 0.6, 3: 0.9, 4: 0.7}  # aluvial/gambut buruk
df["drainage_score"] = (
    (df["elevation_m"] / df["elevation_m"].max()) * 0.4 +
    df["soil_type_encoded"].map(soil_drain) * 0.4 +
    (df["distance_to_river_km"] / df["distance_to_river_km"].max()) * 0.2
).round(4)
print("    + drainage_score (elevasi + soil + jarak sungai)")

# 2e. Season flag (biner: musim hujan vs kemarau)
df["is_rainy_season"] = (df["month"].isin([11, 12, 1, 2, 3])).astype(int)
print("    + is_rainy_season (1=hujan, 0=kemarau)")

# 2f. Heat index effect (suhu tinggi + kelembaban tinggi → evapotranspirasi rendah)
df["heat_humidity"] = (df["temperature"] * df["humidity"] / 100).round(2)
print("    + heat_humidity (suhu × kelembaban/100)")

# 2g. Flood risk composite dari karakteristik kota
df["city_risk"] = (
    df["flood_prone_score"] * 0.6 +
    (1 - df["elevation_m"] / df["elevation_m"].max()) * 0.25 +
    (1 - df["distance_to_river_km"] / df["distance_to_river_km"].max()) * 0.15
).round(4)
print("    + city_risk (composite dari karakteristik kota)")

print(f"    Total fitur tambahan: 7")

# ─── Step 3: Select Features ──────────────────────────────────
print("\n[4] Selecting features...")

FEATURES = [
    # Curah hujan (raw)
    "rainfall_1h",
    "rainfall_3h",
    "rainfall_24h",
    # Kondisi atmosfer
    "humidity",
    "temperature",
    "wind_speed",
    # Waktu
    "month",
    "is_rainy_season",
    # Karakteristik lokasi
    "elevation_m",
    "distance_to_river_km",
    "soil_type_encoded",
    # Engineered features
    "rain_intensity",
    "rain_persistence",
    "saturation_index",
    "drainage_score",
    "heat_humidity",
    "city_risk",
]
TARGET = "risk_level"

print(f"    Jumlah fitur: {len(FEATURES)}")
print(f"    Fitur: {FEATURES}")

X = df[FEATURES].copy()
y = df[TARGET].copy()

# ─── Step 4: Encode Labels ────────────────────────────────────
print("\n[5] Encoding labels...")

CLASS_ORDER = ["aman", "waspada", "siaga", "awas"]
le = LabelEncoder()
le.fit(CLASS_ORDER)
y_enc = le.transform(y)

print(f"    Mapping: {dict(zip(le.classes_, le.transform(le.classes_)))}")
print(f"    Distribusi sebelum balancing:")
for cls in CLASS_ORDER:
    cnt = (y == cls).sum()
    print(f"      {cls:10s}: {cnt:5d} ({cnt/len(y)*100:.1f}%)")

# ─── Step 5: Train/Val/Test Split SEBELUM balancing ──────────────────────────
# Penting: balancing HANYA di training set untuk mencegah data leakage
print("\n[6] Split dataset (70% train / 15% val / 15% test)...")

X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y_enc, test_size=0.15, stratify=y_enc, random_state=42
)
X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.15/0.85,
    stratify=y_trainval, random_state=42
)

print(f"    Train : {len(X_train):,}")
print(f"    Val   : {len(X_val):,}")
print(f"    Test  : {len(X_test):,}")

# ─── Step 6: Oversample TRAINING SET ─────────────────────────
# Manual oversampling (tanpa imbalanced-learn agar tidak perlu install)
print("\n[7] Balancing training set (oversampling kelas minoritas)...")

# Gabungkan train untuk oversampling
train_df = pd.DataFrame(X_train, columns=FEATURES)
train_df["__target__"] = y_train

max_count = train_df["__target__"].value_counts().max()
balanced_parts = []

for cls_idx in range(len(CLASS_ORDER)):
    cls_df = train_df[train_df["__target__"] == cls_idx]
    if len(cls_df) < max_count:
        cls_df = resample(cls_df, replace=True, n_samples=max_count, random_state=42)
    balanced_parts.append(cls_df)

balanced_train = pd.concat(balanced_parts).sample(frac=1, random_state=42).reset_index(drop=True)
X_train_bal = balanced_train[FEATURES].values
y_train_bal  = balanced_train["__target__"].values

print(f"    Training setelah balancing: {len(X_train_bal):,}")
for cls_idx, cls_name in enumerate(CLASS_ORDER):
    cnt = (y_train_bal == cls_idx).sum()
    print(f"      {cls_name:10s}: {cnt:5d}")

# ─── Step 7: Scaling ──────────────────────────────────────────
print("\n[8] Scaling features (StandardScaler)...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_bal)
X_val_scaled   = scaler.transform(X_val)
X_test_scaled  = scaler.transform(X_test)

# ─── Step 8: Simpan semua split ───────────────────────────────
print("\n[9] Saving processed data...")

os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)

np.save("data/processed/X_train.npy", X_train_scaled)
np.save("data/processed/y_train.npy", y_train_bal)
np.save("data/processed/X_val.npy",   X_val_scaled)
np.save("data/processed/y_val.npy",   y_val)
np.save("data/processed/X_test.npy",  X_test_scaled)
np.save("data/processed/y_test.npy",  y_test)

# Simpan scaler dan encoder
joblib.dump(scaler, "models/feature_scaler.pkl")
joblib.dump(le,     "models/label_encoder.pkl")

# Simpan metadata preprocessing
prep_meta = {
    "feature_names"        : FEATURES,
    "n_features"           : len(FEATURES),
    "target_column"        : TARGET,
    "class_order"          : CLASS_ORDER,
    "n_train_before_balance": int(len(X_train)),
    "n_train_after_balance" : int(len(X_train_bal)),
    "n_val"                : int(len(X_val)),
    "n_test"               : int(len(X_test)),
    "scaler"               : "StandardScaler",
    "balancing"            : "Oversampling (resample sklearn)",
    "engineered_features"  : [
        "rain_intensity", "rain_persistence", "saturation_index",
        "drainage_score", "is_rainy_season", "heat_humidity", "city_risk"
    ],
}

with open("data/processed/preprocessing_meta.json", "w") as f:
    json.dump(prep_meta, f, indent=2)

print("    ✓ data/processed/X_train.npy, y_train.npy")
print("    ✓ data/processed/X_val.npy, y_val.npy")
print("    ✓ data/processed/X_test.npy, y_test.npy")
print("    ✓ models/feature_scaler.pkl")
print("    ✓ models/label_encoder.pkl")
print("    ✓ data/processed/preprocessing_meta.json")
print("\n  Preprocessing SELESAI ✓")
print("=" * 60)
