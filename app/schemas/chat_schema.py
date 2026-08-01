"""
chat_schema.py — Pydantic schemas for AI chat endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.action_schema import ActionPreview


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    department: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    action_preview: Optional[ActionPreview] = None
    requires_action: bool = False
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistoryResponse(BaseModel):
    items: List[ChatMessage]
    conversation_id: str
    total: int
