from pydantic import BaseModel, Field
from typing import Optional


class LocationInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    city: str = Field(..., min_length=1)
    province: str = Field(default="")
    display_name: str = Field(...)


class WeatherData(BaseModel):
    temperature: float
    humidity: int
    condition: str
    icon: Optional[str] = None
    wind_speed: float
    rainfall_1h: float = 0.0
    city_name: str = ""


class EarthquakeData(BaseModel):
    magnitude: Optional[str] = None
    depth: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    felt: Optional[str] = None
    summary: str = "Tidak ada aktivitas gempa signifikan"


class DisasterRisk(BaseModel):
    type: str               # banjir | longsor | gempa | angin_kencang
    level: str              # aman | waspada | siaga | awas
    description: str
    recommended_action: str


class LocationStatusResponse(BaseModel):
    location: LocationInput
    weather: WeatherData
    earthquake: EarthquakeData
    risks: list[DisasterRisk]
    overall_risk: str
    summary: str
    updated_at: str
