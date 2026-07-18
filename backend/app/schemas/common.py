"""Shared Pydantic schema helpers."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema that reads attributes from SQLAlchemy ORM instances."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(ORMModel):
    created_at: datetime
    updated_at: datetime


class UUIDSchema(ORMModel):
    id: uuid.UUID
