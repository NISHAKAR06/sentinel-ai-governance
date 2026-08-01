"""
review_routes.py — GET /review  GET /review/{id}
                   POST /review/{id}/approve  POST /review/{id}/reject
                   PUT /review/{id}
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.review_repository import ReviewRepository
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.review_schema import (
    ReviewListResponse,
    ReviewItemResponse,
    ApproveRequest,
    RejectRequest,
    ModifyRequest,
    ReviewActionResponse,
)
from app.services.audit_service import AuditService
from app.services.websocket_service import websocket_service
from app.core.exceptions import RecordNotFoundError, to_http_exception
from app.core.logger import api_logger
from app.core.constants import DEFAULT_PAGE_SIZE
from datetime import datetime, timezone

router = APIRouter()


def _repos(db: AsyncSession):
    return ReviewRepository(db), ActionRepository(db), AuditRepository(db)


@router.get("", response_model=ReviewListResponse, summary="List review queue items")
async def list_reviews(
    page:       int    = Query(1, ge=1),
    page_size:  int    = Query(DEFAULT_PAGE_SIZE, ge=1, le=200),
    status:     Optional[str] = None,
    risk_level: Optional[str] = None,
    priority:   Optional[str] = None,
    department: Optional[str] = None,
    query:      Optional[str] = None,
    limit:      Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    if limit:
        page_size = min(limit, 200)
    review_repo, _, _ = _repos(db)
    items, total = await review_repo.search(
        query=query,
        status=status,
        risk_level=risk_level,
        priority=priority,
        department=department,
        page=page,
        page_size=page_size,
    )
    import math
    return ReviewListResponse(
        items=[ReviewItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{review_id}", response_model=ReviewItemResponse, summary="Get a single review item")
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    review_repo, _, _ = _repos(db)
    try:
        item = await review_repo.get_by_id_or_raise(review_id)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)
    return ReviewItemResponse.model_validate(item)


@router.post("/{review_id}/approve", response_model=ReviewActionResponse, summary="Approve a review item")
async def approve_review(
    review_id: uuid.UUID,
    payload: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    review_repo, action_repo, audit_repo = _repos(db)
    reviewer = payload.reviewed_by or (current_user.get("sub") if current_user else "system")
    try:
        review = await review_repo.approve(review_id, reviewer, payload.reason)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)

    # Update linked action
    from app.core.enums import ActionStatus, WorkflowStage
    await action_repo.update_by_id(
        review.action_id,
        status=ActionStatus.APPROVED.value,
        reviewed_by=reviewer,
        review_comment=payload.reason,
        workflow_stage=WorkflowStage.EXECUTION.value,
    )

    # Audit
    audit_svc = AuditService(audit_repo)
    await audit_svc.log_review(
        reviewer=reviewer,
        action_id=review.action_id,
        review_status="approved",
        risk_level=review.risk_level,
        risk_score=review.risk_score,
        resource=review.target_resource,
        department=review.department,
    )

    await websocket_service.broadcast_review_update(review_id, "approved", reviewer)
    await websocket_service.notify(
        "Action approved",
        f"Review {str(review_id)[:8]} approved by {reviewer}",
        notif_type="success",
        icon="fa-check",
    )

    api_logger.info("Review approved", extra={"review_id": str(review_id), "reviewer": reviewer})
    return ReviewActionResponse(
        review_id=review_id,
        action_id=review.action_id,
        status="approved",
        reviewed_by=reviewer,
        reviewed_at=datetime.now(timezone.utc),
        message="Action approved and queued for execution",
    )


@router.post("/{review_id}/reject", response_model=ReviewActionResponse, summary="Reject a review item")
async def reject_review(
    review_id: uuid.UUID,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    review_repo, action_repo, audit_repo = _repos(db)
    reviewer = payload.reviewed_by or (current_user.get("sub") if current_user else "system")
    try:
        review = await review_repo.reject(review_id, reviewer, payload.reason)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)

    from app.core.enums import ActionStatus
    await action_repo.update_by_id(
        review.action_id,
        status=ActionStatus.REJECTED.value,
        reviewed_by=reviewer,
        review_comment=payload.reason,
    )

    audit_svc = AuditService(audit_repo)
    await audit_svc.log_review(
        reviewer=reviewer,
        action_id=review.action_id,
        review_status="rejected",
        risk_level=review.risk_level,
        risk_score=review.risk_score,
        resource=review.target_resource,
        reason=payload.reason,
        department=review.department,
    )

    await websocket_service.broadcast_review_update(review_id, "rejected", reviewer)
    await websocket_service.notify("Action rejected", payload.reason[:80], notif_type="danger")
    return ReviewActionResponse(
        review_id=review_id,
        action_id=review.action_id,
        status="rejected",
        reviewed_by=reviewer,
        reviewed_at=datetime.now(timezone.utc),
        message="Action rejected",
    )


@router.put("/{review_id}", response_model=ReviewActionResponse, summary="Modify and re-submit a review item")
async def modify_review(
    review_id: uuid.UUID,
    payload: ModifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    review_repo, action_repo, audit_repo = _repos(db)
    reviewer = payload.reviewed_by or (current_user.get("sub") if current_user else "system")
    try:
        review = await review_repo.modify(review_id, reviewer, payload.modified_action_json, payload.reason)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)

    from app.core.enums import ActionStatus
    await action_repo.update_by_id(
        review.action_id,
        status=ActionStatus.MODIFIED.value,
        action_json=payload.modified_action_json,
        reviewed_by=reviewer,
        review_comment=payload.reason,
    )

    audit_svc = AuditService(audit_repo)
    await audit_svc.log_review(
        reviewer=reviewer,
        action_id=review.action_id,
        review_status="modified",
        risk_level=review.risk_level,
        risk_score=review.risk_score,
        resource=review.target_resource,
        reason=payload.reason,
        department=review.department,
    )

    return ReviewActionResponse(
        review_id=review_id,
        action_id=review.action_id,
        status="modified",
        reviewed_by=reviewer,
        reviewed_at=datetime.now(timezone.utc),
        message="Action modified",
    )
