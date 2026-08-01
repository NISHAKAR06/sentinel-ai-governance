"""action.py — Action ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID, JSONType


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    requested_by: Mapped[str | None]    = mapped_column(String(200), nullable=True)
    department: Mapped[str | None]      = mapped_column(String(100), nullable=True)
    natural_language: Mapped[str]       = mapped_column(String(5000), nullable=False)
    intent: Mapped[str]                 = mapped_column(String(300),  nullable=False)
    operation_type: Mapped[str]         = mapped_column(String(50),   nullable=False, index=True)
    target_resource: Mapped[str]        = mapped_column(String(300),  nullable=False)
    target_table: Mapped[str | None]    = mapped_column(String(100),  nullable=True)
    affected_records: Mapped[int]       = mapped_column(Integer, default=0)
    action_json: Mapped[dict]           = mapped_column(JSONType(), nullable=False, default=dict)
    execution_plan: Mapped[list]        = mapped_column(JSONType(), nullable=True, default=list)
    parameters: Mapped[dict]            = mapped_column(JSONType(), nullable=True, default=dict)
    risk_score: Mapped[float]           = mapped_column(Float, default=0.0)
    risk_level: Mapped[str]             = mapped_column(String(20), default="low", index=True)
    risk_breakdown: Mapped[dict]        = mapped_column(JSONType(), nullable=True, default=dict)
    reversibility: Mapped[str]          = mapped_column(String(30), default="reversible")
    data_scope: Mapped[str]             = mapped_column(String(30), default="single_record")
    regulatory_category: Mapped[str]    = mapped_column(String(30), default="none")
    policy_result: Mapped[str]          = mapped_column(String(20), default="pass")
    policy_violations: Mapped[list]     = mapped_column(JSONType(), nullable=True, default=list)
    decision: Mapped[str]               = mapped_column(String(20), default="review", index=True)
    confidence: Mapped[float]           = mapped_column(Float, default=0.0)
    workflow_stage: Mapped[str]         = mapped_column(String(30), default="intake", index=True)
    status: Mapped[str]                 = mapped_column(String(30), default="pending", index=True)
    execution_result: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    execution_logs: Mapped[list]          = mapped_column(JSONType(), nullable=True, default=list)
    rollback_available: Mapped[bool]      = mapped_column(Boolean, nullable=False, default=True)
    rollback_status: Mapped[str | None]   = mapped_column(String(30), nullable=True)
    reviewed_by: Mapped[str | None]     = mapped_column(String(200), nullable=True)
    review_comment: Mapped[str | None]  = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    executed_at: Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Action {self.id} op={self.operation_type} status={self.status}>"
