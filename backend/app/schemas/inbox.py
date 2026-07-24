"""Inbox API schemas — escalated chats and staff reminders."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ConversationStatus, ReminderStatus
from app.schemas.common import ORMModel


class InboxMessagePreview(BaseModel):
    role: str
    content: str
    created_at: datetime


class InboxConversationItem(BaseModel):
    id: uuid.UUID
    session_id: str
    summary: str | None = None
    status: ConversationStatus
    extra_data: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime
    last_message: str | None = None


class InboxReminderItem(ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    session_id: str | None = None
    note: str
    remind_at: datetime
    status: ReminderStatus
    created_at: datetime
    updated_at: datetime


class InboxResponse(BaseModel):
    escalated: list[InboxConversationItem]
    reminders: list[InboxReminderItem]


class InboxConversationUpdate(BaseModel):
    status: ConversationStatus


class InboxReminderUpdate(BaseModel):
    status: ReminderStatus
