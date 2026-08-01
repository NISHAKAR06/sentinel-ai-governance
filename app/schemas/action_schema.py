"""
action_schema.py — Pydantic schemas for Action entities.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    step: int
    description: str
    operation: str
    target: str
    estimated_records: int = 0
    reversible: bool = True


class ActionBase(BaseModel):
    natural_language: str = Field(..., min_length=1, max_length=5000)
    intent: str
    operation_type: str
    target_resource: str
    target_table: Optional[str] = None
    affected_records: int = 0
    action_json: Dict[str, Any] = Field(default_factory=dict)
    execution_plan: List[ExecutionStep] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reversibility: str = "reversible"
    data_scope: str = "single_record"
    regulatory_category: str = "none"
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    department: Optional[str] = None
    requested_by: Optional[str] = None


class ActionCreate(ActionBase):
    conversation_id: Optional[str] = None


class ActionUpdate(BaseModel):
    status: Optional[str] = None
    decision: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_comment: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    rollback_status: Optional[str] = None


class ActionResponse(ActionBase):
    id: uuid.UUID
    conversation_id: Optional[str] = None
    risk_score: float
    risk_level: str
    risk_breakdown: Dict[str, Any] = {}
    policy_result: str
    policy_violations: List[str] = []
    decision: str
    workflow_stage: str
    status: str
    execution_result: Optional[Dict[str, Any]] = None
    execution_logs: List[str] = []
    rollback_available: bool
    rollback_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ActionPreview(BaseModel):
    """Compact preview returned to the chat/assistant UI."""
    action_id: Optional[uuid.UUID] = None
    intent: str
    operation: str
    target_resource: str
    affected_records: int
    confidence: float
    risk_level: str
    reversible: bool
    action_json: Dict[str, Any]
    execution_plan: List[ExecutionStep] = []
