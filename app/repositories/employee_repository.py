"""
employee_repository.py — Employee-specific queries.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.repositories.base_repository import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_username(self, username: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.employee_id == employee_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_department(self, department: str) -> List[Employee]:
        stmt = (
            select(Employee)
            .where(Employee.department == department, Employee.is_active == True)
            .order_by(Employee.full_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_reviewers(self) -> List[Employee]:
        stmt = (
            select(Employee)
            .where(Employee.is_active == True, Employee.role.in_(["reviewer", "admin", "superadmin"]))
            .order_by(Employee.full_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_admins(self) -> List[Employee]:
        stmt = (
            select(Employee)
            .where(Employee.is_admin == True, Employee.is_active == True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_last_login(self, employee_id: str) -> None:
        from datetime import datetime, timezone
        await self.bulk_update(
            {"employee_id": employee_id},
            last_login=datetime.now(timezone.utc),
        )

    async def count_by_department(self) -> List[dict]:
        stmt = (
            select(Employee.department, func.count(Employee.id).label("count"))
            .where(Employee.is_active == True)
            .group_by(Employee.department)
            .order_by(func.count(Employee.id).desc())
        )
        result = await self.session.execute(stmt)
        return [{"department": row[0], "count": row[1]} for row in result.all()]
