"""
settings_schema.py — Pydantic schemas for platform settings.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SettingsPayload(BaseModel):
    theme: str = "light"
    language: str = "en"
    auto_threshold: int = Field(30, ge=0, le=100)
    confirm_threshold: int = Field(60, ge=0, le=100)
    review_threshold: int = Field(80, ge=0, le=100)
    notifications_enabled: bool = True
    notify_high_risk: bool = True
    notify_completion: bool = True
    notify_review: bool = True
    adaptive_learning: bool = True
    learning_rate: float = Field(0.1, ge=0.01, le=1.0)
    ws_url: Optional[str] = None
    ws_reconnect: bool = True
    ws_interval: int = Field(3000, ge=500)
    audit_retention: int = Field(90, ge=7, le=3650)
    audit_level: str = "standard"


class SettingsResponse(SettingsPayload):
    updated_by: Optional[str] = None


class SettingItem(BaseModel):
    key: str
    value: Any
    category: str
    description: Optional[str] = None


class SettingsListResponse(BaseModel):
    items: List[SettingItem]
    total: int
