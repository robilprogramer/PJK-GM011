import httpx
from app.core.config import settings
from app.schemas.location import LocationInput
import structlog

logger = structlog.get_logger()
NOMINATIM = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "SiagaAI/1.0 (disaster-preparedness-app)"}


class GeocoderService:
    """Reverse geocoding dan geocoding menggunakan Nominatim (gratis)."""

    async def reverse_geocode(self, lat: float, lng: float) -> LocationInput:
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT, headers=HEADERS) as client:
                resp = await client.get(
                    f"{NOMINATIM}/reverse",
                    params={"lat": lat, "lon": lng, "format": "json"},
                )
                resp.raise_for_status()
                addr = resp.json().get("address", {})
                city = (
                    addr.get("city") or addr.get("town") or
                    addr.get("village") or addr.get("county") or "Tidak diketahui"
                )
                province = addr.get("state", "")
                return LocationInput(
                    lat=lat, lng=lng, city=city, province=province,
                    display_name=f"{city}, {province}".strip(", "),
                )
        except Exception as e:
            logger.warning("Reverse geocode failed", error=str(e))
            return LocationInput(
                lat=lat, lng=lng,
                city=f"{lat:.4f},{lng:.4f}", province="",
                display_name=f"Koordinat: {lat:.4f}, {lng:.4f}",
            )

    async def geocode_city(self, city_name: str) -> LocationInput | None:
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT, headers=HEADERS) as client:
                resp = await client.get(
                    f"{NOMINATIM}/search",
                    params={"q": f"{city_name}, Indonesia", "format": "json", "limit": 1},
                )
                resp.raise_for_status()
                results = resp.json()
                if not results:
                    return None
                r = results[0]
                parts = r.get("display_name", "").split(", ")
                return LocationInput(
                    lat=float(r["lat"]), lng=float(r["lon"]),
                    city=parts[0] if parts else city_name,
                    province=parts[1] if len(parts) > 1 else "",
                    display_name=f"{parts[0]}, {parts[1]}".strip(", ") if len(parts) > 1 else parts[0],
                )
        except Exception as e:
            logger.error("Geocode city failed", city=city_name, error=str(e))
            return None
