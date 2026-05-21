from pydantic import BaseModel, Field
from typing import Optional


# ─── Request ──────────────────────────────────────────────────
class FloodPredictRequest(BaseModel):
    """Input data cuaca untuk prediksi risiko banjir."""

    # Wajib: data cuaca real-time
    rainfall_1h:  float = Field(..., ge=0, le=500,  description="Curah hujan 1 jam terakhir (mm)")
    rainfall_3h:  float = Field(..., ge=0, le=1500, description="Curah hujan 3 jam terakhir (mm)")
    rainfall_24h: float = Field(..., ge=0, le=3000, description="Curah hujan 24 jam terakhir (mm)")
    humidity:     float = Field(..., ge=0, le=100,  description="Kelembaban relatif (%)")
    temperature:  float = Field(..., ge=15, le=45,  description="Suhu udara (°C)")
    wind_speed:   float = Field(..., ge=0, le=50,   description="Kecepatan angin (m/s)")

    # Opsional: konteks lokasi
    city_name:    str   = Field(default="",         description="Nama kota (untuk lookup karakteristik geo)")
    month:        Optional[int] = Field(default=None, ge=1, le=12, description="Bulan (1-12), default: sekarang")

    # Override geo (jika tidak pakai lookup)
    elevation_m:           Optional[float] = Field(default=None, ge=0,   description="Elevasi kota (meter)")
    distance_to_river_km:  Optional[float] = Field(default=None, ge=0,   description="Jarak ke sungai (km)")
    soil_type_encoded:     Optional[int]   = Field(default=None, ge=0, le=4, description="Jenis tanah: 0=aluvial,1=gambut,2=latosol,3=andosol,4=regosol")
    flood_prone_score:     Optional[float] = Field(default=None, ge=0, le=1, description="Skor historis kerawanan (0-1)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "rainfall_1h":  25.5,
                "rainfall_3h":  68.0,
                "rainfall_24h": 142.0,
                "humidity":     92,
                "temperature":  26.5,
                "wind_speed":   6.2,
                "city_name":    "Jakarta Utara",
                "month":        1,
            }
        }
    }


class FloodPredictFromWeatherRequest(BaseModel):
    """Prediksi otomatis dari dict cuaca OWM/BMKG."""
    city_name:   str   = Field(...,  description="Nama kota")
    temperature: float = Field(...,  description="Suhu (°C)")
    humidity:    float = Field(...,  description="Kelembaban (%)")
    rainfall_1h: float = Field(default=0.0, description="Curah hujan 1h (mm)")
    wind_speed:  float = Field(default=2.0, description="Angin (m/s)")
    lat:         Optional[float] = None
    lng:         Optional[float] = None


# ─── Response ─────────────────────────────────────────────────
class FeatureImportanceItem(BaseModel):
    feature:    str
    importance: float
    value:      float
    direction:  str   # increase_risk | decrease_risk | context


class FloodPredictResponse(BaseModel):
    risk_level:    str   = Field(..., description="aman | waspada | siaga | awas")
    risk_score:    float = Field(..., description="Skor risiko 0.0–1.0")
    probabilities: dict  = Field(..., description="Probabilitas per kelas")
    confidence:    str   = Field(..., description="high | medium | low")
    top_features:  list[FeatureImportanceItem]
    message:       str
    actions:       list[str]
    model_version: str
    inference_ms:  float = Field(..., description="Waktu inference dalam ms")


class MLModelInfoResponse(BaseModel):
    model_type:               str
    model_version:            str
    trained_at:               str
    accuracy:                 float
    f1_score_weighted:        float
    f1_score_macro:           float
    roc_auc:                  Optional[float]
    cv_f1_mean:               Optional[float]
    cv_f1_std:                Optional[float]
    n_features:               int
    feature_names:            list[str]
    class_names:              list[str]
    n_estimators:             Optional[int]
    total_training_samples:   Optional[int]
    per_class_metrics:        dict
    top5_features:            list[str]
    is_loaded:                bool
