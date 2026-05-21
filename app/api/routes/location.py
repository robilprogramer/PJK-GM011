import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_owm_service, get_bmkg_service, get_risk_analyzer, get_geocoder_service
from app.services.weather.openweather import OpenWeatherService
from app.services.weather.bmkg import BMKGService
from app.services.disaster.risk_analyzer import RiskAnalyzer
from app.services.location.geocoder import GeocoderService
from app.schemas.location import LocationInput, LocationStatusResponse, WeatherData, EarthquakeData
from app.schemas.common import SuccessResponse
from fastapi import HTTPException
import structlog

logger = structlog.get_logger()
router = APIRouter()

LEVEL_EMOJI = {"aman": "✅", "waspada": "⚠️", "siaga": "🔶", "awas": "🚨"}


@router.post(
    "/status",
    response_model=SuccessResponse[LocationStatusResponse],
    summary="Status cuaca & risiko bencana",
    description="Berikan koordinat GPS, dapatkan kondisi cuaca real-time + analisis risiko.",
)
async def get_location_status(
    location: LocationInput,
    owm: OpenWeatherService = Depends(get_owm_service),
    bmkg: BMKGService = Depends(get_bmkg_service),
    risk: RiskAnalyzer = Depends(get_risk_analyzer),
):
    weather_r, eq_r = await asyncio.gather(
        owm.get_current_weather(location.lat, location.lng),
        bmkg.get_latest_earthquake(),
        return_exceptions=True,
    )
    weather = None if isinstance(weather_r, Exception) else weather_r
    earthquake = None if isinstance(eq_r, Exception) else eq_r

    w = weather or WeatherData(temperature=0, humidity=0, condition="tidak tersedia", wind_speed=0, rainfall_1h=0)
    e = earthquake or EarthquakeData()
    risks, overall = risk.analyze(w, e)

    emoji = LEVEL_EMOJI.get(overall, "ℹ️")
    summary = (
        f"{emoji} {location.display_name}: {overall.upper()}. "
        f"Cuaca: {w.condition}. Suhu {w.temperature:.0f}°C, "
        f"Hujan {w.rainfall_1h:.1f} mm/jam."
    )

    return SuccessResponse(
        data=LocationStatusResponse(
            location=location, weather=w, earthquake=e,
            risks=risks, overall_risk=overall, summary=summary,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
    )


@router.get(
    "/geocode",
    response_model=SuccessResponse[LocationInput],
    summary="Nama kota → koordinat",
)
async def geocode_city(
    city: str = Query(..., min_length=2),
    geocoder: GeocoderService = Depends(get_geocoder_service),
):
    result = await geocoder.geocode_city(city)
    if not result:
        raise HTTPException(status_code=404, detail=f"Kota '{city}' tidak ditemukan")
    return SuccessResponse(data=result, message=f"Kota '{city}' ditemukan")


@router.get(
    "/reverse",
    response_model=SuccessResponse[LocationInput],
    summary="Koordinat → nama kota",
)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    geocoder: GeocoderService = Depends(get_geocoder_service),
):
    result = await geocoder.reverse_geocode(lat, lng)
    return SuccessResponse(data=result)


@router.get(
    "/earthquakes",
    response_model=SuccessResponse[list],
    summary="Daftar gempa terkini (BMKG)",
)
async def get_earthquakes(
    limit: int = Query(default=5, ge=1, le=15),
    bmkg: BMKGService = Depends(get_bmkg_service),
):
    data = await bmkg.get_recent_earthquakes(limit=limit)
    return SuccessResponse(data=data, message=f"{len(data)} gempa terkini dari BMKG")


@router.get(
    "/forecast",
    response_model=SuccessResponse[list],
    summary="Prakiraan cuaca 24 jam",
)
async def get_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    owm: OpenWeatherService = Depends(get_owm_service),
):
    data = await owm.get_forecast(lat, lng)
    return SuccessResponse(data=data)
