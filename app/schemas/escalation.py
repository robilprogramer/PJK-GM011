from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.location import LocationInput


class EscalationRequest(BaseModel):
    session_id: str
    location: LocationInput
    situation: str = Field(..., min_length=10, max_length=1000)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "ses_abc123",
                "location": {
                    "lat": -7.2575, "lng": 112.7521,
                    "city": "Surabaya", "province": "Jawa Timur",
                    "display_name": "Surabaya, Jawa Timur"
                },
                "situation": "Banjir setinggi 1 meter masuk rumah, tidak bisa keluar. 4 orang termasuk 1 lansia.",
                "contact_name": "Budi Santoso",
                "contact_phone": "081234567890"
            }
        }
    }


class EscalationResponse(BaseModel):
    success: bool = True
    escalation_id: str
    message: str
    emergency_numbers: dict
    status: str = "pending"
