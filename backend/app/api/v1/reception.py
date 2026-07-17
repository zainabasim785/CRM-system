"""Reception agent message endpoint — triage → booking → persist → reply."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import OptionalUser, ReceptionServiceDep
from app.schemas.agent import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reception", tags=["reception"])


@router.post(
    "/message",
    response_model=AgentResponse,
    summary="Send a message to the AI reception agents",
)
def post_message(
    payload: AgentRequest,
    reception_service: ReceptionServiceDep,
    current_user: OptionalUser,
) -> AgentResponse:
    """
    Accept a visitor message, run Triage (and Booking when needed),
    save the conversation, and return the agent reply.
    """
    # Only attach user_id from a verified JWT — never trust payload.user_id.
    user_id = current_user.id if current_user is not None else None

    try:
        return reception_service.handle_message(
            message=payload.message,
            session_id=payload.session_id,
            user_id=user_id,
            conversation_history=payload.conversation_history,
            metadata=payload.metadata,
        )
    except RuntimeError as exc:
        # Typically missing GROQ_API_KEY during agent/LLM init.
        logger.exception("Reception agents unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Reception message handling failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Reception agents failed to process the message",
        ) from exc
