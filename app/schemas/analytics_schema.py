"""
analytics_schema.py — Pydantic schemas for analytics endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_actions: int
    auto_approved: int
    human_reviewed: int
    rejected: int
    avg_risk: float
    compliance_rate: float
    total_trend: Optional[float] = None
    auto_trend: Optional[float] = None
    risk_trend: Optional[float] = None
    compliance_trend: Optional[float] = None


class DailyRequestData(BaseModel):
    labels: List[str]          # date strings
    total: List[int]
    auto: List[int]
    reviewed: List[int]
    rejected: List[int]


class RiskDistributionData(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class TopOperationsData(BaseModel):
    labels: List[str]    # operation names
    counts: List[int]


class AdaptiveTrendData(BaseModel):
    labels: List[str]    # date strings
    auto_rate: List[float]   # % auto-approved
    avg_risk: List[float]    # average risk score
