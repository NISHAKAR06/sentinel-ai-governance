"""
dashboard_schema.py — Pydantic schemas for the dashboard API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StatCardData(BaseModel):
    value: Any
    trend: Optional[float] = None
    trend_direction: str = "neutral"  # "up" | "down" | "neutral"


class ServiceHealth(BaseModel):
    name: str
    status: str           # "online" | "warning" | "offline"
    description: str
    latency: Optional[int] = None  # ms


class RecentAction(BaseModel):
    id: str
    action: str
    action_type: str
    resource: str
    risk_level: str
    risk_score: float
    status: str
    department: Optional[str]
    created_at: datetime


class AuditTimelineEntry(BaseModel):
    id: str
    action: str
    resource: str
    risk_level: str
    reviewer: str
    outcome: str
    timestamp: datetime


class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class ApprovalTrends(BaseModel):
    labels: List[str]
    auto: List[int]
    reviewed: List[int]
    rejected: List[int]


class HourlyActivity(BaseModel):
    hours: List[int]   # 0–23
    counts: List[int]  # requests per hour


class DashboardResponse(BaseModel):
    total_requests: int
    autonomous_actions: int
    pending_confirmations: int
    pending_reviews: int
    avg_risk: float
    requests_trend: float
    autonomous_trend: float
    risk_trend: float
    system_health_label: str
    hourly_activity: List[int]
    recent_actions: List[RecentAction]
    audit_timeline: List[AuditTimelineEntry]
    risk_distribution: RiskDistribution
    approval_trends: ApprovalTrends


class SystemHealthResponse(BaseModel):
    overall: str
    services: List[ServiceHealth]
