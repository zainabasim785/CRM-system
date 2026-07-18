"""User repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
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
