from sqlalchemy import String, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    has_escalated: Mapped[bool] = mapped_column(Boolean, default=False)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    escalations: Mapped[list["EscalationLog"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
