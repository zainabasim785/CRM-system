"""Reminder schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReminderChannel, ReminderStatus
from app.schemas.common import ORMModel


class ReminderBase(BaseModel):
    remind_at: datetime
    note: str = Field(..., min_length=1)
    channel: ReminderChannel = ReminderChannel.INTERNAL
    status: ReminderStatus = ReminderStatus.SCHEDULED


class ReminderCreate(ReminderBase):
    conversation_id: uuid.UUID | None = None
    appointment_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


class ReminderUpdate(BaseModel):
    remind_at: datetime | None = None
    note: str | None = None
    channel: ReminderChannel | None = None
    status: ReminderStatus | None = None
    conversation_id: uuid.UUID | None = None
    appointment_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


class ReminderRead(ReminderBase, ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    appointment_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
