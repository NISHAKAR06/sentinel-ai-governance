"""
analytics_routes.py — GET /analytics/summary  /daily  /risk  /operations  /trend
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.audit_repository import AuditRepository
from app.repositories.action_repository import ActionRepository
from app.schemas.analytics_schema import (
    AnalyticsSummary,
    DailyRequestData,
    RiskDistributionData,
    TopOperationsData,
    AdaptiveTrendData,
)

router = APIRouter()

_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}


def _days(period: str) -> int:
    return _PERIOD_DAYS.get(period, 30)


@router.get("/summary", response_model=AnalyticsSummary, summary="Analytics KPI summary")
async def get_summary(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    days       = _days(period)
    audit_repo = AuditRepository(db)
    action_repo = ActionRepository(db)

    outcome_counts = await audit_repo.outcome_counts(days=days)
    total     = sum(outcome_counts.values())
    auto      = outcome_counts.get("approved", 0) + outcome_counts.get("auto", 0)
    reviewed  = outcome_counts.get("reviewed", 0)
    rejected  = outcome_counts.get("rejected", 0)
    avg_risk  = await audit_repo.avg_risk_score(days=days)

    compliance_rate = round((auto + reviewed) / total * 100, 1) if total else 100.0

    # Trend vs previous period
    prev_counts = await audit_repo.outcome_counts(days=days * 2)
    prev_total  = sum(prev_counts.values())
    prev_half   = prev_total // 2 or 1
    total_trend = round((total - prev_half) / prev_half * 100, 1) if prev_half else 0

    return AnalyticsSummary(
        total_actions=total,
        auto_approved=auto,
        human_reviewed=reviewed,
        rejected=rejected,
        avg_risk=avg_risk,
        compliance_rate=compliance_rate,
        total_trend=total_trend,
        auto_trend=0.0,
        risk_trend=0.0,
        compliance_trend=0.0,
    )


@router.get("/daily", response_model=DailyRequestData, summary="Daily request counts")
async def get_daily(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    data = await audit_repo.daily_counts(days=_days(period))
    return DailyRequestData(
        labels=  [d["day"]      for d in data],
        total=   [d["total"]    for d in data],
        auto=    [d["auto"]     for d in data],
        reviewed=[d["reviewed"] for d in data],
        rejected=[d["rejected"] for d in data],
    )


@router.get("/risk", response_model=RiskDistributionData, summary="Risk level distribution")
async def get_risk_distribution(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    dist = await audit_repo.risk_distribution(days=_days(period))
    return RiskDistributionData(**dist)


@router.get("/operations", response_model=TopOperationsData, summary="Most requested operations")
async def get_top_operations(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    ops = await audit_repo.top_operations(days=_days(period), limit=8)
    return TopOperationsData(
        labels=[o["operation"] for o in ops],
        counts=[o["count"]     for o in ops],
    )


@router.get("/trend", response_model=AdaptiveTrendData, summary="Adaptive learning trend")
async def get_adaptive_trend(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    data = await audit_repo.daily_counts(days=_days(period))

    labels    = [d["day"]   for d in data]
    auto_rate = []
    avg_risk  = []

    for d in data:
        total = d["total"] or 1
        rate  = round(d["auto"] / total * 100, 1)
        auto_rate.append(rate)
        avg_risk.append(0)  # would need per-day avg risk query

    return AdaptiveTrendData(labels=labels, auto_rate=auto_rate, avg_risk=avg_risk)


@router.get("/export", summary="Export analytics report (CSV placeholder)")
async def export_report(
    period: str = Query("30d"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    return {"message": "Report export queued", "period": period, "format": "csv"}
