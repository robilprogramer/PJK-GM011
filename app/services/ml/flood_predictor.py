"""
flood_predictor.py — SiagaAI ML Inference Service
===================================================
Loads trained Random Forest model dari disk dan melakukan:
  - Inference prediksi risiko banjir
  - Feature engineering yang sama persis saat training
  - Feature importance (SHAP-like dari model)
  - Auto-fallback: train ulang jika model belum ada
"""

import os
import json
import time
import numpy as np
import joblib
import structlog
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

logger = structlog.get_logger()

# ─── Feature definitions (HARUS sama dengan saat training) ───
FEATURE_NAMES = [
    "rainfall_1h",
    "rainfall_3h",
    "rainfall_24h",
    "humidity",
    "temperature",
    "wind_speed",
    "month",
    "is_rainy_season",
    "elevation_m",
    "distance_to_river_km",
    "soil_type_encoded",
    "rain_intensity",
    "rain_persistence",
    "saturation_index",
    "drainage_score",
    "heat_humidity",
    "city_risk",
]

CLASS_ORDER = ["aman", "waspada", "siaga", "awas"]

RISK_MESSAGES = {
    "aman":    "Kondisi cuaca normal. Tidak ada risiko banjir signifikan di lokasi ini.",
    "waspada": "Risiko banjir mulai meningkat. Pantau kondisi cuaca dan saluran air di sekitar Anda.",
    "siaga":   "Risiko banjir cukup tinggi. Bersiap untuk evakuasi jika kondisi terus memburuk.",
    "awas":    "⚠️ BAHAYA! Risiko banjir sangat tinggi. Segera evakuasi ke tempat yang lebih tinggi!",
}

RISK_ACTIONS = {
    "aman": [
        "Kondisi normal, tidak ada tindakan mendesak.",
        "Pantau prakiraan cuaca BMKG secara berkala.",
    ],
    "waspada": [
        "Pastikan saluran air dan drainase tidak tersumbat.",
        "Siapkan tas siaga bencana di tempat yang mudah dijangkau.",
        "Pantau ketinggian air sungai terdekat.",
    ],
    "siaga": [
        "Siapkan semua dokumen penting dalam tas kedap air.",
        "Identifikasi jalur evakuasi dan titik kumpul terdekat.",
        "Amankan barang berharga ke lantai atas.",
        "Matikan panel listrik jika air mulai masuk.",
    ],
    "awas": [
        "SEGERA evakuasi ke tempat lebih tinggi!",
        "Hubungi BNPB: 119 atau Darurat: 112.",
        "Jangan melewati genangan air yang mengalir deras.",
        "Matikan listrik dari panel MCB sekarang.",
        "Bawa hanya barang yang sangat penting.",
    ],
}

# ─── Soil type mapping (untuk lookup dari string) ─────────────
SOIL_TYPE_ENCODING = {
    "aluvial": 0,
    "gambut":  1,
    "latosol": 2,
    "andosol": 3,
    "regosol": 4,
}

# ─── Karakteristik kota default (fallback jika koordinat tidak dikenal) ──────
# Lookup berdasarkan nama kota (lowercase)
CITY_DEFAULTS = {
    "jakarta":      {"elevation_m": 8,   "distance_to_river_km": 1.5, "soil_type_encoded": 0, "flood_prone_score": 0.88},
    "bekasi":       {"elevation_m": 18,  "distance_to_river_km": 3.5, "soil_type_encoded": 0, "flood_prone_score": 0.78},
    "tangerang":    {"elevation_m": 10,  "distance_to_river_km": 2.0, "soil_type_encoded": 0, "flood_prone_score": 0.85},
    "depok":        {"elevation_m": 65,  "distance_to_river_km": 4.2, "soil_type_encoded": 2, "flood_prone_score": 0.60},
    "bogor":        {"elevation_m": 265, "distance_to_river_km": 2.8, "soil_type_encoded": 2, "flood_prone_score": 0.72},
    "bandung":      {"elevation_m": 768, "distance_to_river_km": 5.0, "soil_type_encoded": 3, "flood_prone_score": 0.45},
    "semarang":     {"elevation_m": 12,  "distance_to_river_km": 1.8, "soil_type_encoded": 0, "flood_prone_score": 0.88},
    "solo":         {"elevation_m": 92,  "distance_to_river_km": 1.2, "soil_type_encoded": 0, "flood_prone_score": 0.82},
    "yogyakarta":   {"elevation_m": 113, "distance_to_river_km": 2.0, "soil_type_encoded": 4, "flood_prone_score": 0.60},
    "surabaya":     {"elevation_m": 12,  "distance_to_river_km": 2.0, "soil_type_encoded": 0, "flood_prone_score": 0.78},
    "sidoarjo":     {"elevation_m": 6,   "distance_to_river_km": 1.8, "soil_type_encoded": 0, "flood_prone_score": 0.90},
    "medan":        {"elevation_m": 22,  "distance_to_river_km": 2.5, "soil_type_encoded": 0, "flood_prone_score": 0.85},
    "padang":       {"elevation_m": 8,   "distance_to_river_km": 1.5, "soil_type_encoded": 0, "flood_prone_score": 0.80},
    "palembang":    {"elevation_m": 8,   "distance_to_river_km": 1.2, "soil_type_encoded": 0, "flood_prone_score": 0.87},
    "banjarmasin":  {"elevation_m": 2,   "distance_to_river_km": 0.5, "soil_type_encoded": 1, "flood_prone_score": 0.95},
    "pontianak":    {"elevation_m": 2,   "distance_to_river_km": 0.8, "soil_type_encoded": 1, "flood_prone_score": 0.92},
    "makassar":     {"elevation_m": 8,   "distance_to_river_km": 2.0, "soil_type_encoded": 0, "flood_prone_score": 0.72},
    "pekanbaru":    {"elevation_m": 30,  "distance_to_river_km": 3.0, "soil_type_encoded": 1, "flood_prone_score": 0.75},
    "jambi":        {"elevation_m": 18,  "distance_to_river_km": 1.0, "soil_type_encoded": 0, "flood_prone_score": 0.85},
}
_DEFAULT_CITY = {"elevation_m": 25, "distance_to_river_km": 3.0, "soil_type_encoded": 0, "flood_prone_score": 0.65}


@dataclass
class PredictionResult:
    risk_level:     str
    risk_score:     float           # 0.0–1.0
    probabilities:  dict            # per kelas
    confidence:     str             # high / medium / low
    top_features:   list            # [{feature, importance, value}]
    message:        str
    actions:        list[str]
    model_version:  str
    inference_ms:   float           # waktu inference dalam ms


class FloodPredictor:
    """
    Service prediksi risiko banjir menggunakan Random Forest yang sudah ditraining.
    Thread-safe untuk FastAPI async environment.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self._model    = None
        self._scaler   = None
        self._le       = None
        self._metadata: dict = {}
        self._loaded   = False

    # ─── Load ───────────────────────────────────────────────────

    def ensure_loaded(self) -> None:
        """Load model dari disk. Auto-train jika belum ada."""
        if self._loaded:
            return

        model_path  = os.path.join(self.models_dir, "flood_risk_model.pkl")
        scaler_path = os.path.join(self.models_dir, "feature_scaler.pkl")
        enc_path    = os.path.join(self.models_dir, "label_encoder.pkl")
        meta_path   = os.path.join(self.models_dir, "model_metadata.json")

        if not os.path.exists(model_path):
            logger.warning("Model tidak ditemukan, menjalankan training otomatis...")
            self._auto_train()

        self._model  = joblib.load(model_path)
        self._scaler = joblib.load(scaler_path)
        self._le     = joblib.load(enc_path)

        if os.path.exists(meta_path):
            with open(meta_path) as f:
                self._metadata = json.load(f)

        self._loaded = True
        logger.info(
            "FloodPredictor loaded",
            version=self._metadata.get("model_version", "?"),
            accuracy=self._metadata.get("accuracy"),
            f1=self._metadata.get("f1_score_weighted"),
        )

    def _auto_train(self) -> None:
        """Jalankan pipeline training dari awal jika model belum ada."""
        import subprocess, sys
        scripts = [
            "scripts/01_build_dataset.py",
            "scripts/02_preprocess.py",
            "scripts/03_train.py",
        ]
        for script in scripts:
            if os.path.exists(script):
                logger.info(f"Auto-running {script}...")
                result = subprocess.run(
                    [sys.executable, script],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"Script failed: {script}", stderr=result.stderr[-500:])
                    break
            else:
                logger.warning(f"Script not found: {script}")

    # ─── Feature Engineering ───────────────────────────────────

    def _build_features(
        self,
        rainfall_1h:           float,
        rainfall_3h:           float,
        rainfall_24h:          float,
        humidity:              float,
        temperature:           float,
        wind_speed:            float,
        month:                 int,
        elevation_m:           float,
        distance_to_river_km:  float,
        soil_type_encoded:     int,
        flood_prone_score:     float,
    ) -> np.ndarray:
        """
        Membuat feature vector 17-dimensi yang identik dengan saat training.
        """
        is_rainy_season = 1 if month in [11, 12, 1, 2, 3] else 0

        # rain_intensity (0-4)
        if rainfall_1h == 0:      rain_intensity = 0
        elif rainfall_1h < 5:     rain_intensity = 1
        elif rainfall_1h < 20:    rain_intensity = 2
        elif rainfall_1h < 50:    rain_intensity = 3
        else:                     rain_intensity = 4

        # rain_persistence: rasio 3h/1h
        rain_persistence = (
            float(np.clip(rainfall_3h / (rainfall_1h + 0.1), 0, 10))
            if rainfall_1h > 0 else 0.0
        )

        # saturation_index
        saturation_index = rainfall_24h * humidity / 100.0

        # drainage_score
        soil_drain = {0: 0.2, 1: 0.1, 2: 0.6, 3: 0.9, 4: 0.7}
        max_elev = 1600.0  # normalisasi sama seperti training
        max_dist = 50.0
        drainage_score = (
            (elevation_m / max_elev) * 0.4
            + soil_drain.get(soil_type_encoded, 0.5) * 0.4
            + (distance_to_river_km / max_dist) * 0.2
        )

        # heat_humidity
        heat_humidity = temperature * humidity / 100.0

        # city_risk composite
        city_risk = (
            flood_prone_score * 0.6
            + (1 - elevation_m / max_elev) * 0.25
            + (1 - distance_to_river_km / max_dist) * 0.15
        )

        return np.array([[
            rainfall_1h,
            rainfall_3h,
            rainfall_24h,
            humidity,
            temperature,
            wind_speed,
            month,
            is_rainy_season,
            elevation_m,
            distance_to_river_km,
            soil_type_encoded,
            rain_intensity,
            rain_persistence,
            saturation_index,
            drainage_score,
            heat_humidity,
            city_risk,
        ]])

    def _get_city_defaults(self, city_name: str) -> dict:
        """Cari karakteristik geografis kota dari lookup table."""
        key = city_name.lower().strip()
        # Partial match
        for k, v in CITY_DEFAULTS.items():
            if k in key or key in k:
                return v
        return _DEFAULT_CITY

    # ─── Predict ───────────────────────────────────────────────

    def predict(
        self,
        rainfall_1h:          float,
        rainfall_3h:          float,
        rainfall_24h:         float,
        humidity:             float,
        temperature:          float,
        wind_speed:           float,
        month:                Optional[int] = None,
        city_name:            str = "",
        elevation_m:          Optional[float] = None,
        distance_to_river_km: Optional[float] = None,
        soil_type_encoded:    Optional[int] = None,
        flood_prone_score:    Optional[float] = None,
    ) -> PredictionResult:
        """
        Prediksi risiko banjir dari data cuaca.

        Args:
            rainfall_1h   : Curah hujan 1 jam terakhir (mm)
            rainfall_3h   : Curah hujan 3 jam terakhir (mm)
            rainfall_24h  : Curah hujan 24 jam terakhir (mm)
            humidity      : Kelembaban relatif (%)
            temperature   : Suhu (°C)
            wind_speed    : Kecepatan angin (m/s)
            month         : Bulan saat ini (1-12), default: bulan sekarang
            city_name     : Nama kota (untuk lookup karakteristik geografis)
            elevation_m   : Elevasi kota dalam meter (opsional, dari lookup)
            distance_to_river_km : Jarak ke sungai (opsional)
            soil_type_encoded    : Jenis tanah 0-4 (opsional)
            flood_prone_score    : Skor historis kerawanan kota (opsional)

        Returns:
            PredictionResult
        """
        self.ensure_loaded()

        t_start = time.perf_counter()

        # Gunakan bulan sekarang jika tidak diisi
        if month is None:
            month = datetime.now().month

        # Lookup karakteristik kota jika ada
        city_geo = self._get_city_defaults(city_name) if city_name else _DEFAULT_CITY
        elev   = elevation_m          if elevation_m          is not None else city_geo["elevation_m"]
        dist   = distance_to_river_km if distance_to_river_km is not None else city_geo["distance_to_river_km"]
        soil   = soil_type_encoded    if soil_type_encoded     is not None else city_geo["soil_type_encoded"]
        prone  = flood_prone_score    if flood_prone_score     is not None else city_geo["flood_prone_score"]

        # Cap nilai input (konsisten dengan preprocessing)
        rainfall_1h  = float(np.clip(rainfall_1h,  0, 303.3))
        rainfall_3h  = float(np.clip(rainfall_3h,  0, 653.6))
        rainfall_24h = float(np.clip(rainfall_24h, 0, 2047.5))
        wind_speed   = float(np.clip(wind_speed,   0, 30.0))
        humidity     = float(np.clip(humidity,      0, 100.0))

        # Build feature vector
        X_raw = self._build_features(
            rainfall_1h, rainfall_3h, rainfall_24h,
            humidity, temperature, wind_speed,
            month, elev, dist, soil, prone
        )

        # Scale
        X_scaled = self._scaler.transform(X_raw)

        # Predict
        pred_enc = self._model.predict(X_scaled)[0]
        proba    = self._model.predict_proba(X_scaled)[0]

        # Decode label — le.classes_ dari training: ['aman','awas','siaga','waspada']
        risk_level = self._le.inverse_transform([pred_enc])[0]

        # Probabilities per kelas
        classes    = self._le.classes_.tolist()
        prob_dict  = {c: round(float(p), 4) for c, p in zip(classes, proba)}

        # Risk score 0–1 berdasarkan weighted probability
        weights    = {"aman": 0.0, "waspada": 0.33, "siaga": 0.66, "awas": 1.0}
        risk_score = float(sum(weights.get(c, 0) * p for c, p in prob_dict.items()))

        # Confidence
        max_p      = float(proba.max())
        confidence = "high" if max_p >= 0.75 else "medium" if max_p >= 0.55 else "low"

        # Feature importance (dari model, bukan SHAP — lebih ringan)
        feat_vals  = X_raw[0].tolist()
        importances= self._model.feature_importances_.tolist()
        top_features = sorted(
            [
                {
                    "feature":    name,
                    "importance": round(float(imp), 5),
                    "value":      round(float(val), 3),
                    "direction":  "increase_risk"
                        if name in ["rainfall_1h","rainfall_3h","rainfall_24h",
                                    "humidity","saturation_index","city_risk","rain_intensity"]
                        else "decrease_risk"
                        if name in ["drainage_score","elevation_m","distance_to_river_km"]
                        else "context",
                }
                for name, imp, val in zip(FEATURE_NAMES, importances, feat_vals)
            ],
            key=lambda x: x["importance"],
            reverse=True,
        )[:7]

        t_end     = time.perf_counter()
        inf_ms    = round((t_end - t_start) * 1000, 2)

        return PredictionResult(
            risk_level    = risk_level,
            risk_score    = round(risk_score, 4),
            probabilities = prob_dict,
            confidence    = confidence,
            top_features  = top_features,
            message       = RISK_MESSAGES.get(risk_level, ""),
            actions       = RISK_ACTIONS.get(risk_level, []),
            model_version = self._metadata.get("model_version", "unknown"),
            inference_ms  = inf_ms,
        )

    def predict_from_weather(self, weather_data: dict, city_name: str = "") -> PredictionResult:
        """
        Shortcut: prediksi langsung dari dict data cuaca OWM/BMKG.
        weather_data harus memiliki key: temperature, humidity, rainfall_1h, wind_speed
        """
        r1   = float(weather_data.get("rainfall_1h", 0))
        r3   = r1 * float(weather_data.get("rain_persistence_factor", 2.5))
        r24  = r1 * float(weather_data.get("rain_24h_factor", 10.0))
        hum  = float(weather_data.get("humidity", 70))
        temp = float(weather_data.get("temperature", 27))
        wind = float(weather_data.get("wind_speed", 2))

        return self.predict(
            rainfall_1h  = r1,
            rainfall_3h  = r3,
            rainfall_24h = r24,
            humidity     = hum,
            temperature  = temp,
            wind_speed   = wind,
            city_name    = city_name,
        )

    def get_model_info(self) -> dict:
        """Informasi model yang sedang dipakai."""
        self.ensure_loaded()
        return {
            "model_type"              : self._metadata.get("model_type", "RandomForestClassifier"),
            "model_version"           : self._metadata.get("model_version", "unknown"),
            "trained_at"              : self._metadata.get("trained_at", ""),
            "accuracy"                : self._metadata.get("accuracy", 0),
            "f1_score_weighted"       : self._metadata.get("f1_score_weighted", 0),
            "f1_score_macro"          : self._metadata.get("f1_score_macro", 0),
            "roc_auc"                 : self._metadata.get("roc_auc"),
            "cv_f1_mean"              : self._metadata.get("cv_f1_mean"),
            "cv_f1_std"               : self._metadata.get("cv_f1_std"),
            "n_features"              : len(FEATURE_NAMES),
            "feature_names"           : FEATURE_NAMES,
            "class_names"             : CLASS_ORDER,
            "n_estimators"            : getattr(self._model, "n_estimators", None),
            "total_training_samples"  : self._metadata.get("n_train"),
            "per_class_metrics"       : self._metadata.get("per_class_metrics", {}),
            "top5_features"           : self._metadata.get("top5_features", []),
            "is_loaded"               : self._loaded,
        }


# ─── Singleton (load sekali, dipakai semua request) ───────────
flood_predictor = FloodPredictor(models_dir="models")
