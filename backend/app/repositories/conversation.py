"""Conversation repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.enums import ConversationStatus
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    def get_by_session_id(self, session_id: str) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        return self.db.scalars(stmt).first()

    def get_with_logs(self, conversation_id: uuid.UUID) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.interaction_logs))
        )
        return self.db.scalars(stmt).first()

    def get_or_create_by_session(
        self,
        session_id: str,
        *,
        user_id: uuid.UUID | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> tuple[Conversation, bool]:
        existing = self.get_by_session_id(session_id)
        if existing is not None:
            return existing, False
        created = self.create(
            session_id=session_id,
            user_id=user_id,
            extra_data=extra_data or {},
        )
        return created, True

    def update_summary(
        self,
        conversation: Conversation,
        summary: str,
        *,
        status: ConversationStatus | None = None,
    ) -> Conversation:
        payload: dict[str, Any] = {"summary": summary}
        if status is not None:
            payload["status"] = status
        return self.update(conversation, **payload)

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(
        self,
        status: ConversationStatus,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.status == status)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
