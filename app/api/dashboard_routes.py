"""
dashboard_routes.py — GET /dashboard/stats  GET /dashboard/health  GET /dashboard/activity
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.review_repository import ReviewRepository
from app.services.dashboard_service import DashboardService
from app.core.logger import api_logger
from typing import Optional

router = APIRouter()


def _svc(db: AsyncSession) -> DashboardService:
    return DashboardService(
        action_repo=ActionRepository(db),
        audit_repo=AuditRepository(db),
        review_repo=ReviewRepository(db),
    )


@router.get("/stats", summary="Full dashboard statistics")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    svc = _svc(db)
    result = await svc.get_stats()
    return result


@router.get("/health", summary="System health status")
async def get_health(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    svc = _svc(db)
    return await svc.get_system_health()


@router.get("/activity", summary="Recent platform activity feed")
async def get_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    entries    = await audit_repo.get_recent(limit=limit)
    return {
        "items": [
            {
                "id":         str(e.id),
                "action":     e.action,
                "resource":   e.resource,
                "risk_level": e.risk_level,
                "outcome":    e.outcome,
                "actor":      e.actor,
                "timestamp":  e.timestamp.isoformat(),
            }
            for e in entries
        ],
        "total": len(entries),
    }
