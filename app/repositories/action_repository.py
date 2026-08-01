"""
action_repository.py — Action queries.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.repositories.base_repository import BaseRepository


class ActionRepository(BaseRepository[Action]):
    model = Action

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_conversation(self, conversation_id: str) -> List[Action]:
        stmt = (
            select(Action)
            .where(Action.conversation_id == conversation_id)
            .order_by(Action.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_confirmations(self) -> List[Action]:
        stmt = (
            select(Action)
            .where(Action.decision == "confirm", Action.status == "pending")
            .order_by(desc(Action.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self) -> Dict[str, int]:
        stmt = (
            select(Action.status, func.count(Action.id))
            .group_by(Action.status)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def count_today(self) -> int:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.count(filters={"created_at": None})  # override below
        # proper implementation:
        stmt = select(func.count(Action.id)).where(Action.created_at >= today)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def recent(self, limit: int = 10) -> List[Action]:
        stmt = (
            select(Action)
            .order_by(desc(Action.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def avg_risk_score(self, days: int = 7) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(func.avg(Action.risk_score)).where(Action.created_at >= cutoff)
        result = await self.session.execute(stmt)
        val = result.scalar_one()
        return round(float(val or 0.0), 1)

    async def trend_comparison(self, days: int = 7) -> Dict[str, int]:
        """Return counts for current vs previous period."""
        now     = datetime.now(timezone.utc)
        current_start  = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)
        cur_stmt = select(func.count(Action.id)).where(Action.created_at >= current_start)
        prev_stmt = select(func.count(Action.id)).where(
            and_(Action.created_at >= previous_start, Action.created_at < current_start)
        )
        cur_count  = (await self.session.execute(cur_stmt)).scalar_one()
        prev_count = (await self.session.execute(prev_stmt)).scalar_one()
        return {"current": cur_count, "previous": prev_count}

    async def update_status(
        self, action_id: uuid.UUID, status: str, stage: Optional[str] = None
    ) -> Action:
        kwargs: dict = {"status": status}
        if stage:
            kwargs["workflow_stage"] = stage
        return await self.update_by_id(action_id, **kwargs)
