from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from app.schemas.location import LocationInput


class MessageRole(str, Enum):
    user      = "user"
    assistant = "assistant"
    system    = "system"


class MessageIntent(str, Enum):
    prediction  = "prediction"
    evacuation  = "evacuation"
    first_aid   = "first_aid"
    emergency   = "emergency"
    education   = "education"
    general     = "general"


class HistoryItem(BaseModel):
    role: MessageRole
    content: str


# ─── Requests ─────────────────────────────────────────────────────────────────

class NewSessionRequest(BaseModel):
    location: Optional[LocationInput] = None
    model_name: Optional[str] = None   # Pilih model saat buat sesi

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": {
                    "lat": -6.2088, "lng": 106.8456,
                    "city": "Jakarta Pusat", "province": "DKI Jakarta",
                    "display_name": "Jakarta Pusat, DKI Jakarta"
                },
                "model_name": "llama-3.3-70b-versatile"
            }
        }
    }


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(...)
    location: Optional[LocationInput] = None
    history: list[HistoryItem] = Field(default=[])
    model_name: Optional[str] = Field(
        default=None,
        description="Override model per request. Kosong = pakai default dari .env"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Apakah aman keluar rumah sekarang? Hujan deras sejak tadi pagi.",
                "session_id": "ses_abc123",
                "model_name": "llama-3.3-70b-versatile",
                "location": {
                    "lat": -6.2088, "lng": 106.8456,
                    "city": "Jakarta Pusat", "province": "DKI Jakarta",
                    "display_name": "Jakarta Pusat, DKI Jakarta"
                },
                "history": []
            }
        }
    }


# ─── Responses ────────────────────────────────────────────────────────────────

class ChatMessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    intent: Optional[MessageIntent] = None
    model_used: Optional[str] = None
    requires_escalation: bool = False
    suggested_actions: list[str] = []
    timestamp: str


class ChatResponse(BaseModel):
    success: bool = True
    reply: str
    intent: MessageIntent
    session_id: str
    model_used: str
    requires_escalation: bool = False
    suggested_actions: list[str] = []
    message_id: str


class SessionResponse(BaseModel):
    session_id: str
    city: Optional[str] = None
    province: Optional[str] = None
    model_name: Optional[str] = None
    created_at: str
    message_count: int = 0


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageResponse]
    total: int
