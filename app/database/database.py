"""
database.py — SQLAlchemy async engine and declarative base.
Supports both PostgreSQL (production) and SQLite (local dev).
"""
from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import String
from sqlalchemy.engine import make_url
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
    raw_url = settings.DATABASE_URL
    if raw_url.startswith("postgres://") and not raw_url.startswith("postgresql+"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    url = make_url(raw_url)
    is_sqlite = raw_url.startswith("sqlite")
    if is_sqlite:
        from sqlalchemy.pool import StaticPool
        return create_async_engine(
            raw_url,
            echo=settings.DATABASE_ECHO,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    connect_args: dict[str, Any] = {}
    if url.drivername == "postgresql+asyncpg":
        ssl_val = None
        if url.query.get("sslmode"):
            ssl_val = url.query["sslmode"]
        elif url.query.get("ssl"):
            ssl_val = url.query["ssl"]
            if isinstance(ssl_val, str) and ssl_val.lower() in {"true", "1", "yes"}:
                ssl_val = "require"
        if ssl_val:
            connect_args["ssl"] = ssl_val
        # Remove asyncpg-specific query args not supported by asyncpg.connect()
        if url.query:
            filtered_query = {k: v for k, v in url.query.items() if k not in ["sslmode", "ssl", "channel_binding"]}
            url = url.set(query=filtered_query)

    return create_async_engine(
        url,
        echo=settings.DATABASE_ECHO,
        connect_args=connect_args or None,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


import os

# When running Alembic migrations we import the migrations `env.py` which may
# want to import `app.database`. Creating an async engine at import time can
# cause problems for migrations (imports require a sync driver). To avoid this
# when running migrations, set the environment variable
# `ALEMBIC_DISABLE_ENGINE=true` so the engine is not created here.
engine: AsyncEngine | None
if os.getenv("ALEMBIC_DISABLE_ENGINE", "false").lower() == "true":
    engine = None
else:
    engine = create_engine()
