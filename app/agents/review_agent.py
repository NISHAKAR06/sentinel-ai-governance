"""
review_agent.py — Handles human review actions (approve/reject/modify).
Notifies the Execution Service on approval.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.agents.base_agent import BaseAgent, AgentContext
from app.core.enums import ActionStatus, WorkflowStage
from app.core.exceptions import ActionNotApprovedError, RecordNotFoundError
from app.core.logger import agent_logger


class ReviewAgent(BaseAgent):
    name = "ReviewAgent"

    def __init__(
        self,
        review_repo,      # ReviewRepository
        action_repo,      # ActionRepository
        audit_service,    # AuditService
        ws_manager,       # ConnectionManager
    ) -> None:
        self._review_repo = review_repo
        self._action_repo = action_repo
        self._audit       = audit_service
        self._ws          = ws_manager

    async def execute(self, context: AgentContext) -> AgentContext:
        """
        Default execute: used for approve flow triggered from context.
        review_status must be set to "approved" / "rejected" / "modified"
        before calling this.
        """
        self._log("Review processing", action_id=context.action_id, status=context.review_status)

        review_id = context.review_id
        status    = context.review_status or "approved"

        if not review_id:
            context.errors.append("ReviewAgent: review_id is missing in context")
            return context

        try:
            rid = uuid.UUID(review_id) if isinstance(review_id, str) else review_id
            if status == "approved":
                await self._approve(context, rid)
            elif status == "rejected":
                await self._reject(context, rid)
            elif status == "modified":
                await self._modify(context, rid)
        except Exception as exc:
            context.errors.append(f"ReviewAgent: {exc}")
            self._log_error("Review processing failed", error=str(exc))

        return context

    # ── Approve ───────────────────────────────────────────────
    async def _approve(self, context: AgentContext, review_id: uuid.UUID) -> None:
        reviewer = context.reviewed_by or "system"
        review   = await self._review_repo.approve(review_id, reviewer, context.review_comment)

        # Update action status
        if context.action_id:
            aid = uuid.UUID(context.action_id) if isinstance(context.action_id, str) else context.action_id
            await self._action_repo.update_status(aid, ActionStatus.APPROVED.value, WorkflowStage.EXECUTION.value)

        # WS push
        await self._ws.push_review_update({
            "review_id": str(review_id),
            "status":    "approved",
            "reviewed_by": reviewer,
        })
        await self._ws.push_notification(
            "Action approved",
            f"Review {str(review_id)[:8]} approved by {reviewer}",
            notif_type="success",
            icon="fa-check",
        )
        self._log("Action approved", review_id=str(review_id), reviewer=reviewer)

    # ── Reject ────────────────────────────────────────────────
    async def _reject(self, context: AgentContext, review_id: uuid.UUID) -> None:
        reviewer = context.reviewed_by or "system"
        reason   = context.review_comment or "No reason provided"
        await self._review_repo.reject(review_id, reviewer, reason)

        if context.action_id:
            aid = uuid.UUID(context.action_id) if isinstance(context.action_id, str) else context.action_id
            await self._action_repo.update_status(aid, ActionStatus.REJECTED.value)

        await self._ws.push_review_update({
            "review_id":  str(review_id),
            "status":     "rejected",
            "reviewed_by": reviewer,
            "reason":     reason,
        })
        await self._ws.push_notification(
            "Action rejected",
            f"Review {str(review_id)[:8]} rejected: {reason[:60]}",
            notif_type="danger",
            icon="fa-xmark",
        )
        self._log("Action rejected", review_id=str(review_id), reviewer=reviewer)

    # ── Modify ────────────────────────────────────────────────
    async def _modify(self, context: AgentContext, review_id: uuid.UUID) -> None:
        reviewer     = context.reviewed_by or "system"
        reason       = context.review_comment or "Modified"
        modified_json = (context.action.action_json if context.action else {})

        await self._review_repo.modify(review_id, reviewer, modified_json, reason)

        if context.action_id:
            aid = uuid.UUID(context.action_id) if isinstance(context.action_id, str) else context.action_id
            await self._action_repo.update_status(aid, ActionStatus.MODIFIED.value)

        await self._ws.push_review_update({
            "review_id":   str(review_id),
            "status":      "modified",
            "reviewed_by": reviewer,
        })
        self._log("Action modified", review_id=str(review_id), reviewer=reviewer)
