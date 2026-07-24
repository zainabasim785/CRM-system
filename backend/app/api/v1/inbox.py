"""Staff inbox — escalated conversations and follow-up reminders (PostgreSQL only)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models.enums import ConversationStatus, ReminderStatus, UserRole
from app.repositories.conversation import ConversationRepository
from app.repositories.interaction_log import InteractionLogRepository
from app.repositories.reminder import ReminderRepository
from app.schemas.inbox import (
    InboxConversationItem,
    InboxConversationUpdate,
    InboxReminderItem,
    InboxReminderUpdate,
    InboxResponse,
)

router = APIRouter(prefix="/inbox", tags=["inbox"])

_STAFF_ROLES = {UserRole.ADMIN, UserRole.RECEPTIONIST}


def _staff_view(user) -> bool:
    return user.role in _STAFF_ROLES or user.google_calendar_connected


def _require_staff(user) -> None:
    if not _staff_view(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inbox requires a staff account or connected Google Calendar.",
        )


@router.get(
    "",
    response_model=InboxResponse,
    summary="Escalated conversations and pending reminders",
)
def get_inbox(current_user: CurrentUser, db: DbSession) -> InboxResponse:
    _require_staff(current_user)

    conversations = ConversationRepository(db)
    logs = InteractionLogRepository(db)
    reminders = ReminderRepository(db)

    escalated_rows = conversations.list_by_status(
        ConversationStatus.ESCALATED,
        limit=50,
    )
    escalated: list[InboxConversationItem] = []
    for row in escalated_rows:
        thread = logs.list_for_conversation(row.id, limit=500)
        last = thread[-1].content if thread else None
        escalated.append(
            InboxConversationItem(
                id=row.id,
                session_id=row.session_id,
                summary=row.summary,
                status=row.status,
                extra_data=dict(row.extra_data or {}),
                updated_at=row.updated_at,
                last_message=last,
            )
        )

    reminder_rows = reminders.list_scheduled(limit=50)
    reminder_items: list[InboxReminderItem] = []
    for reminder in reminder_rows:
        session_id = None
        if reminder.conversation_id is not None:
            conv = conversations.get(reminder.conversation_id)
            if conv is not None:
                session_id = conv.session_id
        reminder_items.append(
            InboxReminderItem(
                id=reminder.id,
                conversation_id=reminder.conversation_id,
                session_id=session_id,
                note=reminder.note,
                remind_at=reminder.remind_at,
                status=reminder.status,
                created_at=reminder.created_at,
                updated_at=reminder.updated_at,
            )
        )

    return InboxResponse(escalated=escalated, reminders=reminder_items)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=InboxConversationItem,
    summary="Update escalated conversation status (e.g. mark resolved)",
)
def update_inbox_conversation(
    conversation_id: UUID,
    payload: InboxConversationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> InboxConversationItem:
    _require_staff(current_user)

    repo = ConversationRepository(db)
    logs = InteractionLogRepository(db)
    conversation = repo.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = repo.update(conversation, status=payload.status)
    db.commit()
    db.refresh(conversation)

    thread = logs.list_for_conversation(conversation.id, limit=500)
    last = thread[-1].content if thread else None
    return InboxConversationItem(
        id=conversation.id,
        session_id=conversation.session_id,
        summary=conversation.summary,
        status=conversation.status,
        extra_data=dict(conversation.extra_data or {}),
        updated_at=conversation.updated_at,
        last_message=last,
    )


@router.patch(
    "/reminders/{reminder_id}",
    response_model=InboxReminderItem,
    summary="Update reminder status (e.g. mark done)",
)
def update_inbox_reminder(
    reminder_id: UUID,
    payload: InboxReminderUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> InboxReminderItem:
    _require_staff(current_user)

    if payload.status not in {ReminderStatus.SENT, ReminderStatus.CANCELLED}:
        raise HTTPException(
            status_code=400,
            detail="Only sent or cancelled status is allowed from the inbox.",
        )

    reminders = ReminderRepository(db)
    conversations = ConversationRepository(db)
    reminder = reminders.get(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder = reminders.mark_status(reminder, payload.status)
    db.commit()
    db.refresh(reminder)

    session_id = None
    if reminder.conversation_id is not None:
        conv = conversations.get(reminder.conversation_id)
        if conv is not None:
            session_id = conv.session_id

    return InboxReminderItem(
        id=reminder.id,
        conversation_id=reminder.conversation_id,
        session_id=session_id,
        note=reminder.note,
        remind_at=reminder.remind_at,
        status=reminder.status,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )
