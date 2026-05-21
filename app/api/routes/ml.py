"""
ML Endpoints — SiagaAI
======================
POST /api/ml/predict        — prediksi dengan input manual
POST /api/ml/predict-auto   — prediksi dari cuaca (nama kota + basic weather)
GET  /api/ml/model-info     — info model yang loaded
GET  /api/ml/health         — cek model sudah loaded atau belum
POST /api/ml/batch          — prediksi batch (banyak lokasi sekaligus)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.services.ml.flood_predictor import flood_predictor
from app.schemas.ml import (
    FloodPredictRequest,
    FloodPredictFromWeatherRequest,
    FloodPredictResponse,
    MLModelInfoResponse,
    FeatureImportanceItem,
)

import structlog
logger = structlog.get_logger()

router = APIRouter()


def _result_to_response(result) -> FloodPredictResponse:
    """Convert PredictionResult dataclass → FloodPredictResponse."""
    return FloodPredictResponse(
        risk_level    = result.risk_level,
        risk_score    = result.risk_score,
        probabilities = result.probabilities,
        confidence    = result.confidence,
        top_features  = [
            FeatureImportanceItem(**f) for f in result.top_features
        ],
        message       = result.message,
        actions       = result.actions,
        model_version = result.model_version,
        inference_ms  = result.inference_ms,
    )


# ─── POST /api/ml/predict ─────────────────────────────────────
@router.post(
    "/predict",
    response_model=FloodPredictResponse,
    summary="Prediksi risiko banjir",
    description=(
        "Prediksi level risiko banjir menggunakan Random Forest yang dilatih "
        "dari data historis 47 kota Indonesia (18.800 sampel). "
        "Input: data cuaca real-time. Output: risk_level + probabilitas + feature importance."
    ),
    tags=["ML Model"],
)
async def predict_flood(body: FloodPredictRequest):
    try:
        result = flood_predictor.predict(
            rainfall_1h           = body.rainfall_1h,
            rainfall_3h           = body.rainfall_3h,
            rainfall_24h          = body.rainfall_24h,
            humidity              = body.humidity,
            temperature           = body.temperature,
            wind_speed            = body.wind_speed,
            month                 = body.month,
            city_name             = body.city_name or "",
            elevation_m           = body.elevation_m,
            distance_to_river_km  = body.distance_to_river_km,
            soil_type_encoded     = body.soil_type_encoded,
            flood_prone_score     = body.flood_prone_score,
        )
        logger.info(
            "ML predict",
            city=body.city_name,
            risk=result.risk_level,
            confidence=result.confidence,
            ms=result.inference_ms,
        )
        return _result_to_response(result)

    except Exception as e:
        logger.error("ML predict error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediksi gagal: {str(e)}")


# ─── POST /api/ml/predict-auto ────────────────────────────────
@router.post(
    "/predict-auto",
    response_model=FloodPredictResponse,
    summary="Prediksi otomatis dari data cuaca dasar",
    description=(
        "Prediksi cepat dengan input minimal: nama kota + suhu + kelembaban + hujan. "
        "Karakteristik geografis kota diambil dari lookup table internal (47 kota utama). "
        "Cocok untuk integrasi dengan OpenWeatherMap API."
    ),
    tags=["ML Model"],
)
async def predict_auto(body: FloodPredictFromWeatherRequest):
    try:
        weather_dict = {
            "temperature":              body.temperature,
            "humidity":                 body.humidity,
            "rainfall_1h":              body.rainfall_1h,
            "wind_speed":               body.wind_speed,
            "rain_persistence_factor":  2.5,
            "rain_24h_factor":          10.0,
        }
        result = flood_predictor.predict_from_weather(weather_dict, city_name=body.city_name)
        logger.info("ML predict-auto", city=body.city_name, risk=result.risk_level)
        return _result_to_response(result)

    except Exception as e:
        logger.error("ML predict-auto error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediksi gagal: {str(e)}")


# ─── POST /api/ml/batch ───────────────────────────────────────
class BatchItem(BaseModel):
    city_name:    str
    rainfall_1h:  float
    rainfall_3h:  float
    rainfall_24h: float
    humidity:     float
    temperature:  float
    wind_speed:   float
    month:        Optional[int] = None

class BatchRequest(BaseModel):
    locations: list[BatchItem]

class BatchResponseItem(BaseModel):
    city_name:    str
    risk_level:   str
    risk_score:   float
    confidence:   str
    message:      str
    inference_ms: float

@router.post(
    "/batch",
    response_model=list[BatchResponseItem],
    summary="Prediksi batch banyak lokasi sekaligus",
    description="Jalankan prediksi untuk beberapa kota dalam satu request. Maks 20 lokasi.",
    tags=["ML Model"],
)
async def predict_batch(body: BatchRequest):
    if len(body.locations) > 20:
        raise HTTPException(status_code=400, detail="Maksimal 20 lokasi per batch request")

    results = []
    for loc in body.locations:
        try:
            result = flood_predictor.predict(
                rainfall_1h  = loc.rainfall_1h,
                rainfall_3h  = loc.rainfall_3h,
                rainfall_24h = loc.rainfall_24h,
                humidity     = loc.humidity,
                temperature  = loc.temperature,
                wind_speed   = loc.wind_speed,
                month        = loc.month,
                city_name    = loc.city_name,
            )
            results.append(BatchResponseItem(
                city_name    = loc.city_name,
                risk_level   = result.risk_level,
                risk_score   = result.risk_score,
                confidence   = result.confidence,
                message      = result.message,
                inference_ms = result.inference_ms,
            ))
        except Exception as e:
            results.append(BatchResponseItem(
                city_name    = loc.city_name,
                risk_level   = "unknown",
                risk_score   = 0.0,
                confidence   = "low",
                message      = f"Error: {str(e)}",
                inference_ms = 0.0,
            ))
    return results


# ─── GET /api/ml/model-info ───────────────────────────────────
@router.get(
    "/model-info",
    response_model=MLModelInfoResponse,
    summary="Info model ML yang sedang digunakan",
    description="Menampilkan metadata model: versi, akurasi, F1-score, daftar fitur, dll.",
    tags=["ML Model"],
)
async def get_model_info():
    try:
        info = flood_predictor.get_model_info()
        return MLModelInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /api/ml/health ───────────────────────────────────────
@router.get(
    "/health",
    summary="Cek status ML model",
    tags=["ML Model"],
)
async def ml_health():
    try:
        flood_predictor.ensure_loaded()
        meta = flood_predictor._metadata
        return {
            "status":        "loaded",
            "model_version": meta.get("model_version"),
            "accuracy":      meta.get("accuracy"),
            "f1_score":      meta.get("f1_score_weighted"),
            "is_ready":      flood_predictor._loaded,
        }
    except Exception as e:
        return {
            "status":   "error",
            "is_ready": False,
            "detail":   str(e),
        }
