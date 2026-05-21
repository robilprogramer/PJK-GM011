import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.exceptions import WeatherServiceError
from app.schemas.location import WeatherData
import structlog

logger = structlog.get_logger()


class OpenWeatherService:
    """Data cuaca real-time dari OpenWeatherMap API."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8), reraise=True)
    async def get_current_weather(self, lat: float, lng: float) -> WeatherData:
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                resp = await client.get(
                    f"{settings.OWM_BASE_URL}/weather",
                    params={
                        "lat": lat, "lon": lng,
                        "appid": settings.OWM_API_KEY,
                        "units": "metric",
                        "lang": "id",
                    },
                )
                resp.raise_for_status()
                d = resp.json()
                return WeatherData(
                    temperature=d["main"]["temp"],
                    humidity=d["main"]["humidity"],
                    condition=d["weather"][0]["description"],
                    icon=d["weather"][0]["icon"],
                    wind_speed=d["wind"]["speed"],
                    rainfall_1h=d.get("rain", {}).get("1h", 0.0),
                    city_name=d.get("name", ""),
                )
        except httpx.HTTPStatusError as e:
            raise WeatherServiceError(f"OWM error {e.response.status_code}")
        except Exception as e:
            raise WeatherServiceError(str(e))

    async def get_forecast(self, lat: float, lng: float) -> list[dict]:
        """Prakiraan cuaca 24 jam ke depan."""
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                resp = await client.get(
                    f"{settings.OWM_BASE_URL}/forecast",
                    params={
                        "lat": lat, "lon": lng,
                        "appid": settings.OWM_API_KEY,
                        # "units": "metric",
                        # "lang": "id",
                        # "cnt": 8,
                    },
                )
                resp.raise_for_status()
                return [
                    {
                        "time": item["dt_txt"],
                        "temperature": item["main"]["temp"],
                        "condition": item["weather"][0]["description"],
                        "rainfall_3h": item.get("rain", {}).get("3h", 0.0),
                        "humidity": item["main"]["humidity"],
                    }
                    for item in resp.json().get("list", [])
                ]
        except Exception as e:
            logger.warning("OWM forecast error", error=str(e))
            return []
