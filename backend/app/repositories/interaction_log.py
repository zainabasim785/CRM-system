"""InteractionLog repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.models.enums import InteractionRole
from app.models.interaction_log import InteractionLog
from app.repositories.base import BaseRepository


class InteractionLogRepository(BaseRepository[InteractionLog]):
    model = InteractionLog

    def list_for_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 500,
    ) -> list[InteractionLog]:
        stmt = (
            select(InteractionLog)
            .where(InteractionLog.conversation_id == conversation_id)
            .order_by(InteractionLog.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def add_message(
        self,
        *,
        conversation_id: uuid.UUID,
        role: InteractionRole | str,
        content: str,
        intent: str | None = None,
        agent_name: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> InteractionLog:
        resolved_role = role if isinstance(role, InteractionRole) else InteractionRole(role)
        return self.create(
            conversation_id=conversation_id,
            role=resolved_role,
            content=content,
            intent=intent,
            agent_name=agent_name,
            extra_data=extra_data or {},
        )

    def bulk_add_messages(
        self,
        *,
        conversation_id: uuid.UUID,
        messages: list[dict[str, Any]],
        intent: str | None = None,
        agent_name: str | None = None,
    ) -> list[InteractionLog]:
        created: list[InteractionLog] = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if not content:
                continue
            created.append(
                self.add_message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    intent=intent,
                    agent_name=agent_name,
                    extra_data={k: v for k, v in message.items() if k not in {"role", "content"}},
                )
            )
        return created
