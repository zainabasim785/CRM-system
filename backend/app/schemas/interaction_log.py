"""InteractionLog schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import InteractionRole
from app.schemas.common import ORMModel


class InteractionLogBase(BaseModel):
    role: InteractionRole
    content: str = Field(..., min_length=1)
    intent: str | None = Field(default=None, max_length=64)
    agent_name: str | None = Field(default=None, max_length=64)
    extra_data: dict[str, Any] = Field(default_factory=dict)


class InteractionLogCreate(InteractionLogBase):
    conversation_id: uuid.UUID


class InteractionLogRead(InteractionLogBase, ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
