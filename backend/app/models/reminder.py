"""Reminder ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base
from app.models.enums import ReminderChannel, ReminderStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.conversation import Conversation
    from app.models.user import User


class Reminder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_remind_at_status", "remind_at", "status"),
    )

    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[ReminderChannel] = mapped_column(
        Enum(
            ReminderChannel,
            name="reminder_channel",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ReminderChannel.INTERNAL,
        server_default=ReminderChannel.INTERNAL.value,
    )
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(
            ReminderStatus,
            name="reminder_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=ReminderStatus.SCHEDULED,
        server_default=ReminderStatus.SCHEDULED.value,
        index=True,
    )

    conversation: Mapped[Optional[Conversation]] = relationship(back_populates="reminders")
    appointment: Mapped[Optional[Appointment]] = relationship(back_populates="reminders")
    user: Mapped[Optional[User]] = relationship(back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} status={self.status} remind_at={self.remind_at}>"
