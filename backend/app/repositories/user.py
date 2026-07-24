"""User repository."""

from __future__ import annotations

from sqlalchemy import case, or_, select

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalars(stmt).first()

    def get_calendar_owner(self) -> User | None:
        """First active user with Google Calendar linked (staff accounts preferred)."""
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .where(
                or_(
                    User.google_refresh_token.isnot(None),
                    User.google_access_token.isnot(None),
                )
            )
            .order_by(
                case(
                    (User.role.in_([UserRole.ADMIN, UserRole.RECEPTIONIST]), 0),
                    else_=1,
                ),
                User.created_at.asc(),
            )
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def create_user(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        phone: str | None = None,
        role=None,
        is_active: bool = True,
    ) -> User:
        payload: dict = {
            "email": email.lower(),
            "hashed_password": hashed_password,
            "full_name": full_name,
            "phone": phone,
            "is_active": is_active,
        }
        if role is not None:
            payload["role"] = role
        return self.create(**payload)
