"""Conversation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ConversationStatus
from app.schemas.common import ORMModel


class ConversationBase(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    summary: str | None = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    extra_data: dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(ConversationBase):
    user_id: uuid.UUID | None = None


class ConversationUpdate(BaseModel):
    summary: str | None = None
    status: ConversationStatus | None = None
    extra_data: dict[str, Any] | None = None
    user_id: uuid.UUID | None = None


class ConversationRead(ConversationBase, ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
