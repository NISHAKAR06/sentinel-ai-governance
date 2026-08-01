"""settings.py — Platform settings ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID, JSONType


class PlatformSettings(Base):
    __tablename__ = "settings"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    key: Mapped[str]         = mapped_column(String(200), unique=True, nullable=False, index=True)
    value: Mapped[dict]      = mapped_column(JSONType(), nullable=False)
    category: Mapped[str]    = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    is_secret: Mapped[bool]  = mapped_column(Boolean, default=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<PlatformSettings {self.key}>"
