"""
Reception desk use case — wires AgentManager to persistence.

Accepts a visitor message, runs triage → booking (when needed) → follow-up,
ensures the turn is saved, and returns the agent reply.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.manager import AgentManager, get_agent_manager
from app.models.enums import ConversationStatus
from app.schemas.agent import AgentRequest, AgentResponse, ConversationMessage
from app.services.calendar_context import calendar_user_context
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ReceptionService:
    """HTTP-facing orchestration around AgentManager + ConversationService."""

    def __init__(
        self,
        db: Session,
        *,
        agent_manager: AgentManager | None = None,
    ) -> None:
        self.db = db
        self.conversations = ConversationService(db)
        self._agent_manager = agent_manager

    @property
    def agents(self) -> AgentManager:
        if self._agent_manager is None:
            self._agent_manager = get_agent_manager()
        return self._agent_manager

    def handle_message(
        self,
        *,
        message: str,
        session_id: str | None = None,
        user_id: UUID | None = None,
        conversation_history: list[ConversationMessage] | None = None,
        metadata: dict | None = None,
    ) -> AgentResponse:
        history = list(conversation_history or [])
        if session_id and not history:
            history = self._load_history(session_id)

        request = AgentRequest(
            message=message,
            session_id=session_id,
            user_id=str(user_id) if user_id else None,
            conversation_history=history,
            metadata=metadata or {},
        )

        with calendar_user_context(user_id):
            response = self.agents.handle_message(request)
        self._ensure_conversation_saved(request, response, user_id=user_id)
        return response

    def _load_history(self, session_id: str) -> list[ConversationMessage]:
        logs = self.conversations.list_logs(session_id=session_id)
        if not logs:
            return []
        messages = logs[0].get("messages") or []
        return [
            ConversationMessage(role=str(msg["role"]), content=str(msg["content"]))
            for msg in messages
            if msg.get("content")
        ][-12:]

    def _ensure_conversation_saved(
        self,
        request: AgentRequest,
        response: AgentResponse,
        *,
        user_id: UUID | None,
    ) -> None:
        session_id = response.session_id or request.session_id
        if not session_id:
            return

        logged = bool(response.follow_up and response.follow_up.logged)
        if not logged:
            logger.info(
                "Follow-up did not persist session %s; saving turn via ConversationService",
                session_id,
            )
            summary = response.follow_up.summary if response.follow_up else None
            self.conversations.log_conversation(
                session_id=session_id,
                messages=[
                    {"role": "user", "content": request.message},
                    {"role": "assistant", "content": response.reply},
                ],
                summary=summary or None,
                metadata={
                    "intent": response.intent.value,
                    "needs_escalation": response.needs_escalation,
                    **(response.metadata or {}),
                },
                user_id=user_id,
                intent=response.intent.value,
                agent_name="reception",
            )
        elif user_id is not None:
            conversation = self.conversations.conversations.get_by_session_id(session_id)
            if conversation is not None and conversation.user_id is None:
                self.conversations.conversations.update(conversation, user_id=user_id)
                self.db.commit()

        if response.needs_escalation:
            conversation = self.conversations.conversations.get_by_session_id(session_id)
            if conversation is not None and conversation.status != ConversationStatus.ESCALATED:
                self.conversations.conversations.update_summary(
                    conversation,
                    conversation.summary or response.escalate_reason or "Escalated to human",
                    status=ConversationStatus.ESCALATED,
                )
                self.db.commit()
