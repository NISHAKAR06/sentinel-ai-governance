"""
settings_routes.py — GET /settings  PUT /settings  GET /settings/{key}
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings_schema import SettingsPayload, SettingsResponse
from app.core.logger import api_logger

router = APIRouter()

# Default settings keys
_DEFAULTS = {
    "theme":                   "light",
    "language":                "en",
    "auto_threshold":          30,
    "confirm_threshold":       60,
    "review_threshold":        80,
    "notifications_enabled":   True,
    "notify_high_risk":        True,
    "notify_completion":       True,
    "notify_review":           True,
    "adaptive_learning":       True,
    "learning_rate":           0.1,
    "ws_url":                  "ws://localhost:8000/ws",
    "ws_reconnect":            True,
    "ws_interval":             3000,
    "audit_retention":         90,
    "audit_level":             "standard",
}


@router.get("", response_model=SettingsResponse, summary="Get all platform settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo = SettingsRepository(db)
    data = await repo.to_dict()
    # Merge with defaults for any missing keys
    merged = {**_DEFAULTS, **data}
    return SettingsResponse(**{k: merged.get(k, v) for k, v in _DEFAULTS.items()})


@router.put("", response_model=SettingsResponse, summary="Save platform settings")
async def save_settings(
    payload: SettingsPayload,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo       = SettingsRepository(db)
    updated_by = current_user.get("sub", "system") if current_user else "system"
    items      = payload.model_dump()

    for key, value in items.items():
        await repo.upsert(key, {"v": value}, category="platform", updated_by=updated_by)

    api_logger.info("Settings saved", extra={"by": updated_by})

    # Also update runtime config thresholds
    from app.config import settings as app_settings
    if hasattr(payload, "auto_threshold"):
        app_settings.AUTO_APPROVE_THRESHOLD = payload.auto_threshold
    if hasattr(payload, "confirm_threshold"):
        app_settings.CONFIRM_THRESHOLD = payload.confirm_threshold
    if hasattr(payload, "review_threshold"):
        app_settings.HUMAN_REVIEW_THRESHOLD = payload.review_threshold
    if hasattr(payload, "learning_rate"):
        app_settings.LEARNING_RATE = payload.learning_rate
    if hasattr(payload, "adaptive_learning"):
        app_settings.LEARNING_ENABLED = payload.adaptive_learning

    return SettingsResponse(**items, updated_by=updated_by)


@router.get("/{key}", summary="Get a single setting by key")
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    repo  = SettingsRepository(db)
    value = await repo.get_value(key, _DEFAULTS.get(key))
    return {"key": key, "value": value}
