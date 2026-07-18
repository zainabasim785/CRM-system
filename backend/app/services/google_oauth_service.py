"""
Google Calendar Web OAuth (multi-user).

Each authenticated app user connects their own Google account. Tokens are
stored on the users row — no token.json / InstalledAppFlow.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
OAUTH_STATE_PURPOSE = "google_calendar_oauth"
OAUTH_STATE_TTL = timedelta(minutes=15)


class GoogleOAuthError(Exception):
    """Raised when the Web OAuth flow fails."""


class GoogleOAuthService:
    """Builds authorize URLs and exchanges callback codes for per-user tokens."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.google_client_id and self.settings.google_client_secret)

    def build_authorization_url(self, user_id: UUID) -> str:
        if not self.is_configured:
            raise GoogleOAuthError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set."
            )

        state = create_access_token(
            subject=str(user_id),
            expires_delta=OAUTH_STATE_TTL,
            extra_claims={"purpose": OAUTH_STATE_PURPOSE},
        )
        flow = self._make_flow(state=state)
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    def handle_callback(
        self,
        *,
        code: str,
        state: str,
    ) -> User:
        if not self.is_configured:
            raise GoogleOAuthError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set."
            )

        user_id = self._parse_state(state)
        user = self.users.get(user_id)
        if user is None:
            raise GoogleOAuthError("User not found for OAuth state")
        if not user.is_active:
            raise GoogleOAuthError("User account is inactive")

        flow = self._make_flow(state=state)
        try:
            flow.fetch_token(code=code)
        except Exception as exc:
            logger.exception("Google OAuth token exchange failed")
            raise GoogleOAuthError(f"Failed to exchange authorization code: {exc}") from exc

        creds = flow.credentials
        user.google_access_token = creds.token
        if creds.refresh_token:
            user.google_refresh_token = creds.refresh_token
        elif not user.google_refresh_token:
            raise GoogleOAuthError(
                "Google did not return a refresh token. "
                "Revoke app access in Google Account settings and reconnect."
            )

        if creds.expiry:
            expiry = creds.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=UTC)
            user.google_token_expiry = expiry
        else:
            user.google_token_expiry = None

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("Stored Google Calendar tokens for user %s", user.id)
        return user

    def disconnect(self, user: User) -> User:
        managed = self.users.get(user.id)
        if managed is None:
            raise GoogleOAuthError("User not found")

        managed.google_access_token = None
        managed.google_refresh_token = None
        managed.google_token_expiry = None
        self.db.add(managed)
        self.db.commit()
        self.db.refresh(managed)
        return managed

    def _parse_state(self, state: str) -> UUID:
        try:
            payload = decode_access_token(state)
        except ValueError as exc:
            raise GoogleOAuthError("Invalid or expired OAuth state") from exc

        if payload.get("purpose") != OAUTH_STATE_PURPOSE:
            raise GoogleOAuthError("Invalid OAuth state purpose")

        subject = payload.get("sub")
        if not subject:
            raise GoogleOAuthError("OAuth state missing subject")

        try:
            return UUID(str(subject))
        except ValueError as exc:
            raise GoogleOAuthError("OAuth state subject is not a valid user id") from exc

    def _make_flow(self, *, state: str | None = None) -> Flow:
        client_config = {
            "web": {
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "auth_uri": GOOGLE_AUTH_URI,
                "token_uri": GOOGLE_TOKEN_URI,
                "redirect_uris": [self.settings.google_redirect_uri],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=self.settings.google_scopes_list,
            state=state,
        )
        flow.redirect_uri = self.settings.google_redirect_uri
        return flow
