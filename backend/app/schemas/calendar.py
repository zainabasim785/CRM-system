"""Calendar OAuth / connection schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CalendarConnectResponse(BaseModel):
    authorization_url: str = Field(
        ...,
        description="Open this URL to connect Google Calendar for the current user",
    )


class CalendarStatusResponse(BaseModel):
    connected: bool
    google_oauth_configured: bool
    token_expiry: str | None = None


class CalendarDisconnectResponse(BaseModel):
    connected: bool = False
    message: str = "Google Calendar disconnected."
