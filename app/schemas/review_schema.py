"""
review_schema.py — Pydantic schemas for review queue.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReviewItemResponse(BaseModel):
    id: uuid.UUID
    action_id: uuid.UUID
    action_type: str
    action_description: str
    action_json: Dict[str, Any]
    target_resource: str
    department: Optional[str]
    requested_by: Optional[str]
    risk_level: str
    risk_score: float
    risk_breakdown: Dict[str, Any] = {}
    priority: str
    status: str
    assigned_to: Optional[str]
    reviewer_comment: Optional[str]
    reviewed_by: Optional[str]
    reversibility: str
    affected_records: int
    confidence: float
    intent: Optional[str]
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime]
    due_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: List[ReviewItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApproveRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000)
    reviewed_by: Optional[str] = None


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)
    reviewed_by: Optional[str] = None


class ModifyRequest(BaseModel):
    modified_action_json: Dict[str, Any]
    reason: str = Field(..., min_length=1, max_length=1000)
    reviewed_by: Optional[str] = None


class ReviewActionResponse(BaseModel):
    review_id: uuid.UUID
    action_id: uuid.UUID
    status: str
    reviewed_by: Optional[str]
    reviewed_at: datetime
    message: str
