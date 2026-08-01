"""
review_repository.py — Review queue queries.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import ReviewQueue
from app.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository[ReviewQueue]):
    model = ReviewQueue

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_action_id(self, action_id: uuid.UUID) -> Optional[ReviewQueue]:
        stmt = select(ReviewQueue).where(ReviewQueue.action_id == action_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending(self) -> List[ReviewQueue]:
        stmt = (
            select(ReviewQueue)
            .where(ReviewQueue.status == "pending")
            .order_by(
                ReviewQueue.priority.desc(),
                ReviewQueue.created_at.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        priority: Optional[str] = None,
        department: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReviewQueue], int]:
        filters = []
        if query:
            q = f"%{query}%"
            filters.append(
                ReviewQueue.action_description.ilike(q) |
                ReviewQueue.action_type.ilike(q) |
                ReviewQueue.target_resource.ilike(q)
            )
        if status:
            filters.append(ReviewQueue.status == status)
        if risk_level:
            filters.append(ReviewQueue.risk_level == risk_level)
        if priority:
            filters.append(ReviewQueue.priority == priority)
        if department:
            filters.append(ReviewQueue.department == department)

        base    = select(ReviewQueue)
        count_q = select(func.count()).select_from(ReviewQueue)

        if filters:
            where   = and_(*filters)
            base    = base.where(where)
            count_q = count_q.where(where)

        offset = (page - 1) * page_size
        base = base.order_by(desc(ReviewQueue.created_at)).offset(offset).limit(page_size)

        items = list((await self.session.execute(base)).scalars().all())
        total = (await self.session.execute(count_q)).scalar_one()
        return items, total

    async def approve(
        self, review_id: uuid.UUID, reviewed_by: str, reason: Optional[str] = None
    ) -> ReviewQueue:
        return await self.update_by_id(
            review_id,
            status="approved",
            reviewed_by=reviewed_by,
            reviewer_comment=reason,
            reviewed_at=datetime.now(timezone.utc),
        )

    async def reject(
        self, review_id: uuid.UUID, reviewed_by: str, reason: str
    ) -> ReviewQueue:
        return await self.update_by_id(
            review_id,
            status="rejected",
            reviewed_by=reviewed_by,
            reviewer_comment=reason,
            reviewed_at=datetime.now(timezone.utc),
        )

    async def modify(
        self,
        review_id: uuid.UUID,
        reviewed_by: str,
        modified_json: dict,
        reason: str,
    ) -> ReviewQueue:
        return await self.update_by_id(
            review_id,
            status="modified",
            reviewed_by=reviewed_by,
            reviewer_comment=reason,
            action_json=modified_json,
            reviewed_at=datetime.now(timezone.utc),
        )

    async def count_by_status(self) -> Dict[str, int]:
        stmt = (
            select(ReviewQueue.status, func.count(ReviewQueue.id).label("cnt"))
            .group_by(ReviewQueue.status)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def count_by_priority(self) -> Dict[str, int]:
        stmt = (
            select(ReviewQueue.priority, func.count(ReviewQueue.id).label("cnt"))
            .where(ReviewQueue.status == "pending")
            .group_by(ReviewQueue.priority)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
