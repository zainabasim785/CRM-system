"""Conversation logging and reminder tools for the Follow-up Agent."""

from __future__ import annotations

import json
import logging
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.core.database import SessionLocal
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class LogConversationInput(BaseModel):
    session_id: str = Field(..., description="Conversation / session identifier")
    messages_json: str = Field(
        ...,
        description=(
            "JSON array of messages: "
            '[{"role":"user"|"assistant","content":"..."}, ...]'
        ),
    )
    summary: str | None = Field(
        default=None, description="Optional short summary to store with the log"
    )


class LogConversationTool(BaseTool):
    name: str = "log_conversation"
    description: str = (
        "Persist the conversation transcript for CRM / receptionist records."
    )
    args_schema: Type[BaseModel] = LogConversationInput

    def _run(
        self,
        session_id: str,
        messages_json: str,
        summary: str | None = None,
    ) -> str:
        try:
            messages = json.loads(messages_json)
            if not isinstance(messages, list):
                raise ValueError("messages_json must be a JSON array")
        except (json.JSONDecodeError, ValueError) as exc:
            return json.dumps({"success": False, "error": str(exc)})

        db = SessionLocal()
        try:
            service = ConversationService(db)
            result = service.log_conversation(
                session_id=session_id,
                messages=messages,
                summary=summary,
            )
            return json.dumps(result)
        except Exception as exc:
            db.rollback()
            logger.exception("log_conversation failed")
            return json.dumps({"success": False, "error": str(exc)})
        finally:
            db.close()


class ScheduleReminderInput(BaseModel):
    session_id: str = Field(..., description="Conversation / session identifier")
    remind_at: str = Field(
        ...,
        description="When to remind, ISO-8601 UTC datetime",
    )
    note: str = Field(..., description="What the reminder should say / refer to")
    channel: str = Field(
        default="internal",
        description="Delivery channel placeholder: internal | email | sms",
    )


class ScheduleReminderTool(BaseTool):
    name: str = "schedule_reminder"
    description: str = (
        "Schedule a follow-up reminder related to this conversation or appointment."
    )
    args_schema: Type[BaseModel] = ScheduleReminderInput

    def _run(
        self,
        session_id: str,
        remind_at: str,
        note: str,
        channel: str = "internal",
    ) -> str:
        db = SessionLocal()
        try:
            service = ConversationService(db)
            result = service.schedule_reminder(
                session_id=session_id,
                remind_at=remind_at,
                note=note,
                channel=channel,
            )
            return json.dumps(result)
        except Exception as exc:
            db.rollback()
            logger.exception("schedule_reminder failed")
            return json.dumps({"success": False, "error": str(exc)})
        finally:
            db.close()


def get_followup_tools() -> list[BaseTool]:
    return [LogConversationTool(), ScheduleReminderTool()]
