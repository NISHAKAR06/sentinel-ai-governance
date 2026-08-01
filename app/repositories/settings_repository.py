"""
settings_repository.py — Platform settings queries.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import PlatformSettings
from app.repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository[PlatformSettings]):
    model = PlatformSettings

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_key(self, key: str) -> Optional[PlatformSettings]:
        return await self.get_by_field("key", key)

    async def get_by_category(self, category: str) -> List[PlatformSettings]:
        stmt = (
            select(PlatformSettings)
            .where(PlatformSettings.category == category)
            .order_by(PlatformSettings.key)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, key: str, value: Any, category: str, updated_by: Optional[str] = None) -> PlatformSettings:
        existing = await self.get_by_key(key)
        if existing:
            return await self.update_by_id(
                existing.id, value=value, updated_by=updated_by
            )
        return await self.create(
            key=key, value=value, category=category, updated_by=updated_by
        )

    async def upsert_many(self, items: Dict[str, Any], category: str, updated_by: Optional[str] = None) -> None:
        for key, value in items.items():
            await self.upsert(key, value, category, updated_by=updated_by)

    async def get_value(self, key: str, default: Any = None) -> Any:
        item = await self.get_by_key(key)
        if item is None:
            return default
        # value is stored as JSONB dict {"v": <actual_value>}
        return item.value.get("v", default) if isinstance(item.value, dict) else item.value

    async def to_dict(self) -> Dict[str, Any]:
        """Return all settings as flat dict."""
        items = await self.get_all()
        result = {}
        for s in items:
            val = s.value.get("v") if isinstance(s.value, dict) and "v" in s.value else s.value
            result[s.key] = val
        return result
