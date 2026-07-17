"""
Google Calendar operations used by Booking Agent tools.

Uses each authenticated user's OAuth tokens from the database (Web OAuth).
No token.json / InstalledAppFlow.

Core API methods: create_event, update_event, delete_event, get_availability.
Legacy helpers (create_appointment, …) delegate to these unchanged.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterator
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.user import User
from app.services.calendar_context import get_calendar_user_id

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


def _parse_datetime(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _to_rfc3339(value: str) -> str:
    return _parse_datetime(value).isoformat()


class CalendarService:
    """Thin adapter around Google Calendar API for a single user."""

    def __init__(
        self,
        db: Session | None = None,
        user: User | None = None,
    ) -> None:
        self._settings = get_settings()
        self._db = db
        self._user = user
        self._service = None

    @property
    def is_configured(self) -> bool:
        """True when the app has Google OAuth client credentials."""
        return bool(self._settings.google_client_id and self._settings.google_client_secret)

    @property
    def is_user_connected(self) -> bool:
        return bool(
            self._user is not None
            and (self._user.google_refresh_token or self._user.google_access_token)
        )

    # -------------------------------------------------------------------------
    # Core Google Calendar API methods
    # -------------------------------------------------------------------------

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        *,
        attendee_email: str | None = None,
        description: str | None = None,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Create a calendar event (events.insert)."""
        blocked = self._connection_block(
            summary=summary,
            start=start,
            end=end,
            action="create",
        )
        if blocked:
            return blocked

        try:
            service = self._get_service()
            body: dict[str, Any] = {
                "summary": summary,
                "start": {"dateTime": _to_rfc3339(start), "timeZone": "UTC"},
                "end": {"dateTime": _to_rfc3339(end), "timeZone": "UTC"},
            }
            if description:
                body["description"] = description
            if attendee_email:
                body["attendees"] = [{"email": attendee_email}]

            created = (
                service.events()
                .insert(calendarId=calendar_id, body=body, sendUpdates="all")
                .execute()
            )
            event_id = created.get("id")
            return {
                "success": True,
                "configured": True,
                "event_id": event_id,
                "html_link": created.get("htmlLink"),
                "summary": created.get("summary", summary),
                "start": start,
                "end": end,
                "attendee_email": attendee_email,
                "description": description,
                "calendar_id": calendar_id,
                "message": f"Appointment created (event {event_id}).",
            }
        except Exception as exc:
            logger.exception("create_event failed")
            return {
                "success": False,
                "configured": True,
                "summary": summary,
                "start": start,
                "end": end,
                "calendar_id": calendar_id,
                "message": f"Failed to create event: {exc}",
            }

    def update_event(
        self,
        event_id: str,
        *,
        start: str | None = None,
        end: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Update an existing calendar event (events.patch)."""
        blocked = self._connection_block(event_id=event_id, action="update")
        if blocked:
            return blocked

        try:
            service = self._get_service()
            body: dict[str, Any] = {}
            if summary is not None:
                body["summary"] = summary
            if description is not None:
                body["description"] = description
            if start is not None:
                body["start"] = {"dateTime": _to_rfc3339(start), "timeZone": "UTC"}
            if end is not None:
                body["end"] = {"dateTime": _to_rfc3339(end), "timeZone": "UTC"}

            if not body:
                return {
                    "success": False,
                    "configured": True,
                    "event_id": event_id,
                    "calendar_id": calendar_id,
                    "message": "No fields provided to update.",
                }

            updated = (
                service.events()
                .patch(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=body,
                    sendUpdates="all",
                )
                .execute()
            )
            return {
                "success": True,
                "configured": True,
                "event_id": updated.get("id", event_id),
                "html_link": updated.get("htmlLink"),
                "summary": updated.get("summary"),
                "new_start": start,
                "new_end": end,
                "calendar_id": calendar_id,
                "message": f"Event {event_id} updated successfully.",
            }
        except Exception as exc:
            logger.exception("update_event failed")
            return {
                "success": False,
                "configured": True,
                "event_id": event_id,
                "calendar_id": calendar_id,
                "message": f"Failed to update event: {exc}",
            }

    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Delete a calendar event (events.delete)."""
        blocked = self._connection_block(event_id=event_id, action="delete")
        if blocked:
            return blocked

        try:
            service = self._get_service()
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates="all",
            ).execute()
            return {
                "success": True,
                "configured": True,
                "event_id": event_id,
                "calendar_id": calendar_id,
                "message": f"Event {event_id} deleted successfully.",
            }
        except HttpError as exc:
            logger.exception("delete_event failed")
            if getattr(exc, "resp", None) is not None and exc.resp.status in {404, 410}:
                return {
                    "success": True,
                    "configured": True,
                    "event_id": event_id,
                    "calendar_id": calendar_id,
                    "message": f"Event {event_id} was already deleted or not found.",
                }
            return {
                "success": False,
                "configured": True,
                "event_id": event_id,
                "calendar_id": calendar_id,
                "message": f"Failed to delete event: {exc}",
            }
        except Exception as exc:
            logger.exception("delete_event failed")
            return {
                "success": False,
                "configured": True,
                "event_id": event_id,
                "calendar_id": calendar_id,
                "message": f"Failed to delete event: {exc}",
            }

    def get_availability(
        self,
        start: str,
        end: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Check free/busy for a time range (freebusy.query)."""
        blocked = self._connection_block(
            requested_start=start,
            requested_end=end,
            calendar_id=calendar_id,
            action="availability",
        )
        if blocked:
            return blocked

        try:
            service = self._get_service()
            body = {
                "timeMin": _to_rfc3339(start),
                "timeMax": _to_rfc3339(end),
                "items": [{"id": calendar_id}],
            }
            result = service.freebusy().query(body=body).execute()
            calendar_busy = (result.get("calendars") or {}).get(calendar_id) or {}
            busy_slots = calendar_busy.get("busy") or []
            errors = calendar_busy.get("errors") or []
            available = len(busy_slots) == 0 and not errors

            if errors:
                message = f"Could not read availability: {errors}"
            elif available:
                message = f"Slot from {start} to {end} is free."
            else:
                message = f"Slot from {start} to {end} has {len(busy_slots)} conflicting event(s)."

            return {
                "available": available,
                "configured": True,
                "busy": busy_slots,
                "message": message,
                "requested_start": start,
                "requested_end": end,
                "calendar_id": calendar_id,
            }
        except Exception as exc:
            logger.exception("get_availability failed")
            return {
                "available": None,
                "configured": True,
                "message": f"Failed to check availability: {exc}",
                "requested_start": start,
                "requested_end": end,
                "calendar_id": calendar_id,
            }

    # -------------------------------------------------------------------------
    # Existing interface (agent tools) — delegates to core methods
    # -------------------------------------------------------------------------

    def check_availability(
        self,
        start: str,
        end: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        return self.get_availability(start, end, calendar_id)

    def create_appointment(
        self,
        summary: str,
        start: str,
        end: str,
        attendee_email: str | None = None,
        description: str | None = None,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        return self.create_event(
            summary=summary,
            start=start,
            end=end,
            attendee_email=attendee_email,
            description=description,
            calendar_id=calendar_id,
        )

    def cancel_appointment(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        return self.delete_event(event_id, calendar_id)

    def reschedule_appointment(
        self,
        event_id: str,
        new_start: str,
        new_end: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        result = self.update_event(
            event_id,
            start=new_start,
            end=new_end,
            calendar_id=calendar_id,
        )
        if "new_start" not in result:
            result["new_start"] = new_start
        if "new_end" not in result:
            result["new_end"] = new_end
        if result.get("success") and "message" in result:
            result["message"] = (
                f"Reschedule completed for event {event_id} to {new_start}–{new_end}."
            )
        return result

    # -------------------------------------------------------------------------
    # Auth / client helpers (per-user DB tokens)
    # -------------------------------------------------------------------------

    def _connection_block(self, *, action: str, **extra: Any) -> dict[str, Any] | None:
        if not self.is_configured:
            base = {
                "configured": False,
                "message": (
                    "Google Calendar is not configured yet. "
                    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable live checks."
                ),
            }
            if action == "availability":
                return {
                    **base,
                    "available": None,
                    "requested_start": extra.get("requested_start"),
                    "requested_end": extra.get("requested_end"),
                    "calendar_id": extra.get("calendar_id", "primary"),
                }
            return {
                **base,
                "success": False,
                **{k: v for k, v in extra.items() if k in {"summary", "start", "end", "event_id"}},
            }

        if not self.is_user_connected:
            message = (
                "Google Calendar is not connected for this user. "
                "Authenticate and visit /api/v1/calendar/connect to link a calendar."
            )
            if action == "availability":
                return {
                    "available": None,
                    "configured": True,
                    "connected": False,
                    "message": message,
                    "requested_start": extra.get("requested_start"),
                    "requested_end": extra.get("requested_end"),
                    "calendar_id": extra.get("calendar_id", "primary"),
                }
            return {
                "success": False,
                "configured": True,
                "connected": False,
                "message": message,
                **{k: v for k, v in extra.items() if k in {"summary", "start", "end", "event_id"}},
            }
        return None

    def _get_service(self):
        if self._service is not None:
            return self._service

        credentials = self._load_credentials()
        self._service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )
        return self._service

    def _load_credentials(self) -> Credentials:
        if not self.is_configured:
            raise RuntimeError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the environment."
            )
        if self._user is None:
            raise RuntimeError("No authenticated user bound to CalendarService.")
        if not (self._user.google_refresh_token or self._user.google_access_token):
            raise RuntimeError("User has not connected Google Calendar.")

        scopes = self._settings.google_scopes_list
        expiry = self._user.google_token_expiry
        # google-auth expects naive UTC expiry
        naive_expiry = None
        if expiry is not None:
            naive_expiry = expiry.astimezone(UTC).replace(tzinfo=None)

        creds = Credentials(
            token=self._user.google_access_token,
            refresh_token=self._user.google_refresh_token,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret,
            scopes=scopes,
        )
        if naive_expiry is not None:
            creds.expiry = naive_expiry

        if not creds.valid:
            if creds.refresh_token:
                creds.refresh(Request())
                self._persist_credentials(creds)
                logger.info("Refreshed Google Calendar token for user %s", self._user.id)
            else:
                raise RuntimeError(
                    "Google Calendar access token expired and no refresh token is stored. "
                    "Reconnect via /api/v1/calendar/connect."
                )

        return creds

    def _persist_credentials(self, creds: Credentials) -> None:
        if self._user is None or self._db is None:
            return

        self._user.google_access_token = creds.token
        if creds.refresh_token:
            self._user.google_refresh_token = creds.refresh_token
        if creds.expiry:
            expiry = creds.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=UTC)
            self._user.google_token_expiry = expiry

        self._db.add(self._user)
        self._db.commit()
        self._db.refresh(self._user)


@contextmanager
def user_calendar_session(user_id: UUID | None = None) -> Iterator[CalendarService]:
    """Open a DB-backed CalendarService for the given (or context) user."""
    resolved_id = user_id if user_id is not None else get_calendar_user_id()
    db = SessionLocal()
    try:
        user = db.get(User, resolved_id) if resolved_id is not None else None
        yield CalendarService(db=db, user=user)
    finally:
        db.close()


def get_calendar_service() -> CalendarService:
    """
    Resolve a CalendarService for the current calendar user context.

    Prefer `user_calendar_session()` in long-lived callers so the DB session
    is closed; agent tools use that helper.
    """
    user_id = get_calendar_user_id()
    if user_id is None:
        return CalendarService()
    db = SessionLocal()
    user = db.get(User, user_id)
    return CalendarService(db=db, user=user)


# Backward-compatible name — unbound (no user). Prefer get_calendar_service().
calendar_service = CalendarService()
