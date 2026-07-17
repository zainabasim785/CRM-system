"""
Appointment booking service used by the Booking Agent.

Coordinates CalendarService (Google Calendar) with AppointmentRepository (DB).
Prevents double booking by checking both sources before confirm.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.models.user import User
from app.repositories.appointment import AppointmentRepository
from app.services.calendar_context import get_calendar_user_id
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

DEFAULT_SLOT_STEP = timedelta(minutes=30)
DEFAULT_SEARCH_WINDOW = timedelta(days=7)
DEFAULT_ALTERNATIVE_COUNT = 3


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    cleaned = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _format_range(starts_at: datetime, ends_at: datetime) -> str:
    start_local = starts_at.astimezone(UTC)
    end_local = ends_at.astimezone(UTC)
    if start_local.date() == end_local.date():
        return (
            f"{start_local.strftime('%A, %B %d, %Y')} from "
            f"{start_local.strftime('%H:%M')} to {end_local.strftime('%H:%M')} UTC"
        )
    return (
        f"{start_local.strftime('%A, %B %d, %Y %H:%M')} UTC to "
        f"{end_local.strftime('%A, %B %d, %Y %H:%M')} UTC"
    )


def _ranges_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and end_a > start_b


class AppointmentService:
    """Create / cancel / reschedule appointments in DB + Google Calendar."""

    def __init__(
        self,
        db: Session,
        *,
        calendar: CalendarService | None = None,
        user: User | None = None,
    ) -> None:
        self.db = db
        self.user = user
        self.appointments = AppointmentRepository(db)
        self.calendar = calendar or CalendarService(db=db, user=user)

    def book_appointment(
        self,
        summary: str,
        start: str,
        end: str,
        attendee_email: str | None = None,
        description: str | None = None,
        calendar_id: str = "primary",
        attendee_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Confirm a booking after availability checks.

        Checks Google Calendar and overlapping DB appointments first.
        If unavailable, returns the next three free slots instead of booking.
        """
        starts_at = _parse_datetime(start)
        ends_at = _parse_datetime(end)
        if ends_at <= starts_at:
            return {
                "success": False,
                "message": "End time must be after start time.",
                "summary": summary,
                "start": start,
                "end": end,
            }

        availability = self.check_slot_availability(
            starts_at=starts_at,
            ends_at=ends_at,
            calendar_id=calendar_id,
        )
        if not availability.get("available"):
            return self._unavailable_response(
                summary=summary,
                start=start,
                end=end,
                starts_at=starts_at,
                ends_at=ends_at,
                calendar_id=calendar_id,
                availability=availability,
            )

        calendar_result = self.calendar.create_appointment(
            summary=summary,
            start=start,
            end=end,
            attendee_email=attendee_email,
            description=description,
            calendar_id=calendar_id,
        )
        if not calendar_result.get("success"):
            return {
                "success": False,
                "configured": calendar_result.get("configured"),
                "connected": calendar_result.get("connected"),
                "summary": summary,
                "start": start,
                "end": end,
                "message": calendar_result.get("message")
                or "Could not create the Google Calendar event.",
            }

        event_id = calendar_result.get("event_id")
        user_id = self._resolve_user_id()

        try:
            appointment = self.appointments.create(
                user_id=user_id,
                google_event_id=event_id,
                calendar_id=calendar_id,
                summary=summary,
                description=description,
                attendee_email=attendee_email,
                attendee_name=attendee_name,
                starts_at=starts_at,
                ends_at=ends_at,
                status=AppointmentStatus.SCHEDULED,
            )
            self.db.commit()
            self.db.refresh(appointment)
        except Exception as exc:
            self.db.rollback()
            logger.exception("Failed to persist appointment after calendar create")
            if event_id:
                self.calendar.cancel_appointment(str(event_id), calendar_id)
            return {
                "success": False,
                "summary": summary,
                "start": start,
                "end": end,
                "event_id": event_id,
                "message": f"Calendar event created but saving the appointment failed: {exc}",
            }

        when = _format_range(appointment.starts_at, appointment.ends_at)
        confirmation = (
            f'Your appointment "{appointment.summary}" is confirmed for {when}.'
        )

        return {
            "success": True,
            "configured": True,
            "connected": True,
            "available": True,
            "appointment_id": str(appointment.id),
            "event_id": event_id,
            "google_event_id": event_id,
            "html_link": calendar_result.get("html_link"),
            "summary": appointment.summary,
            "description": appointment.description,
            "attendee_email": appointment.attendee_email,
            "start": start,
            "end": end,
            "starts_at": appointment.starts_at.isoformat(),
            "ends_at": appointment.ends_at.isoformat(),
            "calendar_id": appointment.calendar_id,
            "status": appointment.status.value,
            "confirmation": confirmation,
            "message": confirmation,
        }

    def check_slot_availability(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
        calendar_id: str = "primary",
        exclude_appointment_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Check Google Calendar free/busy and overlapping DB appointments."""
        google = self.calendar.check_availability(
            starts_at.isoformat(),
            ends_at.isoformat(),
            calendar_id,
        )
        if google.get("configured") is False or google.get("connected") is False:
            return {
                "available": False,
                "configured": google.get("configured"),
                "connected": google.get("connected"),
                "google_available": google.get("available"),
                "db_available": None,
                "conflicts": [],
                "message": google.get("message")
                or "Google Calendar is not available for availability checks.",
            }

        if google.get("available") is None and google.get("configured"):
            # API error while checking
            return {
                "available": False,
                "configured": True,
                "connected": True,
                "google_available": None,
                "db_available": None,
                "conflicts": [],
                "message": google.get("message") or "Failed to check Google availability.",
            }

        overlaps = self._db_overlaps(
            starts_at,
            ends_at,
            calendar_id=calendar_id,
            exclude_appointment_id=exclude_appointment_id,
        )
        google_available = bool(google.get("available"))
        db_available = len(overlaps) == 0
        available = google_available and db_available

        conflicts: list[dict[str, Any]] = []
        if not google_available:
            for busy in google.get("busy") or []:
                conflicts.append(
                    {
                        "source": "google_calendar",
                        "start": busy.get("start"),
                        "end": busy.get("end"),
                    }
                )
        for appointment in overlaps:
            conflicts.append(
                {
                    "source": "database",
                    "appointment_id": str(appointment.id),
                    "summary": appointment.summary,
                    "start": appointment.starts_at.isoformat(),
                    "end": appointment.ends_at.isoformat(),
                }
            )

        if available:
            message = f"Slot from {starts_at.isoformat()} to {ends_at.isoformat()} is free."
        elif not google_available and not db_available:
            message = "Requested time conflicts with Google Calendar and an existing appointment."
        elif not google_available:
            message = "Requested time is busy on Google Calendar."
        else:
            message = "Requested time overlaps an existing appointment in the database."

        return {
            "available": available,
            "configured": True,
            "connected": True,
            "google_available": google_available,
            "db_available": db_available,
            "conflicts": conflicts,
            "message": message,
            "requested_start": starts_at.isoformat(),
            "requested_end": ends_at.isoformat(),
            "calendar_id": calendar_id,
        }

    def suggest_next_available_slots(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
        calendar_id: str = "primary",
        count: int = DEFAULT_ALTERNATIVE_COUNT,
        exclude_appointment_id: UUID | None = None,
    ) -> list[dict[str, str]]:
        """Return up to `count` free slots of the same duration after `starts_at`."""
        duration = ends_at - starts_at
        if duration <= timedelta(0):
            return []

        step = min(duration, DEFAULT_SLOT_STEP)
        if step <= timedelta(0):
            step = DEFAULT_SLOT_STEP

        search_start = starts_at
        search_end = starts_at + DEFAULT_SEARCH_WINDOW
        busy_periods = self._collect_busy_periods(
            search_start,
            search_end,
            calendar_id=calendar_id,
            exclude_appointment_id=exclude_appointment_id,
        )

        suggestions: list[dict[str, str]] = []
        cursor = starts_at + step
        # Ensure we don't propose the original slot again
        while cursor + duration <= search_end and len(suggestions) < count:
            candidate_start = cursor
            candidate_end = cursor + duration
            if not any(
                _ranges_overlap(candidate_start, candidate_end, busy_start, busy_end)
                for busy_start, busy_end in busy_periods
            ):
                suggestions.append(
                    {
                        "start": candidate_start.isoformat(),
                        "end": candidate_end.isoformat(),
                        "label": _format_range(candidate_start, candidate_end),
                    }
                )
            cursor += step

        return suggestions

    def cancel_appointment(
        self,
        event_id: str | None = None,
        calendar_id: str = "primary",
        *,
        appointment_id: str | UUID | None = None,
    ) -> dict[str, Any]:
        """Cancel in Google Calendar and mark cancelled in the database."""
        appointment = self._resolve_appointment(
            event_id=event_id,
            appointment_id=appointment_id,
        )
        if appointment is None:
            return {
                "success": False,
                "event_id": event_id,
                "appointment_id": str(appointment_id) if appointment_id else None,
                "message": (
                    "Appointment not found. Provide a valid appointment_id or "
                    "Google event_id (or list appointments first)."
                ),
            }

        if appointment.status == AppointmentStatus.CANCELLED:
            return {
                "success": True,
                "appointment_id": str(appointment.id),
                "event_id": appointment.google_event_id,
                "status": AppointmentStatus.CANCELLED.value,
                "message": f'Appointment "{appointment.summary}" was already cancelled.',
            }

        google_event_id = appointment.google_event_id or event_id
        cal_id = appointment.calendar_id or calendar_id

        if google_event_id:
            calendar_result = self.calendar.cancel_appointment(google_event_id, cal_id)
            if not calendar_result.get("success"):
                # Still allow DB cancel if Google is simply not connected.
                if calendar_result.get("configured") is not False and calendar_result.get(
                    "connected"
                ) is not False:
                    return {
                        "success": False,
                        "appointment_id": str(appointment.id),
                        "event_id": google_event_id,
                        "message": calendar_result.get("message")
                        or "Failed to cancel the Google Calendar event.",
                    }

        self.appointments.cancel(appointment)
        self.db.commit()
        self.db.refresh(appointment)

        when = _format_range(appointment.starts_at, appointment.ends_at)
        return {
            "success": True,
            "appointment_id": str(appointment.id),
            "event_id": google_event_id,
            "google_event_id": google_event_id,
            "summary": appointment.summary,
            "starts_at": appointment.starts_at.isoformat(),
            "ends_at": appointment.ends_at.isoformat(),
            "status": AppointmentStatus.CANCELLED.value,
            "message": f'Appointment "{appointment.summary}" on {when} has been cancelled.',
        }

    def reschedule_appointment(
        self,
        event_id: str | None = None,
        new_start: str | None = None,
        new_end: str | None = None,
        calendar_id: str = "primary",
        *,
        appointment_id: str | UUID | None = None,
    ) -> dict[str, Any]:
        """Reschedule in Google Calendar and update the database row."""
        if not new_start or not new_end:
            return {
                "success": False,
                "message": "new_start and new_end are required to reschedule.",
            }

        starts_at = _parse_datetime(new_start)
        ends_at = _parse_datetime(new_end)
        if ends_at <= starts_at:
            return {
                "success": False,
                "event_id": event_id,
                "appointment_id": str(appointment_id) if appointment_id else None,
                "message": "End time must be after start time.",
            }

        appointment = self._resolve_appointment(
            event_id=event_id,
            appointment_id=appointment_id,
        )
        if appointment is None:
            return {
                "success": False,
                "event_id": event_id,
                "appointment_id": str(appointment_id) if appointment_id else None,
                "message": (
                    "Appointment not found. Provide a valid appointment_id or "
                    "Google event_id (or list appointments first)."
                ),
            }

        if appointment.status == AppointmentStatus.CANCELLED:
            return {
                "success": False,
                "appointment_id": str(appointment.id),
                "event_id": appointment.google_event_id,
                "message": "Cannot reschedule a cancelled appointment.",
            }

        google_event_id = appointment.google_event_id or event_id
        cal_id = appointment.calendar_id or calendar_id
        exclude_id = appointment.id

        availability = self.check_slot_availability(
            starts_at=starts_at,
            ends_at=ends_at,
            calendar_id=cal_id,
            exclude_appointment_id=exclude_id,
        )
        if not availability.get("available"):
            alternatives = self.suggest_next_available_slots(
                starts_at=starts_at,
                ends_at=ends_at,
                calendar_id=cal_id,
                exclude_appointment_id=exclude_id,
            )
            labels = [slot["label"] for slot in alternatives]
            message = availability.get("message") or "Requested time is unavailable."
            if labels:
                message = (
                    f"{message} Next available options: "
                    + "; ".join(labels)
                    + "."
                )
            return {
                "success": False,
                "available": False,
                "appointment_id": str(appointment.id),
                "event_id": google_event_id,
                "new_start": new_start,
                "new_end": new_end,
                "alternative_slots": alternatives,
                "conflicts": availability.get("conflicts") or [],
                "message": message,
            }

        if google_event_id:
            calendar_result = self.calendar.reschedule_appointment(
                event_id=google_event_id,
                new_start=new_start,
                new_end=new_end,
                calendar_id=cal_id,
            )
            if not calendar_result.get("success"):
                return {
                    "success": False,
                    "appointment_id": str(appointment.id),
                    "event_id": google_event_id,
                    "new_start": new_start,
                    "new_end": new_end,
                    "message": calendar_result.get("message")
                    or "Failed to reschedule the Google Calendar event.",
                }
        else:
            calendar_result = {"success": True, "event_id": None}

        self.appointments.reschedule(
            appointment,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        self.db.commit()
        self.db.refresh(appointment)
        when = _format_range(appointment.starts_at, appointment.ends_at)
        confirmation = (
            f'Appointment "{appointment.summary}" was rescheduled to {when}.'
        )
        return {
            "success": True,
            "available": True,
            "appointment_id": str(appointment.id),
            "event_id": google_event_id,
            "google_event_id": google_event_id,
            "summary": appointment.summary,
            "new_start": new_start,
            "new_end": new_end,
            "starts_at": appointment.starts_at.isoformat(),
            "ends_at": appointment.ends_at.isoformat(),
            "status": appointment.status.value,
            "confirmation": confirmation,
            "message": confirmation,
        }

    def list_appointments(
        self,
        *,
        attendee_email: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """List upcoming (non-cancelled) appointments for lookup before cancel/reschedule."""
        after = datetime.now(UTC)
        user_id = self._resolve_user_id()
        rows = self.appointments.list_upcoming(
            user_id=user_id,
            attendee_email=attendee_email.lower() if attendee_email else None,
            after=after,
            limit=limit,
        )
        items = [
            {
                "appointment_id": str(row.id),
                "event_id": row.google_event_id,
                "summary": row.summary,
                "attendee_email": row.attendee_email,
                "starts_at": row.starts_at.isoformat(),
                "ends_at": row.ends_at.isoformat(),
                "status": row.status.value,
                "label": _format_range(row.starts_at, row.ends_at),
            }
            for row in rows
        ]
        return {
            "success": True,
            "count": len(items),
            "appointments": items,
            "message": (
                f"Found {len(items)} upcoming appointment(s)."
                if items
                else "No upcoming appointments found."
            ),
        }

    def _resolve_appointment(
        self,
        *,
        event_id: str | None = None,
        appointment_id: str | UUID | None = None,
    ) -> Appointment | None:
        if appointment_id:
            try:
                appt_uuid = (
                    appointment_id
                    if isinstance(appointment_id, UUID)
                    else UUID(str(appointment_id))
                )
            except ValueError:
                return None
            found = self.appointments.get(appt_uuid)
            if found is not None:
                return found
        if event_id:
            return self.appointments.get_by_google_event_id(event_id)
        return None

    def _unavailable_response(
        self,
        *,
        summary: str,
        start: str,
        end: str,
        starts_at: datetime,
        ends_at: datetime,
        calendar_id: str,
        availability: dict[str, Any],
    ) -> dict[str, Any]:
        alternatives = self.suggest_next_available_slots(
            starts_at=starts_at,
            ends_at=ends_at,
            calendar_id=calendar_id,
        )
        labels = [slot["label"] for slot in alternatives]
        base_message = availability.get("message") or "Requested time is unavailable."
        if labels:
            message = (
                f"{base_message} Next available options: "
                + "; ".join(labels)
                + "."
            )
        else:
            message = (
                f"{base_message} No alternative slots were found in the next "
                f"{int(DEFAULT_SEARCH_WINDOW.total_seconds() // 86400)} days."
            )

        return {
            "success": False,
            "available": False,
            "configured": availability.get("configured", True),
            "connected": availability.get("connected", True),
            "summary": summary,
            "start": start,
            "end": end,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "calendar_id": calendar_id,
            "conflicts": availability.get("conflicts") or [],
            "alternative_slots": alternatives,
            "message": message,
        }

    def _db_overlaps(
        self,
        starts_at: datetime,
        ends_at: datetime,
        *,
        calendar_id: str,
        exclude_appointment_id: UUID | None = None,
    ) -> list[Appointment]:
        overlaps = self.appointments.list_in_range(
            starts_at,
            ends_at,
            calendar_id=calendar_id,
        )
        if exclude_appointment_id is None:
            return overlaps
        return [item for item in overlaps if item.id != exclude_appointment_id]

    def _collect_busy_periods(
        self,
        search_start: datetime,
        search_end: datetime,
        *,
        calendar_id: str,
        exclude_appointment_id: UUID | None = None,
    ) -> list[tuple[datetime, datetime]]:
        periods: list[tuple[datetime, datetime]] = []

        google = self.calendar.check_availability(
            search_start.isoformat(),
            search_end.isoformat(),
            calendar_id,
        )
        for busy in google.get("busy") or []:
            try:
                periods.append(
                    (
                        _parse_datetime(str(busy["start"])),
                        _parse_datetime(str(busy["end"])),
                    )
                )
            except (KeyError, TypeError, ValueError):
                logger.warning("Skipping malformed Google busy period: %s", busy)

        for appointment in self.appointments.list_in_range(
            search_start,
            search_end,
            calendar_id=calendar_id,
        ):
            if exclude_appointment_id is not None and appointment.id == exclude_appointment_id:
                continue
            periods.append((appointment.starts_at, appointment.ends_at))

        return periods

    def _resolve_user_id(self) -> UUID | None:
        if self.user is not None:
            return self.user.id
        return get_calendar_user_id()
