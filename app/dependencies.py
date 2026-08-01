"""
dependencies.py — FastAPI dependency injection providers.
"""
from __future__ import annotations

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorisationError, to_http_exception
from app.core.security import decode_access_token, extract_token
from app.database.session import AsyncSessionLocal
from app.core.logger import get_logger

logger = get_logger("sentinel.deps")


# ── Database session ──────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session; commit on success, rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Auth helpers ──────────────────────────────────────────────
def _parse_bearer(authorization: Optional[str]) -> Optional[dict]:
    if not authorization:
        return None
    try:
        token   = extract_token(authorization)
        payload = decode_access_token(token)
        return payload
    except Exception:
        return None


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> dict:
    """Require a valid JWT. Returns decoded payload."""
    payload = _parse_bearer(authorization)
    if payload is None:
        raise to_http_exception(AuthenticationError("Missing or invalid Authorization header"))
    return payload


async def get_optional_user(
    authorization: Optional[str] = Header(default=None),
) -> Optional[dict]:
    """Return decoded JWT payload or None (unauthenticated access allowed)."""
    return _parse_bearer(authorization)


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require the current user to have the 'admin' role."""
    if current_user.get("role") not in ("admin", "superadmin"):
        raise to_http_exception(AuthorisationError("Admin role required"))
    return current_user


# ── Repository convenience factories ─────────────────────────
# These are imported where needed to avoid circular imports.
# Usage in routers:
#   from app.dependencies import get_db
#   from app.repositories.employee_repository import EmployeeRepository
#   db: AsyncSession = Depends(get_db)
#   repo = EmployeeRepository(db)
