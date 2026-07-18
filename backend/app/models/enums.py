"""Domain enumerations persisted as PostgreSQL / SQLAlchemy enums."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"
    CUSTOMER = "customer"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ESCALATED = "escalated"


class InteractionRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class ReminderChannel(str, enum.Enum):
    INTERNAL = "internal"
    EMAIL = "email"
    SMS = "sms"


class ReminderStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"
