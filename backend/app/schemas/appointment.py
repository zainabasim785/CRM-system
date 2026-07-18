"""Appointment schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import AppointmentStatus
from app.schemas.common import ORMModel


class AppointmentBase(BaseModel):
    summary: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    attendee_email: EmailStr | None = None
    attendee_name: str | None = Field(default=None, max_length=255)
    starts_at: datetime
    ends_at: datetime
    calendar_id: str = "primary"
    google_event_id: str | None = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


class AppointmentCreate(AppointmentBase):
    user_id: uuid.UUID | None = None


class AppointmentUpdate(BaseModel):
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    attendee_email: EmailStr | None = None
    attendee_name: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    calendar_id: str | None = None
    google_event_id: str | None = None
    status: AppointmentStatus | None = None
    user_id: uuid.UUID | None = None


class AppointmentRead(AppointmentBase, ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
