"""
POST /api/chat/sessions              — buat sesi baru
POST /api/chat/send                  — kirim pesan
GET  /api/chat/sessions/{id}         — info sesi
GET  /api/chat/sessions/{id}/history — riwayat pesan
DELETE /api/chat/sessions/{id}       — tutup sesi
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_chatbot_service
from app.services.ai.chatbot import ChatbotService
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    NewSessionRequest, SessionResponse,
    SessionHistoryResponse, ChatMessageResponse,
)
from app.schemas.common import SuccessResponse
from app.models.session import ChatSession
from app.models.message import ChatMessage
from app.core.exceptions import SessionNotFoundError
from app.core.config import settings

import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/sessions",
    response_model=SuccessResponse[SessionResponse],
    summary="Buat sesi chat baru",
)
async def create_session(
    body: NewSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    session_id = f"ses_{uuid.uuid4().hex[:12]}"
    loc = body.location
    model = body.model_name or settings.DEFAULT_MODEL

    session = ChatSession(
        id=session_id,
        city=loc.city if loc else None,
        province=loc.province if loc else None,
        lat=loc.lat if loc else None,
        lng=loc.lng if loc else None,
        display_name=loc.display_name if loc else None,
        model_name=model,
    )
    db.add(session)
    await db.flush()

    logger.info("Session created", session_id=session_id, model=model)
    return SuccessResponse(
        data=SessionResponse(
            session_id=session_id,
            city=session.city,
            province=session.province,
            model_name=model,
            created_at=session.created_at.isoformat(),
        ),
        message="Sesi chat berhasil dibuat",
    )


@router.post(
    "/send",
    response_model=SuccessResponse[ChatResponse],
    summary="Kirim pesan ke chatbot",
)
async def send_message(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chatbot: ChatbotService = Depends(get_chatbot_service),
):
    session = await db.get(ChatSession, body.session_id)
    if not session:
        raise SessionNotFoundError(body.session_id)

    # Update lokasi jika belum ada
    if body.location and not session.city:
        session.city = body.location.city
        session.province = body.location.province
        session.lat = body.location.lat
        session.lng = body.location.lng
        session.display_name = body.location.display_name

    # Simpan pesan user
    db.add(ChatMessage(
        session_id=body.session_id,
        role="user",
        content=body.message,
    ))

    # Proses chatbot
    chat_response = await chatbot.process(body)

    # Simpan respons AI
    db.add(ChatMessage(
        session_id=body.session_id,
        role="assistant",
        content=chat_response.reply,
        intent=chat_response.intent.value,
        model_used=chat_response.model_used,
        requires_escalation=chat_response.requires_escalation,
    ))

    if chat_response.requires_escalation:
        session.has_escalated = True

    await db.flush()

    logger.info(
        "Message processed",
        session_id=body.session_id,
        intent=chat_response.intent,
        model=chat_response.model_used,
        escalation=chat_response.requires_escalation,
    )
    return SuccessResponse(data=chat_response, message="Pesan berhasil diproses")


@router.get(
    "/sessions/{session_id}",
    response_model=SuccessResponse[SessionResponse],
    summary="Ambil info sesi",
)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    count_result = await db.execute(
        select(func.count()).select_from(ChatMessage)
        .where(ChatMessage.session_id == session_id)
    )
    msg_count = count_result.scalar() or 0

    return SuccessResponse(
        data=SessionResponse(
            session_id=session.id,
            city=session.city,
            province=session.province,
            model_name=session.model_name,
            created_at=session.created_at.isoformat(),
            message_count=msg_count,
        )
    )


@router.get(
    "/sessions/{session_id}/history",
    response_model=SuccessResponse[SessionHistoryResponse],
    summary="Riwayat percakapan",
)
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return SuccessResponse(
        data=SessionHistoryResponse(
            session_id=session_id,
            messages=[
                ChatMessageResponse(
                    id=m.id, role=m.role, content=m.content,
                    intent=m.intent, model_used=m.model_used,
                    requires_escalation=m.requires_escalation,
                    suggested_actions=[],
                    timestamp=m.created_at.isoformat(),
                )
                for m in messages
            ],
            total=len(messages),
        )
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=SuccessResponse[dict],
    summary="Tutup sesi chat",
)
async def close_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise SessionNotFoundError(session_id)
    session.is_active = False
    await db.flush()
    return SuccessResponse(
        data={"session_id": session_id},
        message="Sesi berhasil ditutup",
    )
