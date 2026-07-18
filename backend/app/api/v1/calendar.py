"""Google Calendar Web OAuth routes (per authenticated user)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, GoogleOAuthServiceDep
from app.schemas.calendar import (
    CalendarConnectResponse,
    CalendarDisconnectResponse,
    CalendarStatusResponse,
)
from app.services.google_oauth_service import GoogleOAuthError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get(
    "/connect",
    response_model=CalendarConnectResponse,
    summary="Start Google Calendar Web OAuth for the current user",
)
def connect_calendar(
    current_user: CurrentUser,
    oauth: GoogleOAuthServiceDep,
    redirect: bool = Query(
        default=False,
        description="If true, redirect the browser to Google instead of returning JSON",
    ),
):
    try:
        authorization_url = oauth.build_authorization_url(current_user.id)
    except GoogleOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if redirect:
        return RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)
    return CalendarConnectResponse(authorization_url=authorization_url)


@router.get(
    "/callback",
    summary="Google OAuth callback — stores per-user calendar tokens",
)
def calendar_oauth_callback(
    oauth: GoogleOAuthServiceDep,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}",
        )
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state from Google OAuth callback",
        )

    try:
        user = oauth.handle_callback(code=code, state=state)
    except GoogleOAuthError as exc:
        logger.exception("Calendar OAuth callback failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "connected": True,
        "user_id": str(user.id),
        "email": user.email,
        "message": "Google Calendar connected successfully.",
    }


@router.get(
    "/status",
    response_model=CalendarStatusResponse,
    summary="Whether the current user has connected Google Calendar",
)
def calendar_status(
    current_user: CurrentUser,
    oauth: GoogleOAuthServiceDep,
) -> CalendarStatusResponse:
    expiry = None
    if current_user.google_token_expiry is not None:
        expiry = current_user.google_token_expiry.isoformat()
    return CalendarStatusResponse(
        connected=current_user.google_calendar_connected,
        google_oauth_configured=oauth.is_configured,
        token_expiry=expiry,
    )


@router.delete(
    "/disconnect",
    response_model=CalendarDisconnectResponse,
    summary="Disconnect Google Calendar for the current user",
)
def disconnect_calendar(
    current_user: CurrentUser,
    oauth: GoogleOAuthServiceDep,
) -> CalendarDisconnectResponse:
    oauth.disconnect(current_user)
    return CalendarDisconnectResponse()
