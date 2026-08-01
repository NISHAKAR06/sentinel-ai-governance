"""
document_repository.py — Document queries.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search(self, query: str, limit: int = 10) -> List[Document]:
        q = f"%{query}%"
        stmt = (
            select(Document)
            .where(
                Document.is_active == True,
                or_(Document.title.ilike(q), Document.description.ilike(q)),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_department(self, department: str) -> List[Document]:
        stmt = (
            select(Document)
            .where(Document.department == department, Document.is_active == True)
            .order_by(Document.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_confidential(self) -> List[Document]:
        return await self.get_all(
            filters={"is_confidential": True, "is_active": True},
            order_by="updated_at",
        )
