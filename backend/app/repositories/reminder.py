"""Reminder repository."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, select

from app.models.enums import ReminderStatus
from app.models.reminder import Reminder
from app.repositories.base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    model = Reminder

    def list_due(
        self,
        as_of: datetime,
        *,
        status: ReminderStatus = ReminderStatus.SCHEDULED,
        limit: int = 100,
    ) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(
                and_(
                    Reminder.status == status,
                    Reminder.remind_at <= as_of,
                )
            )
            .order_by(Reminder.remind_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_conversation(self, conversation_id: uuid.UUID) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(Reminder.conversation_id == conversation_id)
            .order_by(Reminder.remind_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_for_session_via_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(Reminder.conversation_id == conversation_id)
            .order_by(Reminder.remind_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def mark_status(self, reminder: Reminder, status: ReminderStatus) -> Reminder:
        return self.update(reminder, status=status)
