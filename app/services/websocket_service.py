"""
websocket_service.py — Higher-level WebSocket event orchestration.
Wraps ConnectionManager with domain-aware broadcast helpers.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from app.core.websocket_manager import ws_manager
from app.core.logger import ws_logger


class WebSocketService:
    """
    Thin service layer over ConnectionManager.
    Used by routers and other services to push real-time updates
    without directly depending on the ws_manager singleton.
    """

    async def broadcast_dashboard_update(self, stats: Dict[str, Any]) -> None:
        await ws_manager.push_dashboard_update(stats)

    async def broadcast_new_review(
        self,
        review_id: uuid.UUID,
        action_type: str,
        risk_level: str,
        priority: str,
        department: Optional[str] = None,
    ) -> None:
        await ws_manager.push_review_new({
            "review_id":   str(review_id),
            "action_type": action_type,
            "risk_level":  risk_level,
            "priority":    priority,
            "department":  department,
        })
        ws_logger.info("New review broadcast", extra={"review_id": str(review_id)})

    async def broadcast_review_update(
        self,
        review_id: uuid.UUID,
        status: str,
        reviewed_by: Optional[str] = None,
    ) -> None:
        await ws_manager.push_review_update({
            "review_id":   str(review_id),
            "status":      status,
            "reviewed_by": reviewed_by,
        })

    async def broadcast_audit_entry(self, audit_data: Dict[str, Any]) -> None:
        await ws_manager.push_audit_new(audit_data)

    async def notify(
        self,
        title: str,
        message: str,
        notif_type: str = "info",
        icon: str = "fa-bell",
    ) -> None:
        await ws_manager.push_notification(title, message, notif_type, icon)

    async def push_action_status(
        self, action_id: uuid.UUID, status: str, progress: int = 0
    ) -> None:
        await ws_manager.push_action_status(str(action_id), status, progress)


# ── Module-level singleton ────────────────────────────────────
websocket_service = WebSocketService()
