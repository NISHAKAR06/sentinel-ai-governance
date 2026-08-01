"""employee.py — Employee ORM model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base, GUID


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(20),  unique=True, nullable=False, index=True)
    username: Mapped[str]    = mapped_column(String(80),  unique=True, nullable=False, index=True)
    email: Mapped[str]       = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str]   = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str]        = mapped_column(String(50),  nullable=False, default="reviewer")
    department: Mapped[str]  = mapped_column(String(100), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str]       = mapped_column(String(20),  nullable=True)
    avatar_url: Mapped[str]  = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool]  = mapped_column(Boolean, default=True,  nullable=False)
    is_admin: Mapped[bool]   = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str]    = mapped_column(String(5),  default="en", nullable=False)
    timezone: Mapped[str]    = mapped_column(String(60), default="UTC", nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<Employee {self.username} ({self.role})>"
