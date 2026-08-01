"""
knowledge_repository.py — Knowledge base queries.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeBase
from app.repositories.base_repository import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeBase]):
    model = KnowledgeBase

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(self, query: str, limit: int = 10) -> List[KnowledgeBase]:
        q = f"%{query}%"
        stmt = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.is_active == True,
                or_(
                    KnowledgeBase.title.ilike(q),
                    KnowledgeBase.content.ilike(q),
                    KnowledgeBase.category.ilike(q),
                ),
            )
            .order_by(KnowledgeBase.relevance_score.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(self, category: str) -> List[KnowledgeBase]:
        stmt = (
            select(KnowledgeBase)
            .where(KnowledgeBase.category == category, KnowledgeBase.is_active == True)
            .order_by(KnowledgeBase.relevance_score.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active(self) -> List[KnowledgeBase]:
        return await self.get_all(
            filters={"is_active": True},
            order_by="relevance_score",
            desc=True,
        )
