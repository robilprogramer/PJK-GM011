from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone

from app.api.deps import get_db, get_bmkg_service, get_owm_service, get_llm_factory
from app.core.config import settings

router = APIRouter()


@router.get("", summary="Health check semua layanan")
async def health_check(
    db: AsyncSession = Depends(get_db),
    bmkg=Depends(get_bmkg_service),
    owm=Depends(get_owm_service),
    factory=Depends(get_llm_factory),
):
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # BMKG
    try:
        eq = await bmkg.get_latest_earthquake()
        checks["bmkg"] = "ok" if eq.summary else "no_data"
    except Exception as e:
        checks["bmkg"] = f"error: {e}"

    # OpenWeatherMap (test Jakarta)
    try:
        if settings.OWM_API_KEY:
            w = await owm.get_current_weather(-6.2088, 106.8456)
            checks["openweathermap"] = "ok"
        else:
            checks["openweathermap"] = "no_api_key"
    except Exception as e:
        checks["openweathermap"] = f"error: {e}"

    # LLM Models
    active_models = factory.list_models(only_active=True)
    checks["llm_models"] = {
        "default": settings.DEFAULT_MODEL,
        "active_count": len(active_models),
        "active": [m.model_id for m in active_models],
    }

    overall = "healthy" if all(
        v == "ok" for k, v in checks.items() if k != "llm_models"
    ) else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": checks,
    }
