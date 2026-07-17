"""Google Calendar tools for the Booking Agent."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Iterator, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.core.database import SessionLocal
from app.models.user import User
from app.services.appointment_service import AppointmentService
from app.services.calendar_context import get_calendar_user_id
from app.services.calendar_service import CalendarService


@contextmanager
def appointment_service_session() -> Iterator[AppointmentService]:
    """DB + CalendarService bound to the current calendar user context."""
    user_id = get_calendar_user_id()
    db = SessionLocal()
    try:
        user = db.get(User, user_id) if user_id is not None else None
        calendar = CalendarService(db=db, user=user)
        yield AppointmentService(db=db, calendar=calendar, user=user)
    finally:
        db.close()


class AvailabilityInput(BaseModel):
    start: str = Field(..., description="Requested start datetime in ISO-8601 format")
    end: str = Field(..., description="Requested end datetime in ISO-8601 format")
    calendar_id: str = Field(default="primary", description="Google Calendar ID")


class CheckAvailabilityTool(BaseTool):
    name: str = "check_calendar_availability"
    description: str = (
        "Check whether a time range is free on Google Calendar and in the "
        "appointments database before booking."
    )
    args_schema: Type[BaseModel] = AvailabilityInput

    def _run(self, start: str, end: str, calendar_id: str = "primary") -> str:
        from app.services.appointment_service import _parse_datetime

        with appointment_service_session() as appointments:
            starts_at = _parse_datetime(start)
            ends_at = _parse_datetime(end)
            result = appointments.check_slot_availability(
                starts_at=starts_at,
                ends_at=ends_at,
                calendar_id=calendar_id,
            )
            if not result.get("available"):
                result["alternative_slots"] = appointments.suggest_next_available_slots(
                    starts_at=starts_at,
                    ends_at=ends_at,
                    calendar_id=calendar_id,
                )
        return json.dumps(result)


class CreateAppointmentInput(BaseModel):
    summary: str = Field(..., description="Appointment title / purpose")
    start: str = Field(..., description="Start datetime in ISO-8601 format")
    end: str = Field(..., description="End datetime in ISO-8601 format")
    attendee_email: str | None = Field(
        default=None, description="Guest email address if available"
    )
    description: str | None = Field(default=None, description="Optional notes")
    calendar_id: str = Field(default="primary", description="Google Calendar ID")


class CreateAppointmentTool(BaseTool):
    name: str = "create_appointment"
    description: str = (
        "Confirm a booking after checking Google Calendar and database availability. "
        "Creates the Google event, saves the appointment (with google event id), and "
        "returns a confirmation with date/time. If the slot is taken, returns the "
        "next three available slots instead."
    )
    args_schema: Type[BaseModel] = CreateAppointmentInput

    def _run(
        self,
        summary: str,
        start: str,
        end: str,
        attendee_email: str | None = None,
        description: str | None = None,
        calendar_id: str = "primary",
    ) -> str:
        with appointment_service_session() as appointments:
            result = appointments.book_appointment(
                summary=summary,
                start=start,
                end=end,
                attendee_email=attendee_email,
                description=description,
                calendar_id=calendar_id,
            )
        return json.dumps(result)


class CancelAppointmentInput(BaseModel):
    appointment_id: str | None = Field(
        default=None,
        description="Database appointment UUID (preferred when known)",
    )
    event_id: str | None = Field(
        default=None,
        description="Google Calendar event ID (used if appointment_id is unknown)",
    )
    calendar_id: str = Field(default="primary", description="Google Calendar ID")


class CancelAppointmentTool(BaseTool):
    name: str = "cancel_appointment"
    description: str = (
        "Cancel an appointment by appointment_id or Google event_id. "
        "Removes/cancels the Google Calendar event and marks the DB row cancelled."
    )
    args_schema: Type[BaseModel] = CancelAppointmentInput

    def _run(
        self,
        appointment_id: str | None = None,
        event_id: str | None = None,
        calendar_id: str = "primary",
    ) -> str:
        with appointment_service_session() as appointments:
            result = appointments.cancel_appointment(
                event_id=event_id,
                calendar_id=calendar_id,
                appointment_id=appointment_id,
            )
        return json.dumps(result)


class RescheduleAppointmentInput(BaseModel):
    new_start: str = Field(..., description="New start datetime in ISO-8601 format")
    new_end: str = Field(..., description="New end datetime in ISO-8601 format")
    appointment_id: str | None = Field(
        default=None,
        description="Database appointment UUID (preferred when known)",
    )
    event_id: str | None = Field(
        default=None,
        description="Google Calendar event ID (used if appointment_id is unknown)",
    )
    calendar_id: str = Field(default="primary", description="Google Calendar ID")


class RescheduleAppointmentTool(BaseTool):
    name: str = "reschedule_appointment"
    description: str = (
        "Reschedule an appointment by appointment_id or Google event_id. "
        "Checks availability, updates Google Calendar and the database together. "
        "If the new slot is taken, returns the next three available slots."
    )
    args_schema: Type[BaseModel] = RescheduleAppointmentInput

    def _run(
        self,
        new_start: str,
        new_end: str,
        appointment_id: str | None = None,
        event_id: str | None = None,
        calendar_id: str = "primary",
    ) -> str:
        with appointment_service_session() as appointments:
            result = appointments.reschedule_appointment(
                event_id=event_id,
                new_start=new_start,
                new_end=new_end,
                calendar_id=calendar_id,
                appointment_id=appointment_id,
            )
        return json.dumps(result)


class ListAppointmentsInput(BaseModel):
    attendee_email: str | None = Field(
        default=None,
        description="Optional attendee email to filter appointments",
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max appointments to return")


class ListAppointmentsTool(BaseTool):
    name: str = "list_appointments"
    description: str = (
        "List upcoming appointments (with appointment_id and event_id) so you can "
        "cancel or reschedule the correct one."
    )
    args_schema: Type[BaseModel] = ListAppointmentsInput

    def _run(
        self,
        attendee_email: str | None = None,
        limit: int = 10,
    ) -> str:
        with appointment_service_session() as appointments:
            result = appointments.list_appointments(
                attendee_email=attendee_email,
                limit=limit,
            )
        return json.dumps(result)


def get_booking_tools() -> list[BaseTool]:
    return [
        CheckAvailabilityTool(),
        CreateAppointmentTool(),
        ListAppointmentsTool(),
        CancelAppointmentTool(),
        RescheduleAppointmentTool(),
    ]
