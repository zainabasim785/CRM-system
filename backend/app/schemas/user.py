"""User API / domain schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    phone: str | None = Field(default=None, max_length=32)
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(UserBase, ORMModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    google_calendar_connected: bool = False
