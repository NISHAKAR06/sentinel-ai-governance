"""
init_db.py — Create all tables and optionally seed the database.
Run directly:  python -m app.database.init_db
Or call init_db() from app startup.
"""
from __future__ import annotations

import asyncio
import sys

from app.database.database import engine, Base
from app.core.logger import get_logger

# Import all models so Base.metadata knows about them
import app.models.employee   # noqa: F401
import app.models.knowledge  # noqa: F401
import app.models.document   # noqa: F401
import app.models.review     # noqa: F401
import app.models.audit      # noqa: F401
import app.models.settings   # noqa: F401
import app.models.action     # noqa: F401

logger = get_logger("sentinel.init_db")


async def init_db(seed: bool = False) -> None:
    """Create all tables. Optionally run seeder."""
    async with engine.begin() as conn:
        logger.info("Creating database tables…")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created.")

    if seed:
        from app.database.seed import run_seed
        await run_seed()


async def drop_db() -> None:
    """Drop all tables (destructive — development only)."""
    async with engine.begin() as conn:
        logger.warning("Dropping ALL database tables…")
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All tables dropped.")


if __name__ == "__main__":
    seed_flag = "--seed" in sys.argv
    asyncio.run(init_db(seed=seed_flag))
