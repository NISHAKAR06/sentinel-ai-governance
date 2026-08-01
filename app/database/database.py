"""
database.py — SQLAlchemy async engine and declarative base.
Supports both PostgreSQL (production) and SQLite (local dev).
"""
from __future__ import annotations

import uuid
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData
from sqlalchemy.types import TypeDecorator, CHAR

from app.config import settings


# ── Cross-database UUID type ──────────────────────────────────
class GUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type, stores as CHAR(36) on SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            try:
                return str(uuid.UUID(str(value)))
            except ValueError:
                return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            try:
                return uuid.UUID(str(value))
            except ValueError:
                return value
        return value


# ── Cross-database JSON type ──────────────────────────────────
class JSONType(TypeDecorator):
    """Stores dicts/lists as JSON text on SQLite, uses JSONB on PostgreSQL."""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        from sqlalchemy import Text
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        import json
        return json.dumps(value, default=str)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (dict, list)):
            return value
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value


# ── Naming convention for Alembic autogenerate ────────────────
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    metadata = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        import re
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name


# ── Async engine (used at runtime) ───────────────────────────
def create_engine() -> AsyncEngine:
    url = settings.DATABASE_URL
    is_sqlite = url.startswith("sqlite")
    if is_sqlite:
        from sqlalchemy.pool import StaticPool
        return create_async_engine(
            url,
            echo=settings.DATABASE_ECHO,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_async_engine(
        url,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


engine: AsyncEngine = create_engine()
