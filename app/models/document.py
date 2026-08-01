"""document.py — Document ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Boolean, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID, JSONType


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    title: Mapped[str]       = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str]    = mapped_column(String(80),  nullable=False, index=True)
    department: Mapped[str]  = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    file_path: Mapped[str]   = mapped_column(String(1000), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str]   = mapped_column(String(120), nullable=True)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool]  = mapped_column(Boolean, default=True)
    version: Mapped[int]     = mapped_column(Integer, default=1)
    owner_id: Mapped[str]    = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict]  = mapped_column("metadata", JSONType(), nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
