"""
governance_schema.py — Pydantic schemas for governance flow.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.enums import DecisionType, RiskLevel, PolicyResult


class RiskBreakdownItem(BaseModel):
    factor: str
    score: float
    weight: float
    contribution: float
    icon: str = "fa-circle"


class RiskAssessmentResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    level: RiskLevel
    breakdown: List[RiskBreakdownItem]
    reversibility_score: float
    data_scope_score: float
    regulatory_score: float
    confidence_penalty: float


class PolicyRuleResult(BaseModel):
    rule_id: str
    name: str
    description: str
    status: PolicyResult  # pass | warn | block
    message: Optional[str] = None
    icon: str = "fa-shield-halved"


class PolicyCheckResult(BaseModel):
    overall: PolicyResult
    rules: List[PolicyRuleResult]
    blocked_by: Optional[str] = None


class GovernanceAssessmentRequest(BaseModel):
    action_id: uuid.UUID


class GovernanceAssessmentResponse(BaseModel):
    action_id: uuid.UUID
    current_stage: str
    risk_score: float
    risk_level: str
    risk_factors: List[RiskBreakdownItem]
    policy_rules: List[PolicyRuleResult]
    decision: str
    confidence: float
    reversible: bool
    reversibility: str
    data_scope: str
    regulations: List[str]
    timeline: List[Dict[str, Any]]
    metadata_: Optional[Dict[str, Any]] = None


class DecideRequest(BaseModel):
    action_id: uuid.UUID
    decision: DecisionType
    reason: Optional[str] = None
    override_by: Optional[str] = None


class DecideResponse(BaseModel):
    action_id: uuid.UUID
    decision: DecisionType
    previous_decision: str
    overridden_by: Optional[str] = None
    timestamp: datetime
