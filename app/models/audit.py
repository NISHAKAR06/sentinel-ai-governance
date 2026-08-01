"""audit.py — Audit Log ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID, JSONType


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    action_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str]  = mapped_column(String(80),  nullable=False, index=True)
    action: Mapped[str]      = mapped_column(String(200), nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=True)
    resource: Mapped[str]    = mapped_column(String(300), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    actor: Mapped[str]       = mapped_column(String(200), nullable=False, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reviewer: Mapped[str | None]   = mapped_column(String(200), nullable=True)
    risk_level: Mapped[str]  = mapped_column(String(20), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_breakdown: Mapped[dict] = mapped_column(JSONType(), nullable=True, default=dict)
    decision: Mapped[str]    = mapped_column(String(30), nullable=False, index=True)
    outcome: Mapped[str]     = mapped_column(String(30), nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    execution_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    execution_duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    rollback_executed: Mapped[bool]      = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict]  = mapped_column("metadata", JSONType(), nullable=True, default=dict)
    ip_address: Mapped[str | None]  = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None]  = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.event_type} outcome={self.outcome}>"
