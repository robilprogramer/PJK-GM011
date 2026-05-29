import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.escalation import EscalationRequest, EscalationResponse
from app.schemas.common import SuccessResponse
from app.models.escalation import EscalationLog
from app.models.session import ChatSession
from app.core.exceptions import SessionNotFoundError

import structlog

logger = structlog.get_logger()
router = APIRouter()

EMERGENCY_NUMBERS = {
    "BNPB": "119",
    "Darurat Nasional": "112",
    "Ambulans": "118",
    "Polisi": "110",
    "Pemadam Kebakaran": "113",
    "SAR Nasional": "115",
    "PLN": "123",
}


@router.post(
    "",
    response_model=SuccessResponse[EscalationResponse],
    summary="Laporkan situasi darurat",
)
async def escalate_emergency(
    body: EscalationRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, body.session_id)
    if not session:
        raise SessionNotFoundError(body.session_id)

    esc_id = f"esc_{uuid.uuid4().hex[:10]}"
    db.add(EscalationLog(
        id=esc_id,
        session_id=body.session_id,
        situation=body.situation,
        contact_name=body.contact_name,
        contact_phone=body.contact_phone,
        city=body.location.city,
        province=body.location.province,
        lat=body.location.lat,
        lng=body.location.lng,
        status="pending",
    ))
    session.has_escalated = True
    await db.flush()

    logger.warning(
        "EMERGENCY ESCALATION",
        id=esc_id,
        location=body.location.display_name,
        situation=body.situation[:80],
    )

    return SuccessResponse(
        data=EscalationResponse(
            escalation_id=esc_id,
            message=(
                f"🚨 Laporan darurat dari {body.location.display_name} diterima. "
                f"ID: {esc_id}. Segera hubungi nomor darurat!"
            ),
            emergency_numbers=EMERGENCY_NUMBERS,
            status="pending",
        ),
        message="Laporan darurat berhasil dikirim",
    )


@router.get(
    "/{escalation_id}",
    response_model=SuccessResponse[dict],
    summary="Cek status laporan darurat",
)
async def get_escalation(escalation_id: str, db: AsyncSession = Depends(get_db)):
    log = await db.get(EscalationLog, escalation_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Laporan '{escalation_id}' tidak ditemukan")
    return SuccessResponse(data={
        "escalation_id": log.id,
        "status": log.status,
        "city": log.city,
        "province": log.province,
        "situation": log.situation,
        "contact_name": log.contact_name,
        "contact_phone": log.contact_phone,
        "created_at": log.created_at.isoformat(),
    })
