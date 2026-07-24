"""Appointment listing for the staff dashboard (PostgreSQL only — no paid APIs)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.models.enums import UserRole
from app.repositories.appointment import AppointmentRepository
from app.schemas.appointment import AppointmentListResponse, AppointmentRead

router = APIRouter(prefix="/appointments", tags=["appointments"])

_STAFF_ROLES = {UserRole.ADMIN, UserRole.RECEPTIONIST}


@router.get(
    "",
    response_model=AppointmentListResponse,
    summary="List appointments for the signed-in user",
)
def list_appointments(
    current_user: CurrentUser,
    db: DbSession,
    upcoming_only: bool = Query(
        default=False,
        description="When true, return only future appointments (soonest first).",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
) -> AppointmentListResponse:
    """
    Staff (admin/receptionist) or users with a connected calendar see all bookings.

    Customers only see appointments linked to their account or attendee email.
    """
    repo = AppointmentRepository(db)
    staff_view = (
        current_user.role in _STAFF_ROLES
        or current_user.google_calendar_connected
    )
    items = repo.list_accessible(
        user_id=current_user.id,
        attendee_email=str(current_user.email),
        staff_view=staff_view,
        skip=skip,
        limit=limit,
        upcoming_only=upcoming_only,
    )
    return AppointmentListResponse(
        items=[AppointmentRead.model_validate(row) for row in items],
        total=len(items),
    )
