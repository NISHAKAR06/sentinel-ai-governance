"""
audit_repository.py — Audit log queries and analytics.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, desc, cast, Date, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_action_id(self, action_id: uuid.UUID) -> List[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.action_id == action_id)
            .order_by(AuditLog.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        query: Optional[str] = None,
        risk_level: Optional[str] = None,
        outcome: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AuditLog], int]:
        filters = []
        if query:
            q = f"%{query}%"
            filters.append(
                (AuditLog.action.ilike(q)) |
                (AuditLog.resource.ilike(q)) |
                (AuditLog.actor.ilike(q))
            )
        if risk_level:
            filters.append(AuditLog.risk_level == risk_level)
        if outcome:
            filters.append(AuditLog.outcome == outcome)
        if date_from:
            filters.append(AuditLog.timestamp >= date_from)
        if date_to:
            filters.append(AuditLog.timestamp <= date_to)

        base = select(AuditLog)
        count_q = select(func.count()).select_from(AuditLog)
        if filters:
            where = and_(*filters)
            base    = base.where(where)
            count_q = count_q.where(where)

        offset = (page - 1) * page_size
        base = base.order_by(desc(AuditLog.timestamp)).offset(offset).limit(page_size)

        items   = list((await self.session.execute(base)).scalars().all())
        total   = (await self.session.execute(count_q)).scalar_one()
        return items, total

    async def get_recent(self, limit: int = 10) -> List[AuditLog]:
        stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def risk_distribution(self, days: int = 30) -> Dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(AuditLog.risk_level, func.count(AuditLog.id).label("cnt"))
            .where(AuditLog.timestamp >= cutoff)
            .group_by(AuditLog.risk_level)
        )
        result = await self.session.execute(stmt)
        mapping = {row[0]: row[1] for row in result.all()}
        return {
            "low":      mapping.get("low", 0),
            "medium":   mapping.get("medium", 0),
            "high":     mapping.get("high", 0),
            "critical": mapping.get("critical", 0),
        }

    async def daily_counts(self, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        from sqlalchemy import text
        from app.config import settings as app_settings

        if app_settings.DATABASE_URL.startswith("sqlite"):
            stmt = text("""
                SELECT
                    strftime('%Y-%m-%d', timestamp) as day,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome='approved' THEN 1 ELSE 0 END) as auto,
                    SUM(CASE WHEN outcome='reviewed' THEN 1 ELSE 0 END) as reviewed,
                    SUM(CASE WHEN outcome='rejected' THEN 1 ELSE 0 END) as rejected
                FROM audit_logs
                WHERE timestamp >= :cutoff
                GROUP BY strftime('%Y-%m-%d', timestamp)
                ORDER BY day
            """)
            result = await self.session.execute(stmt, {"cutoff": cutoff.isoformat()})
        else:
            stmt = (
                select(
                    cast(AuditLog.timestamp, Date).label("day"),
                    func.count(AuditLog.id).label("total"),
                    func.sum(func.cast(AuditLog.outcome == "approved", type_=Integer)).label("auto"),
                    func.sum(func.cast(AuditLog.outcome == "reviewed", type_=Integer)).label("reviewed"),
                    func.sum(func.cast(AuditLog.outcome == "rejected", type_=Integer)).label("rejected"),
                )
                .where(AuditLog.timestamp >= cutoff)
                .group_by(cast(AuditLog.timestamp, Date))
                .order_by(cast(AuditLog.timestamp, Date))
            )
            result = await self.session.execute(stmt)
        return [
            {
                "day":      str(row[0]),
                "total":    row[1],
                "auto":     int(row[2] or 0),
                "reviewed": int(row[3] or 0),
                "rejected": int(row[4] or 0),
            }
            for row in result.all()
        ]

    async def top_operations(self, days: int = 30, limit: int = 8) -> List[Dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(AuditLog.event_type, func.count(AuditLog.id).label("cnt"))
            .where(AuditLog.timestamp >= cutoff)
            .group_by(AuditLog.event_type)
            .order_by(func.count(AuditLog.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [{"operation": row[0], "count": row[1]} for row in result.all()]

    async def hourly_counts_today(self) -> List[int]:
        """Return a list of 24 ints (requests per hour, today UTC)."""
        today = datetime.now(timezone.utc).date()
        from sqlalchemy import text
        from app.config import settings as app_settings
        if app_settings.DATABASE_URL.startswith("sqlite"):
            stmt = text("""
                SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
                FROM audit_logs
                WHERE date(timestamp) = :today
                GROUP BY strftime('%H', timestamp)
            """)
            result = await self.session.execute(stmt, {"today": str(today)})
        else:
            stmt = (
                select(
                    func.extract("hour", AuditLog.timestamp).label("hour"),
                    func.count(AuditLog.id).label("cnt"),
                )
                .where(cast(AuditLog.timestamp, Date) == today)
                .group_by(func.extract("hour", AuditLog.timestamp))
            )
            result = await self.session.execute(stmt)
        hourly = {int(row[0]): row[1] for row in result.all()}
        return [hourly.get(h, 0) for h in range(24)]

    async def avg_risk_score(self, days: int = 30) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(func.avg(AuditLog.risk_score)).where(AuditLog.timestamp >= cutoff)
        result = await self.session.execute(stmt)
        val = result.scalar_one()
        return round(float(val or 0.0), 1)

    async def outcome_counts(self, days: int = 7) -> Dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(AuditLog.outcome, func.count(AuditLog.id))
            .where(AuditLog.timestamp >= cutoff)
            .group_by(AuditLog.outcome)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def delete_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        from sqlalchemy import delete as sa_delete
        stmt = sa_delete(AuditLog).where(AuditLog.timestamp < cutoff)
        result = await self.session.execute(stmt)
        return result.rowcount
