"""review.py — Review Queue ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID, JSONType


class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    action_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[str] = mapped_column(String(2000), nullable=False)
    action_json: Mapped[dict] = mapped_column(JSONType(), nullable=False, default=dict)
    target_resource: Mapped[str] = mapped_column(String(300), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    risk_level: Mapped[str]  = mapped_column(String(20), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[str]    = mapped_column(String(20), nullable=False, default="medium", index=True)
    status: Mapped[str]      = mapped_column(String(30), nullable=False, default="pending", index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    reviewed_by: Mapped[str | None]      = mapped_column(String(200), nullable=True)
    reversibility: Mapped[str] = mapped_column(String(30), default="reversible")
    affected_records: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    intent: Mapped[str]      = mapped_column(String(2000), nullable=True)
    risk_breakdown: Mapped[dict] = mapped_column(JSONType(), nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None]      = mapped_column(DateTime(timezone=True), nullable=True)
