"""
Conversation logging and reminder helpers for the Follow-up Agent.

Persists via SQLAlchemy repositories (Conversation, InteractionLog, Reminder).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import InteractionRole, ReminderChannel, ReminderStatus
from app.repositories.conversation import ConversationRepository
from app.repositories.interaction_log import InteractionLogRepository
from app.repositories.reminder import ReminderRepository

logger = logging.getLogger(__name__)


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    cleaned = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _normalize_role(role: str) -> InteractionRole:
    try:
        return InteractionRole(role.lower())
    except ValueError:
        return InteractionRole.SYSTEM


class ConversationService:
    """Log transcripts, store summaries, and register reminders in PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.interactions = InteractionLogRepository(db)
        self.reminders = ReminderRepository(db)

    def log_conversation(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
        summary: str | None = None,
        metadata: dict[str, Any] | None = None,
        user_id: UUID | None = None,
        intent: str | None = None,
        agent_name: str = "followup",
    ) -> dict[str, Any]:
        conversation, created = self.conversations.get_or_create_by_session(
            session_id,
            user_id=user_id,
            extra_data=metadata or {},
        )

        if metadata:
            merged = dict(conversation.extra_data or {})
            merged.update(metadata)
            conversation = self.conversations.update(conversation, extra_data=merged)

        normalized_messages: list[dict[str, Any]] = []
        for message in messages:
            content = message.get("content")
            if not content:
                continue
            normalized_messages.append(
                {
                    "role": _normalize_role(str(message.get("role", "user"))).value,
                    "content": str(content),
                    **{
                        key: value
                        for key, value in message.items()
                        if key not in {"role", "content"}
                    },
                }
            )

        logs = self.interactions.bulk_add_messages(
            conversation_id=conversation.id,
            messages=normalized_messages,
            intent=intent,
            agent_name=agent_name,
        )

        if summary:
            conversation = self.conversations.update_summary(conversation, summary)

        self.db.commit()
        self.db.refresh(conversation)

        return {
            "success": True,
            "conversation_id": str(conversation.id),
            "log_id": str(conversation.id),
            "session_id": session_id,
            "created_conversation": created,
            "message_count": len(logs),
            "summary": conversation.summary,
            "logged_at": conversation.updated_at.isoformat(),
        }

    def schedule_reminder(
        self,
        session_id: str,
        remind_at: str | datetime,
        note: str,
        channel: str = "internal",
        user_id: UUID | None = None,
        appointment_id: UUID | None = None,
    ) -> dict[str, Any]:
        conversation, _ = self.conversations.get_or_create_by_session(
            session_id,
            user_id=user_id,
        )

        try:
            channel_enum = ReminderChannel(channel.lower())
        except ValueError:
            channel_enum = ReminderChannel.INTERNAL

        reminder = self.reminders.create(
            conversation_id=conversation.id,
            appointment_id=appointment_id,
            user_id=user_id or conversation.user_id,
            remind_at=_parse_datetime(remind_at),
            note=note,
            channel=channel_enum,
            status=ReminderStatus.SCHEDULED,
        )
        self.db.commit()
        self.db.refresh(reminder)

        return {
            "success": True,
            "reminder_id": str(reminder.id),
            "conversation_id": str(conversation.id),
            "session_id": session_id,
            "remind_at": reminder.remind_at.isoformat(),
            "note": reminder.note,
            "channel": reminder.channel.value,
            "status": reminder.status.value,
            "message": "Reminder scheduled successfully.",
        }

    def default_reminder_time(self, hours_from_now: int = 24) -> str:
        return (datetime.now(UTC) + timedelta(hours=hours_from_now)).isoformat()

    def list_logs(self, session_id: str | None = None) -> list[dict[str, Any]]:
        if session_id is None:
            conversations = self.conversations.list(limit=200)
        else:
            conversation = self.conversations.get_by_session_id(session_id)
            conversations = [conversation] if conversation else []

        results: list[dict[str, Any]] = []
        for conversation in conversations:
            if conversation is None:
                continue
            logs = self.interactions.list_for_conversation(conversation.id)
            results.append(
                {
                    "id": str(conversation.id),
                    "session_id": conversation.session_id,
                    "summary": conversation.summary,
                    "status": conversation.status.value,
                    "messages": [
                        {
                            "role": log.role.value,
                            "content": log.content,
                            "intent": log.intent,
                            "agent_name": log.agent_name,
                            "created_at": log.created_at.isoformat(),
                        }
                        for log in logs
                    ],
                    "logged_at": conversation.updated_at.isoformat(),
                }
            )
        return results
