"""Appointment repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    model = Appointment

    def get_by_google_event_id(self, google_event_id: str) -> Appointment | None:
        stmt = select(Appointment).where(Appointment.google_event_id == google_event_id)
        return self.db.scalars(stmt).first()

    def list_upcoming(
        self,
        *,
        user_id: uuid.UUID | None = None,
        attendee_email: str | None = None,
        after: datetime | None = None,
        limit: int = 10,
    ) -> list[Appointment]:
        stmt = select(Appointment).where(
            Appointment.status.notin_(
                (AppointmentStatus.CANCELLED,)
            )
        )
        if user_id is not None:
            stmt = stmt.where(Appointment.user_id == user_id)
        if attendee_email is not None:
            stmt = stmt.where(Appointment.attendee_email == attendee_email.lower())
        if after is not None:
            stmt = stmt.where(Appointment.starts_at >= after)
        stmt = stmt.order_by(Appointment.starts_at.asc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.user_id == user_id)
            .order_by(Appointment.starts_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_accessible(
        self,
        *,
        user_id: uuid.UUID | None = None,
        attendee_email: str | None = None,
        staff_view: bool = False,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = False,
    ) -> list[Appointment]:
        """List appointments for dashboard — staff see all; customers see their own."""
        stmt = select(Appointment)
        if not staff_view:
            filters = []
            if user_id is not None:
                filters.append(Appointment.user_id == user_id)
            if attendee_email:
                filters.append(
                    Appointment.attendee_email == attendee_email.lower()
                )
            if filters:
                from sqlalchemy import or_

                stmt = stmt.where(or_(*filters))
            else:
                return []
        if upcoming_only:
            stmt = stmt.where(Appointment.starts_at >= datetime.now(UTC))
        stmt = (
            stmt.order_by(Appointment.starts_at.asc() if upcoming_only else Appointment.starts_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_in_range(
        self,
        starts_at: datetime,
        ends_at: datetime,
        *,
        calendar_id: str = "primary",
        exclude_statuses: tuple[AppointmentStatus, ...] | None = None,
    ) -> list[Appointment]:
        excluded = exclude_statuses or (AppointmentStatus.CANCELLED,)
        stmt = (
            select(Appointment)
            .where(
                and_(
                    Appointment.calendar_id == calendar_id,
                    Appointment.starts_at < ends_at,
                    Appointment.ends_at > starts_at,
                    Appointment.status.notin_(excluded),
                )
            )
            .order_by(Appointment.starts_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def cancel(self, appointment: Appointment) -> Appointment:
        return self.update(appointment, status=AppointmentStatus.CANCELLED)

    def reschedule(
        self,
        appointment: Appointment,
        *,
        starts_at: datetime,
        ends_at: datetime,
        google_event_id: str | None = None,
    ) -> Appointment:
        payload: dict = {
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": AppointmentStatus.RESCHEDULED,
        }
        if google_event_id is not None:
            payload["google_event_id"] = google_event_id
        return self.update(appointment, **payload)
