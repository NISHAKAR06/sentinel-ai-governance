"""
base_repository.py — Generic async repository with full CRUD + pagination.
All repositories inherit from this class.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import Base
from app.core.exceptions import RecordNotFoundError
from app.core.logger import repo_logger

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository.
    Subclasses must set `model` class attribute.
    Only repositories interact with SQLAlchemy sessions directly.
    """

    model: Type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Create ────────────────────────────────────────────────
    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        repo_logger.debug("Created", extra={"model": self.model.__name__, "id": str(getattr(instance, "id", ""))})
        return instance

    async def bulk_create(self, records: List[Dict[str, Any]]) -> List[ModelT]:
        instances = [self.model(**r) for r in records]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    # ── Read ──────────────────────────────────────────────────
    async def get_by_id(self, record_id: Any) -> Optional[ModelT]:
        result = await self.session.get(self.model, record_id)
        return result

    async def get_by_id_or_raise(self, record_id: Any) -> ModelT:
        instance = await self.get_by_id(record_id)
        if instance is None:
            raise RecordNotFoundError(self.model.__name__, str(record_id))
        return instance

    async def get_by_field(self, field: str, value: Any) -> Optional[ModelT]:
        stmt = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = True,
    ) -> List[ModelT]:
        stmt = select(self.model)
        if filters:
            for field, value in filters.items():
                if value is not None:
                    stmt = stmt.where(getattr(self.model, field) == value)
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            stmt = stmt.order_by(col.desc() if desc else col.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "created_at",
        desc: bool = True,
    ) -> Tuple[List[ModelT], int]:
        """Return (items, total_count) for a given page."""
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    clause = getattr(self.model, field) == value
                    stmt       = stmt.where(clause)
                    count_stmt = count_stmt.where(clause)

        if hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            stmt = stmt.order_by(col.desc() if desc else col.asc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        items_result = await self.session.execute(stmt)
        count_result = await self.session.execute(count_stmt)

        items = list(items_result.scalars().all())
        total = count_result.scalar_one()
        return items, total

    # ── Update ────────────────────────────────────────────────
    async def update_by_id(self, record_id: Any, **data: Any) -> ModelT:
        instance = await self.get_by_id_or_raise(record_id)
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def bulk_update(self, filters: Dict[str, Any], **data: Any) -> int:
        stmt = update(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.values(**data)
        result = await self.session.execute(stmt)
        return result.rowcount

    # ── Delete ────────────────────────────────────────────────
    async def delete_by_id(self, record_id: Any) -> bool:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    # ── Utilities ─────────────────────────────────────────────
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, **kwargs: Any) -> bool:
        stmt = select(func.count()).select_from(self.model)
        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
