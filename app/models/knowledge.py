"""knowledge.py — Knowledge base ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Boolean, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID, JSONType


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    title: Mapped[str]       = mapped_column(String(300), nullable=False)
    category: Mapped[str]    = mapped_column(String(100), nullable=False, index=True)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=True)
    content: Mapped[str]     = mapped_column(String(10000), nullable=False)
    tags: Mapped[list]       = mapped_column(JSONType(), nullable=True, default=list)
    source: Mapped[str]      = mapped_column(String(300), nullable=True)
    author: Mapped[str]      = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool]  = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int]     = mapped_column(Integer, default=1, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
