from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.services.ml.flood_predictor import flood_predictor
from app.services.weather.openweather import OpenWeatherService
from app.schemas.ml import (
    FloodPredictRequest, FloodPredictResponse,
    MLModelInfoResponse, FeatureImportanceItem,
)
from app.schemas.location import LocationInput
from app.api.deps import get_owm_service
import structlog

logger = structlog.get_logger()
router = APIRouter()


def _to_response(result) -> FloodPredictResponse:
    return FloodPredictResponse(
        risk_level    = result.risk_level,
        risk_score    = result.risk_score,
        probabilities = result.probabilities,
        confidence    = result.confidence,
        top_features  = [FeatureImportanceItem(**f) for f in result.top_features],
        message       = result.message,
        actions       = result.actions,
        model_version = result.model_version,
        inference_ms  = result.inference_ms,
    )


# ─── POST /api/ml/predict ─────────────────────────────────────
@router.post("/predict", response_model=FloodPredictResponse,
    summary="Prediksi risiko banjir (input manual)")
async def predict_flood(body: FloodPredictRequest):
    try:
        result = flood_predictor.predict(
            rainfall_1h           = body.rainfall_1h,
            rainfall_3h           = body.rainfall_3h,
            rainfall_24h          = body.rainfall_24h,
            humidity              = body.humidity,
            temperature           = body.temperature,
            wind_speed            = body.wind_speed,
            month                 = body.month or datetime.now().month,
            city_name             = body.city_name or "",
            elevation_m           = body.elevation_m,
            distance_to_river_km  = body.distance_to_river_km,
            soil_type_encoded     = body.soil_type_encoded,
            flood_prone_score     = body.flood_prone_score,
        )
        logger.info("ML predict", city=body.city_name, risk=result.risk_level)
        return _to_response(result)
    except Exception as e:
        logger.error("ML predict error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /api/ml/predict-auto ────────────────────────────────
# Alur: terima lokasi → fetch cuaca real-time OWM → ML predictor
@router.post("/predict-auto", response_model=FloodPredictResponse,
    summary="Prediksi otomatis — fetch cuaca OWM lalu ML inference")
async def predict_auto(
    location: LocationInput,
    owm: OpenWeatherService = Depends(get_owm_service),
):
    try:
        # 1. Fetch cuaca real-time dari OWM
        weather = await owm.get_current_weather(location.lat, location.lng)

        # 2. Estimasi rainfall_3h & rainfall_24h dari rainfall_1h
        r1  = weather.rainfall_1h
        r3  = r1 * 2.5    # estimasi konservatif 3 jam
        r24 = r1 * 10.0   # estimasi konservatif 24 jam

        # 3. ML inference dengan data cuaca real-time
        result = flood_predictor.predict(
            rainfall_1h  = r1,
            rainfall_3h  = r3,
            rainfall_24h = r24,
            humidity     = weather.humidity,
            temperature  = weather.temperature,
            wind_speed   = weather.wind_speed,
            city_name    = location.city,
        )

        logger.info(
            "ML predict-auto",
            city     = location.city,
            rain_1h  = r1,
            humidity = weather.humidity,
            risk     = result.risk_level,
        )
        return _to_response(result)

    except Exception as e:
        logger.error("ML predict-auto error", city=location.city, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /api/ml/batch ───────────────────────────────────────
class BatchItem(BaseModel):
    city_name:    str
    rainfall_1h:  float = Field(default=0)
    rainfall_3h:  float = Field(default=0)
    rainfall_24h: float = Field(default=0)
    humidity:     float = Field(default=70)
    temperature:  float = Field(default=27)
    wind_speed:   float = Field(default=2)
    month:        Optional[int] = None

class BatchRequest(BaseModel):
    locations: list[BatchItem]

class BatchItem_Out(BaseModel):
    city_name:    str
    risk_level:   str
    risk_score:   float
    confidence:   str
    message:      str
    inference_ms: float

@router.post("/batch", response_model=list[BatchItem_Out],
    summary="Prediksi batch (maks 20 lokasi)")
async def predict_batch(body: BatchRequest):
    if len(body.locations) > 20:
        raise HTTPException(status_code=400, detail="Maks 20 lokasi per request")
    results = []
    for loc in body.locations:
        try:
            r = flood_predictor.predict(
                rainfall_1h=loc.rainfall_1h, rainfall_3h=loc.rainfall_3h,
                rainfall_24h=loc.rainfall_24h, humidity=loc.humidity,
                temperature=loc.temperature, wind_speed=loc.wind_speed,
                month=loc.month, city_name=loc.city_name,
            )
            results.append(BatchItem_Out(
                city_name=loc.city_name, risk_level=r.risk_level,
                risk_score=r.risk_score, confidence=r.confidence,
                message=r.message, inference_ms=r.inference_ms,
            ))
        except Exception as e:
            results.append(BatchItem_Out(
                city_name=loc.city_name, risk_level="unknown",
                risk_score=0, confidence="low",
                message=str(e), inference_ms=0,
            ))
    return results


# ─── GET /api/ml/model-info ───────────────────────────────────
@router.get("/model-info", response_model=MLModelInfoResponse,
    summary="Info Custom ML Model")
async def get_model_info():
    try:
        return MLModelInfoResponse(**flood_predictor.get_model_info())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /api/ml/health ───────────────────────────────────────
@router.get("/health", summary="Status ML Model")
async def ml_health():
    try:
        flood_predictor.ensure_loaded()
        m = flood_predictor._metadata
        return {
            "status":        "loaded",
            "model_version": m.get("model_version"),
            "accuracy":      m.get("accuracy"),
            "f1_score":      m.get("f1_score_weighted"),
            "is_ready":      True,
        }
    except Exception as e:
        return {"status": "error", "is_ready": False, "detail": str(e)}
