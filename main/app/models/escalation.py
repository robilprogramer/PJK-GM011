from sqlalchemy import String, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
import uuid


class EscalationLog(Base, TimestampMixin):
    __tablename__ = "escalation_logs"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    situation: Mapped[str] = mapped_column(Text, nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")

    session: Mapped["ChatSession"] = relationship(back_populates="escalations")
