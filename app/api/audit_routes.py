"""
audit_routes.py — GET /audit  GET /audit/export/csv  GET /audit/export/json
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.audit_repository import AuditRepository
from app.core.constants import DEFAULT_PAGE_SIZE

router = APIRouter()


@router.get("", summary="List audit logs")
async def list_audit_logs(
    page:       int    = Query(1, ge=1),
    page_size:  int    = Query(DEFAULT_PAGE_SIZE, ge=1, le=200),
    limit:      Optional[int] = None,
    query:      Optional[str] = None,
    risk_level: Optional[str] = None,
    outcome:    Optional[str] = None,
    date_from:  Optional[datetime] = None,
    date_to:    Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    if limit:
        page_size = min(limit, 200)
    audit_repo = AuditRepository(db)
    items, total = await audit_repo.search(
        query=query,
        risk_level=risk_level,
        outcome=outcome,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    import math
    return {
        "items": [
            {
                "id":           str(e.id),
                "action_id":    str(e.action_id) if e.action_id else None,
                "event_type":   e.event_type,
                "action":       e.action,
                "resource":     e.resource,
                "risk_level":   e.risk_level,
                "risk_score":   e.risk_score,
                "decision":     e.decision,
                "outcome":      e.outcome,
                "actor":        e.actor,
                "reviewer":     e.reviewer,
                "department":   e.department,
                "description":  e.description,
                "timestamp":    e.timestamp.isoformat(),
                "details":      e.description,
            }
            for e in items
        ],
        "total":       total,
        "page":        page,
        "page_size":   page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


@router.get("/export/csv", summary="Export audit logs as CSV")
async def export_csv(
    risk_level: Optional[str] = None,
    outcome:    Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    items, _ = await audit_repo.search(
        risk_level=risk_level, outcome=outcome, page=1, page_size=1000
    )

    def csv_generator():
        yield "id,action,resource,risk_level,risk_score,outcome,actor,reviewer,timestamp\n"
        for e in items:
            yield (
                f"{e.id},{e.action},{e.resource},{e.risk_level},"
                f"{e.risk_score},{e.outcome},{e.actor},{e.reviewer or ''},"
                f"{e.timestamp.isoformat()}\n"
            )

    return StreamingResponse(
        csv_generator(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


@router.get("/export/json", summary="Export audit logs as JSON")
async def export_json_file(
    risk_level: Optional[str] = None,
    outcome:    Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    audit_repo = AuditRepository(db)
    items, _ = await audit_repo.search(
        risk_level=risk_level, outcome=outcome, page=1, page_size=1000
    )
    data = [
        {
            "id":         str(e.id),
            "action":     e.action,
            "resource":   e.resource,
            "risk_level": e.risk_level,
            "risk_score": e.risk_score,
            "outcome":    e.outcome,
            "actor":      e.actor,
            "reviewer":   e.reviewer,
            "timestamp":  e.timestamp.isoformat(),
        }
        for e in items
    ]
    return StreamingResponse(
        iter([json.dumps(data, default=str)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=audit_logs.json"},
    )
