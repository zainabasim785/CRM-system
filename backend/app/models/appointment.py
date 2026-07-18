"""Appointment ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base
from app.models.enums import AppointmentStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.reminder import Reminder
    from app.models.user import User


class Appointment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_starts_at_status", "starts_at", "status"),
        Index("ix_appointments_attendee_email", "attendee_email"),
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    google_event_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    calendar_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="primary",
        server_default="primary",
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attendee_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    attendee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(
            AppointmentStatus,
            name="appointment_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
        server_default=AppointmentStatus.SCHEDULED.value,
        index=True,
    )

    user: Mapped[Optional[User]] = relationship(back_populates="appointments")
    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} status={self.status} starts_at={self.starts_at}>"
