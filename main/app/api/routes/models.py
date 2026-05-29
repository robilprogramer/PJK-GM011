"""
GET  /api/models          — daftar semua model
GET  /api/models/active   — hanya model yang aktif (punya API key)
GET  /api/models/{id}     — detail satu model
POST /api/models/test     — test koneksi model
"""

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_llm_factory
from app.services.ai.llm_factory import LLMFactory
from app.schemas.model import ModelInfoResponse, ModelListResponse
from app.schemas.common import SuccessResponse
from app.core.config import settings
from app.core.exceptions import ModelNotFoundError

router = APIRouter()


def _to_response(info) -> ModelInfoResponse:
    return ModelInfoResponse(
        model_id=info.model_id,
        display_name=info.display_name,
        provider=info.provider,
        context_window=info.context_window,
        is_free=info.is_free,
        is_active=info.is_active,
        description=info.description,
        tags=info.tags,
    )


@router.get(
    "",
    response_model=SuccessResponse[ModelListResponse],
    summary="Daftar semua model yang tersedia",
    description="Menampilkan semua model yang terdaftar di SiagaAI beserta status aktif/nonaktifnya.",
)
async def list_models(
    factory: LLMFactory = Depends(get_llm_factory),
):
    all_models = factory.list_models(only_active=False)
    active = [m for m in all_models if m.is_active]

    return SuccessResponse(
        data=ModelListResponse(
            models=[_to_response(m) for m in all_models],
            default_model=settings.DEFAULT_MODEL,
            total=len(all_models),
            total_active=len(active),
        ),
        message=f"{len(all_models)} model tersedia, {len(active)} aktif",
    )


@router.get(
    "/active",
    response_model=SuccessResponse[ModelListResponse],
    summary="Daftar model yang aktif saja",
    description="Hanya model yang memiliki API key terkonfigurasi.",
)
async def list_active_models(
    factory: LLMFactory = Depends(get_llm_factory),
):
    active = factory.list_models(only_active=True)
    return SuccessResponse(
        data=ModelListResponse(
            models=[_to_response(m) for m in active],
            default_model=settings.DEFAULT_MODEL,
            total=len(active),
            total_active=len(active),
        ),
        message=f"{len(active)} model aktif",
    )


@router.get(
    "/{model_id}",
    response_model=SuccessResponse[ModelInfoResponse],
    summary="Detail satu model",
)
async def get_model(
    model_id: str,
    factory: LLMFactory = Depends(get_llm_factory),
):
    try:
        info = factory.get_model_info(model_id)
        return SuccessResponse(data=_to_response(info))
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/test",
    response_model=SuccessResponse[dict],
    summary="Test koneksi model",
    description="Kirim pesan test ke model untuk memverifikasi koneksi dan API key.",
)
async def test_model(
    model_id: str,
    factory: LLMFactory = Depends(get_llm_factory),
):
    try:
        llm = factory.get_llm(model_id)
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content="Balas dengan: OK")])
        return SuccessResponse(
            data={
                "model_id": model_id,
                "status": "ok",
                "response_preview": response.content[:100],
            },
            message=f"Model '{model_id}' berhasil diakses",
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal menghubungi model '{model_id}': {str(e)}"
        )
