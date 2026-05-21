"""
GET  /api/knowledge/stats    — statistik knowledge base
POST /api/knowledge/search   — test semantic search
POST /api/knowledge/reload   — reload dari file JSON
DELETE /api/knowledge/reset  — reset seluruh KB (dev only)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_knowledge_base
from app.services.ai.knowledge_base import KnowledgeBaseService
from app.schemas.common import SuccessResponse
from app.core.config import settings

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    n_results: int = 3


@router.get(
    "/stats",
    response_model=SuccessResponse[dict],
    summary="Statistik knowledge base",
)
async def get_stats(kb: KnowledgeBaseService = Depends(get_knowledge_base)):
    return SuccessResponse(data=kb.get_stats())


@router.post(
    "/search",
    response_model=SuccessResponse[dict],
    summary="Test semantic search di knowledge base",
)
async def search_kb(
    body: SearchRequest,
    kb: KnowledgeBaseService = Depends(get_knowledge_base),
):
    docs = await kb.search(body.query, n_results=body.n_results)
    return SuccessResponse(
        data={"query": body.query, "results": docs, "count": len(docs)},
        message=f"{len(docs)} dokumen ditemukan",
    )


@router.post(
    "/reload",
    response_model=SuccessResponse[dict],
    summary="Reload knowledge base dari dataset JSON",
)
async def reload_kb(
    dataset_path: str = Query(
        default="app/data/disaster_knowledge.json",
        description="Path ke file dataset JSON",
    ),
    kb: KnowledgeBaseService = Depends(get_knowledge_base),
):
    count = kb.load_from_json(dataset_path)
    if count == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Gagal load dataset dari '{dataset_path}'. Pastikan file ada dan formatnya benar.",
        )
    return SuccessResponse(
        data={"loaded": count, "path": dataset_path},
        message=f"{count} dokumen berhasil dimuat ke knowledge base",
    )


@router.delete(
    "/reset",
    response_model=SuccessResponse[dict],
    summary="Reset knowledge base (dev only)",
)
async def reset_kb(kb: KnowledgeBaseService = Depends(get_knowledge_base)):
    if settings.APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Reset tidak diizinkan di production")
    ok = kb.reset()
    return SuccessResponse(
        data={"reset": ok},
        message="Knowledge base berhasil di-reset" if ok else "Reset gagal",
    )
