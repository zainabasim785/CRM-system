"""Pydantic contracts for agent orchestration I/O."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    FAQ = "faq"
    BOOKING = "booking"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    AVAILABILITY = "availability"
    ESCALATE = "escalate"
    GENERAL = "general"
    FOLLOW_UP = "follow_up"


class ConversationMessage(BaseModel):
    role: str = Field(..., description="speaker role: user | assistant | system")
    content: str


class AgentRequest(BaseModel):
    """Inbound payload processed by AgentManager."""

    message: str = Field(..., min_length=1)
    session_id: str | None = None
    user_id: str | None = None
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TriageResult(BaseModel):
    intent: IntentType = IntentType.GENERAL
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    response: str = ""
    needs_escalation: bool = False
    escalate_reason: str | None = None
    faq_matched: bool = False
    raw_output: str | None = None


class BookingResult(BaseModel):
    success: bool = False
    action: str | None = None
    response: str = ""
    appointment_details: dict[str, Any] = Field(default_factory=dict)
    raw_output: str | None = None


class FollowUpResult(BaseModel):
    logged: bool = False
    summary: str = ""
    reminder_scheduled: bool = False
    reminder_details: dict[str, Any] = Field(default_factory=dict)
    raw_output: str | None = None


class AgentResponse(BaseModel):
    """Unified response returned by AgentManager."""

    session_id: str | None = None
    intent: IntentType = IntentType.GENERAL
    reply: str
    needs_escalation: bool = False
    escalate_reason: str | None = None
    triage: TriageResult | None = None
    booking: BookingResult | None = None
    follow_up: FollowUpResult | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
