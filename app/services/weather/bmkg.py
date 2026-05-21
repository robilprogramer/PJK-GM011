import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.exceptions import BMKGServiceError
from app.schemas.location import EarthquakeData
import structlog

logger = structlog.get_logger()


class BMKGService:
    """Mengambil data gempa dan cuaca dari BMKG Open Data (tidak perlu API key)."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8), reraise=True)
    async def get_latest_earthquake(self) -> EarthquakeData:
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                resp = await client.get(settings.BMKG_GEMPA_URL)
                resp.raise_for_status()
                raw = resp.json()
                g = raw.get("Infogempa", {}).get("gempa", {})

                mag = g.get("Magnitude", "")
                wilayah = g.get("Wilayah", "")
                tanggal = g.get("Tanggal", "")
                jam = g.get("Jam", "")

                return EarthquakeData(
                    magnitude=mag,
                    depth=g.get("Kedalaman"),
                    location=wilayah,
                    date=tanggal,
                    time=jam,
                    felt=g.get("Dirasakan", "Tidak ada laporan"),
                    summary=(
                        f"M{mag} di {wilayah} ({tanggal} {jam})"
                        if mag else "Tidak ada aktivitas gempa signifikan"
                    ),
                )
        except Exception as e:
            logger.warning("BMKG error, returning default", error=str(e))
            return EarthquakeData()

    async def get_recent_earthquakes(self, limit: int = 5) -> list[dict]:
        """Daftar gempa terkini dari BMKG."""
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
                resp = await client.get(settings.BMKG_GEMPA_LIST_URL)
                resp.raise_for_status()
                raw = resp.json()
                gempa_list = raw.get("Infogempa", {}).get("gempa", [])
                return [
                    {
                        "magnitude": g.get("Magnitude"),
                        "depth": g.get("Kedalaman"),
                        "location": g.get("Wilayah"),
                        "date": g.get("Tanggal"),
                        "time": g.get("Jam"),
                        "felt": g.get("Dirasakan", "-"),
                    }
                    for g in gempa_list[:limit]
                ]
        except Exception as e:
            logger.warning("BMKG list error", error=str(e))
            return []
