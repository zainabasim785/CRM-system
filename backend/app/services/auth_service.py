"""
Authentication domain service.

Handles registration, credential verification, and JWT issuance.
HTTP concerns stay in the API layer.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate


class AuthError(Exception):
    """Base authentication / authorization error."""


class EmailAlreadyRegisteredError(AuthError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InactiveUserError(AuthError):
    def __init__(self) -> None:
        super().__init__("User account is inactive")


class InvalidTokenError(AuthError):
    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message)


class UserNotFoundError(AuthError):
    def __init__(self) -> None:
        super().__init__("User not found")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

    def register(self, data: UserCreate) -> tuple[User, TokenResponse]:
        """Create a customer account and return the user plus an access token."""
        if self.users.get_by_email(str(data.email)):
            raise EmailAlreadyRegisteredError(str(data.email))

        user = self.users.create_user(
            email=str(data.email),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        self.db.commit()
        self.db.refresh(user)
        return user, self._issue_token(user)

    def login(self, email: str, password: str) -> tuple[User, TokenResponse]:
        """Verify credentials and issue a JWT access token."""
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()
        return user, self._issue_token(user)

    def get_user_from_token(self, token: str) -> User:
        """Decode a JWT and load the corresponding active user."""
        try:
            payload = decode_access_token(token)
        except ValueError as exc:
            raise InvalidTokenError() from exc

        subject = payload.get("sub")
        if not subject:
            raise InvalidTokenError("Token missing subject")

        try:
            user_id = UUID(str(subject))
        except ValueError as exc:
            raise InvalidTokenError("Token subject is not a valid user id") from exc

        user = self.users.get(user_id)
        if user is None:
            raise UserNotFoundError()
        if not user.is_active:
            raise InactiveUserError()
        return user

    def _issue_token(self, user: User) -> TokenResponse:
        expires_minutes = self.settings.access_token_expire_minutes
        token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=expires_minutes),
            extra_claims={
                "email": user.email,
                "role": user.role.value,
            },
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_minutes * 60,
        )
