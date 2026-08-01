"""
execution_routes.py — GET /execution/{id}  POST /execution/{id}/execute
                       POST /execution/{id}/rollback  GET /execution/{id}/logs
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.action_repository import ActionRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.execution_service import ExecutionService
from app.services.audit_service import AuditService
from app.core.websocket_manager import ws_manager
from app.core.exceptions import RecordNotFoundError, ExecutionError, RollbackError, to_http_exception
from app.core.logger import api_logger

router = APIRouter()


def _svc(db: AsyncSession) -> ExecutionService:
    return ExecutionService(
        action_repo=ActionRepository(db),
        employee_repo=EmployeeRepository(db),
        knowledge_repo=KnowledgeRepository(db),
        ws_manager=ws_manager,
    )


@router.get("/{action_id}", summary="Get execution status for an action")
async def get_execution_status(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo = ActionRepository(db)
    try:
        action = await repo.get_by_id_or_raise(action_id)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)
    return {
        "action_id":         str(action.id),
        "status":            action.status,
        "workflow_stage":    action.workflow_stage,
        "execution_result":  action.execution_result,
        "execution_logs":    action.execution_logs or [],
        "rollback_available": action.rollback_available,
        "rollback_status":   action.rollback_status,
        "executed_at":       action.executed_at.isoformat() if action.executed_at else None,
        "completed_at":      action.completed_at.isoformat() if action.completed_at else None,
    }


@router.post("/{action_id}/execute", summary="Execute an approved action")
async def execute_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    executed_by = current_user.get("sub", "system") if current_user else "system"
    svc = _svc(db)
    try:
        result = await svc.execute_action(action_id, executed_by)
    except (RecordNotFoundError, ExecutionError) as exc:
        if isinstance(exc, RecordNotFoundError):
            raise to_http_exception(exc)
        raise to_http_exception(ExecutionError(str(action_id), str(exc)))

    audit_repo  = AuditRepository(db)
    action_repo = ActionRepository(db)
    action      = await action_repo.get_by_id_or_raise(action_id)
    audit_svc   = AuditService(audit_repo)
    await audit_svc.log_execution(
        actor=executed_by,
        action_id=action_id,
        status="completed",
        resource=action.target_resource,
        risk_level=action.risk_level,
        risk_score=action.risk_score,
        duration_ms=result.duration_ms,
        department=action.department,
    )

    return {
        "action_id":      str(action_id),
        "status":         "completed",
        "success":        result.success,
        "rows_affected":  result.rows_affected,
        "duration_ms":    result.duration_ms,
        "logs":           result.logs,
        "rollback_available": result.rollback_available,
    }


@router.post("/{action_id}/rollback", summary="Rollback a completed action")
async def rollback_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    rolled_back_by = current_user.get("sub", "system") if current_user else "system"
    svc = _svc(db)
    try:
        result = await svc.rollback_action(action_id, rolled_back_by)
    except (RecordNotFoundError, RollbackError) as exc:
        raise to_http_exception(exc)

    return {
        "action_id":     str(action_id),
        "status":        "rolled_back",
        "rolled_back_by": rolled_back_by,
        "logs":          result.logs,
    }


@router.get("/{action_id}/logs", summary="Stream execution logs for an action")
async def get_execution_logs(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo = ActionRepository(db)
    try:
        action = await repo.get_by_id_or_raise(action_id)
    except RecordNotFoundError as exc:
        raise to_http_exception(exc)
    return {
        "action_id": str(action_id),
        "logs":      action.execution_logs or [],
        "status":    action.status,
    }
