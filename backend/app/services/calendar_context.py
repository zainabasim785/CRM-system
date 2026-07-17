"""Request/agent context for which user's Google Calendar to use."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from collections.abc import Iterator
from uuid import UUID

_calendar_user_id: ContextVar[UUID | None] = ContextVar("calendar_user_id", default=None)


def get_calendar_user_id() -> UUID | None:
    return _calendar_user_id.get()


def set_calendar_user_id(user_id: UUID | None) -> Token:
    return _calendar_user_id.set(user_id)


def reset_calendar_user_id(token: Token) -> None:
    _calendar_user_id.reset(token)


@contextmanager
def calendar_user_context(user_id: UUID | None) -> Iterator[None]:
    """Bind calendar API calls to a specific authenticated user."""
    token = set_calendar_user_id(user_id)
    try:
        yield
    finally:
        reset_calendar_user_id(token)
