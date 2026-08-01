"""
audit_service.py — Creates immutable audit log entries.
Receives action + decision context. Stores via AuditRepository.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.repositories.audit_repository import AuditRepository
from app.core.logger import audit_logger


class AuditService:
    """
    Creates structured audit records for every governance event.
    All writes go through the AuditRepository.
    """

    def __init__(self, audit_repo: AuditRepository) -> None:
        self._repo = audit_repo

    async def log_action(
        self,
        *,
        event_type: str,
        action: str,
        resource: str,
        actor: str,
        risk_level: str,
        risk_score: float,
        decision: str,
        outcome: str,
        action_id: Optional[uuid.UUID] = None,
        conversation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        department: Optional[str] = None,
        description: Optional[str] = None,
        actor_role: Optional[str] = None,
        reviewer: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        execution_status: Optional[str] = None,
        execution_duration_ms: float = 0.0,
        rollback_executed: bool = False,
        risk_breakdown: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        try:
            await self._repo.create(
                event_type=event_type,
                action=action,
                resource=resource,
                actor=actor,
                risk_level=risk_level,
                risk_score=risk_score,
                decision=decision,
                outcome=outcome,
                action_id=action_id,
                conversation_id=conversation_id,
                operation_type=operation_type,
                department=department,
                description=description,
                actor_role=actor_role,
                reviewer=reviewer,
                rejection_reason=rejection_reason,
                execution_status=execution_status,
                execution_duration_ms=execution_duration_ms,
                rollback_executed=rollback_executed,
                risk_breakdown=risk_breakdown or {},
                metadata_=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(timezone.utc),
            )
            audit_logger.info(
                "Audit entry created",
                extra={
                    "event":    event_type,
                    "action":   action,
                    "outcome":  outcome,
                    "risk":     risk_level,
                    "actor":    actor,
                },
            )
        except Exception as exc:
            audit_logger.error("Failed to create audit entry", extra={"error": str(exc)})

    async def log_chat(
        self,
        actor: str,
        natural_language: str,
        conversation_id: Optional[str],
        action_id: Optional[uuid.UUID],
        department: Optional[str] = None,
    ) -> None:
        await self.log_action(
            event_type="CHAT_REQUEST",
            action="AI Assistant request",
            resource=f"conversation:{conversation_id}",
            actor=actor,
            risk_level="low",
            risk_score=0.0,
            decision="pending",
            outcome="received",
            action_id=action_id,
            conversation_id=conversation_id,
            department=department,
            description=natural_language[:300],
        )

    async def log_governance(
        self,
        actor: str,
        action_id: uuid.UUID,
        risk_score: float,
        risk_level: str,
        decision: str,
        resource: str,
        risk_breakdown: Optional[Dict[str, Any]] = None,
        department: Optional[str] = None,
    ) -> None:
        await self.log_action(
            event_type="GOVERNANCE_DECISION",
            action=f"Governance decision: {decision.upper()}",
            resource=resource,
            actor=actor,
            risk_level=risk_level,
            risk_score=risk_score,
            decision=decision,
            outcome=decision,
            action_id=action_id,
            department=department,
            risk_breakdown=risk_breakdown,
        )

    async def log_review(
        self,
        reviewer: str,
        action_id: uuid.UUID,
        review_status: str,
        risk_level: str,
        risk_score: float,
        resource: str,
        reason: Optional[str] = None,
        department: Optional[str] = None,
    ) -> None:
        await self.log_action(
            event_type="HUMAN_REVIEW",
            action=f"Review: {review_status.upper()}",
            resource=resource,
            actor=reviewer,
            risk_level=risk_level,
            risk_score=risk_score,
            decision="review",
            outcome=review_status,
            action_id=action_id,
            reviewer=reviewer,
            rejection_reason=reason if review_status == "rejected" else None,
            department=department,
        )

    async def log_execution(
        self,
        actor: str,
        action_id: uuid.UUID,
        status: str,
        resource: str,
        risk_level: str,
        risk_score: float,
        duration_ms: float = 0.0,
        rollback_executed: bool = False,
        department: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        await self.log_action(
            event_type="EXECUTION",
            action=f"Execute action: {status.upper()}",
            resource=resource,
            actor=actor,
            risk_level=risk_level,
            risk_score=risk_score,
            decision="approved",
            outcome=status,
            action_id=action_id,
            execution_status=status,
            execution_duration_ms=duration_ms,
            rollback_executed=rollback_executed,
            department=department,
            description=description,
        )
