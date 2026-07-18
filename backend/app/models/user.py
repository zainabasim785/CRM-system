"""User ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.conversation import Conversation
    from app.models.reminder import Reminder


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=UserRole.CUSTOMER,
        server_default=UserRole.CUSTOMER.value,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # Per-user Google Calendar OAuth tokens (Web OAuth flow)
    google_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_token_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    appointments: Mapped[list[Appointment]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def google_calendar_connected(self) -> bool:
        return bool(self.google_refresh_token or self.google_access_token)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
