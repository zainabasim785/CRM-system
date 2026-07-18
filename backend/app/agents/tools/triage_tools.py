"""FAQ and escalation helpers for the Triage Agent."""

from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.faq_service import get_faq_service


class FAQLookupInput(BaseModel):
    query: str = Field(..., description="User question to match against FAQs")


class FAQLookupTool(BaseTool):
    name: str = "faq_lookup"
    description: str = (
        "Search the company FAQ knowledge base (local JSON) for an answer. "
        "Use this before inventing policy answers."
    )
    args_schema: Type[BaseModel] = FAQLookupInput

    def _run(self, query: str) -> str:
        match = get_faq_service().find_match(query)
        if match is None:
            return json.dumps(
                {
                    "matched": False,
                    "message": (
                        "No confident FAQ match found. Classify intent and continue: "
                        "booking, cancel, reschedule, escalate, or general."
                    ),
                }
            )

        return json.dumps(
            {
                "matched": True,
                "question": match["question"],
                "answer": match["answer"],
                "score": match["score"],
            }
        )


class EscalationInput(BaseModel):
    reason: str = Field(..., description="Why the conversation should be escalated")
    user_message: str = Field(..., description="Latest user message")
    urgency: str = Field(
        default="normal",
        description="Urgency level: low | normal | high | critical",
    )


class FlagEscalationTool(BaseTool):
    name: str = "flag_escalation"
    description: str = (
        "Flag the conversation for human receptionist escalation when the user "
        "is angry, requests a human, reports an emergency, or the request is "
        "outside the AI receptionist's scope."
    )
    args_schema: Type[BaseModel] = EscalationInput

    def _run(self, reason: str, user_message: str, urgency: str = "normal") -> str:
        return (
            "ESCALATION_FLAGGED\n"
            f"urgency={urgency}\n"
            f"reason={reason}\n"
            f"user_message={user_message}\n"
            "A human receptionist should take over this conversation."
        )


def get_triage_tools() -> list[BaseTool]:
    return [FAQLookupTool(), FlagEscalationTool()]
