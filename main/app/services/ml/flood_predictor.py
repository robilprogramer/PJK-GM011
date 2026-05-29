"""
flood_predictor.py — SiagaAI ML Inference Service
===================================================
Load trained Random Forest model dari folder models/
(model dihasilkan dari project 03_SiagaAI_ML_Pipeline)

CARA PAKAI:
  1. Copy hasil training dari ML Pipeline:
       models/flood_risk_model.pkl
       models/feature_scaler.pkl
       models/label_encoder.pkl
       models/model_metadata.json
  2. Jalankan backend → model auto-load saat startup
"""

import os
import json
import time
import numpy as np
import joblib
import structlog
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

logger = structlog.get_logger()

# ─── Konstanta (harus identik dengan saat training) ───────────
FEATURE_NAMES = [
    "rainfall_1h", "rainfall_3h", "rainfall_24h",
    "humidity", "temperature", "wind_speed",
    "month", "is_rainy_season",
    "elevation_m", "distance_to_river_km", "soil_type_encoded",
    "rain_intensity", "rain_persistence", "saturation_index",
    "drainage_score", "heat_humidity", "city_risk",
]

CLASS_ORDER = ["aman", "waspada", "siaga", "awas"]

RISK_MESSAGES = {
    "aman":    "Kondisi cuaca normal. Tidak ada risiko banjir signifikan.",
    "waspada": "Risiko banjir mulai meningkat. Pantau kondisi cuaca secara berkala.",
    "siaga":   "Risiko banjir cukup tinggi. Bersiap evakuasi jika kondisi memburuk.",
    "awas":    "⚠️ BAHAYA! Risiko banjir sangat tinggi. Segera evakuasi!",
}

RISK_ACTIONS = {
    "aman":    ["Kondisi normal, tidak ada tindakan mendesak.", "Pantau prakiraan cuaca BMKG."],
    "waspada": ["Pastikan saluran drainase tidak tersumbat.", "Siapkan tas siaga bencana.", "Pantau ketinggian air sungai."],
    "siaga":   ["Siapkan dokumen penting dalam tas kedap air.", "Identifikasi jalur evakuasi terdekat.", "Amankan barang berharga ke lantai atas.", "Matikan panel listrik jika air mulai masuk."],
    "awas":    ["SEGERA evakuasi ke tempat lebih tinggi!", "Hubungi BNPB: 119 atau Darurat: 112.", "Jangan melewati genangan air deras.", "Matikan listrik dari MCB sekarang.", "Bawa hanya barang yang sangat penting."],
}

# Karakteristik geografis 47 kota utama Indonesia
CITY_DEFAULTS = {
    "jakarta":     {"elevation_m": 8,   "distance_to_river_km": 1.5, "soil_type_encoded": 0, "flood_prone_score": 0.88},
    "bekasi":      {"elevation_m": 18,  "distance_to_river_km": 3.5, "soil_type_encoded": 0, "flood_prone_score": 0.78},
    "tangerang":   {"elevation_m": 10,  "distance_to_river_km": 2.0, "soil_type_encoded": 0, "flood_prone_score": 0.85},
    "depok":       {"elevation_m": 65,  "distance_to_river_km": 4.2, "soil_type_encoded": 2, "flood_prone_score": 0.60},
    "bogor":       {"elevation_m": 265, "distance_to_river_km": 2.8, "soil_type_encoded": 2, "flood_prone_score": 0.72},
    "bandung":     {"elevation_m": 768, "distance_to_river_km": 5.0, "soil_type_encoded": 3, "flood_prone_score": 0.45},
    "semarang":    {"elevation_m": 12,  "distance_to_river_km": 1.8, "soil_type_encoded": 0, "flood_prone_score": 0.88},
    "solo":        {"elevation_m": 92,  "distance_to_river_km": 1.2, "soil_type_encoded": 0, "flood_prone_score": 0.82},
    "yogyakarta":  {"elevation_m": 113, "distance_to_river_km": 2.0, "soil_type_encoded": 4, "flood_prone_score": 0.60},
    "surabaya":    {"elevation_m": 12,  "distance_to_river_km": 2.0, "soil_type_encoded": 0, "flood_prone_score": 0.78},
    "sidoarjo":    {"elevation_m": 6,   "distance_to_river_km": 1.8, "soil_type_encoded": 0, "flood_prone_score": 0.90},
    "medan":       {"elevation_m": 22,  "distance_to_river_km": 2.5, "soil_type_encoded": 0, "flood_prone_score": 0.85},
    "padang":      {"elevation_m": 8,   "distance_to_river_km": 1.5, "soil_type_encoded": 0, "flood_prone_score": 0.80},
    "palembang":   {"elevation_m": 8,   "distance_to_river_km": 1.2, "soil_type_encoded": 0, "flood_prone_score": 0.87},
    "banjarmasin": {"elevation_m": 2,   "distance_to_river_km": 0.5, "soil_type_encoded": 1, "flood_prone_score": 0.95},
    "pontianak":   {"elevation_m": 2,   "distance_to_river_km": 0.8, "soil_type_encoded": 1, "flood_prone_score": 0.92},
    "makassar":    {"elevation_m": 8,   "distance_to_river_km": 2.0, "soil_type_encoded": 0, "flood_prone_score": 0.72},
    "pekanbaru":   {"elevation_m": 30,  "distance_to_river_km": 3.0, "soil_type_encoded": 1, "flood_prone_score": 0.75},
    "jambi":       {"elevation_m": 18,  "distance_to_river_km": 1.0, "soil_type_encoded": 0, "flood_prone_score": 0.85},
    "samarinda":   {"elevation_m": 12,  "distance_to_river_km": 1.5, "soil_type_encoded": 0, "flood_prone_score": 0.80},
    "manado":      {"elevation_m": 35,  "distance_to_river_km": 2.5, "soil_type_encoded": 0, "flood_prone_score": 0.68},
}
_DEFAULT_GEO = {"elevation_m": 25, "distance_to_river_km": 3.0, "soil_type_encoded": 0, "flood_prone_score": 0.65}


@dataclass
class PredictionResult:
    risk_level:    str
    risk_score:    float
    probabilities: dict
    confidence:    str
    top_features:  list
    message:       str
    actions:       list
    model_version: str
    inference_ms:  float


class FloodPredictor:
    """
    Load trained model dari models/ dan jalankan inference.
    Model ditraining terpisah di project ML Pipeline.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self._model    = None
        self._scaler   = None
        self._le       = None
        self._metadata: dict = {}
        self._loaded   = False

    def ensure_loaded(self) -> None:
        """Load model dari disk. Raise error jika file tidak ada."""
        if self._loaded:
            return

        model_path  = os.path.join(self.models_dir, "flood_risk_model.pkl")
        scaler_path = os.path.join(self.models_dir, "feature_scaler.pkl")
        enc_path    = os.path.join(self.models_dir, "label_encoder.pkl")
        meta_path   = os.path.join(self.models_dir, "model_metadata.json")

        # Validasi semua file ada
        missing = [p for p in [model_path, scaler_path, enc_path, meta_path]
                   if not os.path.exists(p)]
        if missing:
            raise FileNotFoundError(
                f"Model files tidak ditemukan: {missing}\n"
                f"Copy hasil training dari project ML Pipeline ke folder: {self.models_dir}/"
            )

        self._model  = joblib.load(model_path)
        self._scaler = joblib.load(scaler_path)
        self._le     = joblib.load(enc_path)

        with open(meta_path) as f:
            self._metadata = json.load(f)

        self._loaded = True
        logger.info(
            "FloodPredictor loaded",
            version=self._metadata.get("model_version"),
            accuracy=self._metadata.get("accuracy"),
            f1=self._metadata.get("f1_score_weighted"),
        )

    # ─── Feature Engineering (identik dengan training) ────────
    def _build_features(
        self, rainfall_1h, rainfall_3h, rainfall_24h,
        humidity, temperature, wind_speed, month,
        elevation_m, distance_to_river_km, soil_type_encoded, flood_prone_score
    ) -> np.ndarray:

        is_rainy = 1 if month in [11, 12, 1, 2, 3] else 0

        if rainfall_1h == 0:      rain_intensity = 0
        elif rainfall_1h < 5:     rain_intensity = 1
        elif rainfall_1h < 20:    rain_intensity = 2
        elif rainfall_1h < 50:    rain_intensity = 3
        else:                     rain_intensity = 4

        rain_persistence = (
            float(np.clip(rainfall_3h / (rainfall_1h + 0.1), 0, 10))
            if rainfall_1h > 0 else 0.0
        )
        saturation_index = rainfall_24h * humidity / 100.0

        soil_drain = {0: 0.2, 1: 0.1, 2: 0.6, 3: 0.9, 4: 0.7}
        drainage_score = (
            (elevation_m / 1600.0) * 0.4
            + soil_drain.get(soil_type_encoded, 0.5) * 0.4
            + (distance_to_river_km / 50.0) * 0.2
        )

        heat_humidity = temperature * humidity / 100.0
        city_risk = (
            flood_prone_score * 0.6
            + (1 - elevation_m / 1600.0) * 0.25
            + (1 - distance_to_river_km / 50.0) * 0.15
        )

        return np.array([[
            rainfall_1h, rainfall_3h, rainfall_24h,
            humidity, temperature, wind_speed,
            month, is_rainy,
            elevation_m, distance_to_river_km, soil_type_encoded,
            rain_intensity, rain_persistence, saturation_index,
            drainage_score, heat_humidity, city_risk,
        ]])

    def _get_city_geo(self, city_name: str) -> dict:
        key = city_name.lower().strip()
        for k, v in CITY_DEFAULTS.items():
            if k in key or key in k:
                return v
        return _DEFAULT_GEO

    # ─── Predict ──────────────────────────────────────────────
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
        self.ensure_loaded()
        t0 = time.perf_counter()

        if month is None:
            month = datetime.now().month

        # Lookup geo dari nama kota jika parameter tidak di-override
        geo = self._get_city_geo(city_name) if city_name else _DEFAULT_GEO
        elev  = elevation_m          if elevation_m          is not None else geo["elevation_m"]
        dist  = distance_to_river_km if distance_to_river_km is not None else geo["distance_to_river_km"]
        soil  = soil_type_encoded    if soil_type_encoded     is not None else geo["soil_type_encoded"]
        prone = flood_prone_score    if flood_prone_score     is not None else geo["flood_prone_score"]

        # Cap nilai sesuai training
        rainfall_1h  = float(np.clip(rainfall_1h,  0, 303.3))
        rainfall_3h  = float(np.clip(rainfall_3h,  0, 653.6))
        rainfall_24h = float(np.clip(rainfall_24h, 0, 2047.5))
        wind_speed   = float(np.clip(wind_speed,   0, 30.0))
        humidity     = float(np.clip(humidity,      0, 100.0))

        X_raw    = self._build_features(rainfall_1h, rainfall_3h, rainfall_24h,
                                        humidity, temperature, wind_speed, month,
                                        elev, dist, soil, prone)
        X_scaled = self._scaler.transform(X_raw)

        pred_enc = self._model.predict(X_scaled)[0]
        proba    = self._model.predict_proba(X_scaled)[0]
        risk     = self._le.inverse_transform([pred_enc])[0]

        classes   = self._le.classes_.tolist()
        prob_dict = {c: round(float(p), 4) for c, p in zip(classes, proba)}

        weights    = {"aman": 0.0, "waspada": 0.33, "siaga": 0.66, "awas": 1.0}
        risk_score = float(sum(weights.get(c, 0) * p for c, p in prob_dict.items()))

        max_p      = float(proba.max())
        confidence = "high" if max_p >= 0.75 else "medium" if max_p >= 0.55 else "low"

        importances = self._model.feature_importances_.tolist()
        top_features = sorted(
            [{"feature": n, "importance": round(float(i), 5),
              "value": round(float(v), 3),
              "direction": "increase_risk"
                  if n in ["rainfall_1h","rainfall_3h","rainfall_24h","humidity","saturation_index","city_risk","rain_intensity"]
                  else "decrease_risk"
                  if n in ["drainage_score","elevation_m","distance_to_river_km"]
                  else "context"}
             for n, i, v in zip(FEATURE_NAMES, importances, X_raw[0].tolist())],
            key=lambda x: x["importance"], reverse=True
        )[:7]

        return PredictionResult(
            risk_level    = risk,
            risk_score    = round(risk_score, 4),
            probabilities = prob_dict,
            confidence    = confidence,
            top_features  = top_features,
            message       = RISK_MESSAGES.get(risk, ""),
            actions       = RISK_ACTIONS.get(risk, []),
            model_version = self._metadata.get("model_version", "unknown"),
            inference_ms  = round((time.perf_counter() - t0) * 1000, 2),
        )

    def predict_from_weather(self, weather: dict, city_name: str = "") -> PredictionResult:
        """Shortcut dari dict cuaca OWM/BMKG."""
        r1 = float(weather.get("rainfall_1h", 0))
        return self.predict(
            rainfall_1h  = r1,
            rainfall_3h  = r1 * float(weather.get("rain_persistence_factor", 2.5)),
            rainfall_24h = r1 * float(weather.get("rain_24h_factor", 10.0)),
            humidity     = float(weather.get("humidity", 70)),
            temperature  = float(weather.get("temperature", 27)),
            wind_speed   = float(weather.get("wind_speed", 2)),
            city_name    = city_name,
        )

    def get_model_info(self) -> dict:
        self.ensure_loaded()
        return {
            "model_type"             : self._metadata.get("model_type", "RandomForestClassifier"),
            "model_version"          : self._metadata.get("model_version", "unknown"),
            "trained_at"             : self._metadata.get("trained_at", ""),
            "accuracy"               : self._metadata.get("accuracy", 0),
            "f1_score_weighted"      : self._metadata.get("f1_score_weighted", 0),
            "f1_score_macro"         : self._metadata.get("f1_score_macro", 0),
            "roc_auc"                : self._metadata.get("roc_auc"),
            "cv_f1_mean"             : self._metadata.get("cv_f1_mean"),
            "n_features"             : len(FEATURE_NAMES),
            "feature_names"          : FEATURE_NAMES,
            "class_names"            : CLASS_ORDER,
            "n_estimators"           : getattr(self._model, "n_estimators", None),
            "total_training_samples" : self._metadata.get("n_train"),
            "per_class_metrics"      : self._metadata.get("per_class_metrics", {}),
            "top5_features"          : self._metadata.get("top5_features", []),
            "is_loaded"              : self._loaded,
        }


# Singleton
flood_predictor = FloodPredictor(models_dir="models")
