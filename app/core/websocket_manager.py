"""
websocket_manager.py — Manages all active WebSocket connections and broadcasts.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.enums import WSEventType
from app.core.logger import ws_logger


class ConnectionManager:
    """
    Maintains sets of WebSocket connections grouped by channel.
    Channels: 'dashboard', 'audit', 'review', 'notifications', 'global'
    """

    def __init__(self):
        # channel → set of websockets
        self._channels: Dict[str, Set[WebSocket]] = defaultdict(set)
        # websocket → metadata
        self._meta: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    # ── Connect ───────────────────────────────────────────────
    async def connect(
        self,
        ws: WebSocket,
        channel: str = "global",
        user_id: Optional[str] = None,
    ) -> None:
        await ws.accept()
        async with self._lock:
            self._channels[channel].add(ws)
            self._channels["global"].add(ws)
            self._meta[ws] = {
                "channel":    channel,
                "user_id":    user_id,
                "connected_at": datetime.now(timezone.utc).isoformat(),
            }
        ws_logger.info("WebSocket connected", extra={"channel": channel, "user_id": user_id})
        await self.send_personal(ws, {"type": WSEventType.CONNECTED, "channel": channel})

    # ── Disconnect ────────────────────────────────────────────
    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            meta = self._meta.pop(ws, {})
            channel = meta.get("channel", "global")
            self._channels[channel].discard(ws)
            self._channels["global"].discard(ws)
        ws_logger.info("WebSocket disconnected", extra={"channel": channel})

    # ── Send to one connection ────────────────────────────────
    async def send_personal(self, ws: WebSocket, data: Dict[str, Any]) -> bool:
        if ws.client_state != WebSocketState.CONNECTED:
            return False
        try:
            await ws.send_text(json.dumps(data, default=str))
            return True
        except Exception as exc:
            ws_logger.warning("Failed to send personal message", extra={"error": str(exc)})
            await self.disconnect(ws)
            return False

    # ── Broadcast to channel ──────────────────────────────────
    async def broadcast(
        self,
        data: Dict[str, Any],
        channel: str = "global",
        exclude: Optional[WebSocket] = None,
    ) -> int:
        connections = set(self._channels.get(channel, set()))
        sent = 0
        dead: list[WebSocket] = []
        for ws in connections:
            if ws is exclude:
                continue
            if ws.client_state != WebSocketState.CONNECTED:
                dead.append(ws)
                continue
            try:
                await ws.send_text(json.dumps(data, default=str))
                sent += 1
            except Exception:
                dead.append(ws)
        # cleanup dead connections
        for ws in dead:
            await self.disconnect(ws)
        return sent

    # ── Typed event helpers ───────────────────────────────────
    async def push_dashboard_update(self, payload: Dict[str, Any]) -> None:
        await self.broadcast(
            {"type": WSEventType.DASHBOARD_UPDATE, "data": payload, "ts": _now()},
            channel="dashboard",
        )

    async def push_review_new(self, payload: Dict[str, Any]) -> None:
        await self.broadcast(
            {"type": WSEventType.REVIEW_NEW, "data": payload, "ts": _now()},
            channel="review",
        )

    async def push_review_update(self, payload: Dict[str, Any]) -> None:
        await self.broadcast(
            {"type": WSEventType.REVIEW_UPDATE, "data": payload, "ts": _now()},
            channel="review",
        )

    async def push_audit_new(self, payload: Dict[str, Any]) -> None:
        await self.broadcast(
            {"type": WSEventType.AUDIT_NEW, "data": payload, "ts": _now()},
            channel="audit",
        )

    async def push_notification(
        self,
        title: str,
        message: str,
        notif_type: str = "info",
        icon: str = "fa-bell",
    ) -> None:
        await self.broadcast(
            {
                "type":    WSEventType.NOTIFICATION,
                "data":    {"title": title, "message": message, "type": notif_type, "icon": icon},
                "ts":      _now(),
            },
            channel="global",
        )

    async def push_action_status(self, action_id: str, status: str, progress: int = 0) -> None:
        await self.broadcast(
            {
                "type": WSEventType.ACTION_STATUS,
                "data": {"action_id": action_id, "status": status, "progress": progress},
                "ts":   _now(),
            },
            channel="global",
        )

    async def push_execution_progress(
        self, action_id: str, step: str, progress: int, log_line: str
    ) -> None:
        await self.broadcast(
            {
                "type": WSEventType.EXECUTION_PROGRESS,
                "data": {
                    "action_id": action_id,
                    "step":      step,
                    "progress":  progress,
                    "log":       log_line,
                },
                "ts": _now(),
            },
            channel="global",
        )

    # ── Stats ─────────────────────────────────────────────────
    @property
    def total_connections(self) -> int:
        return len(self._meta)

    def channel_count(self, channel: str) -> int:
        return len(self._channels.get(channel, set()))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Singleton instance ────────────────────────────────────────
ws_manager = ConnectionManager()
