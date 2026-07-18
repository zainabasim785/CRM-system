"""
AgentManager — coordinates Triage, Booking, and Follow-up agents.

Flow per visitor turn:
1. Triage classifies intent / answers FAQs / flags escalation
2. Booking runs when the intent is scheduling-related
3. Follow-up always logs the turn and may schedule a reminder
"""

from __future__ import annotations

import json
import logging
import re
import time
from uuid import uuid4

from crewai import Crew, Process

from app.agents.booking_agent import build_booking_task, create_booking_agent
from app.agents.followup_agent import build_followup_task, create_followup_agent
from app.agents.llm import get_groq_llm
from app.agents.triage_agent import build_triage_task, create_triage_agent
from app.core.config import get_settings
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    BookingResult,
    FollowUpResult,
    IntentType,
    TriageResult,
)
from app.services.faq_service import FaqService, get_faq_service
from app.utils.json_extract import crew_output_to_text, extract_json_object

logger = logging.getLogger(__name__)

BOOKING_INTENTS = {
    IntentType.BOOKING,
    IntentType.CANCEL,
    IntentType.RESCHEDULE,
    IntentType.AVAILABILITY,
}

# Actionable scheduling language — do not short-circuit these to FAQ answers.
_SCHEDULING_REQUEST = re.compile(
    r"\b("
    r"tomorrow|today|tonight|next\s+\w+|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"\d{1,2}(:\d{2})?\s*(am|pm)|"
    r"cancel\s+my|reschedule\s+my|book\s+me|book\s+an?\s+appointment\s+for|"
    r"book(?:ing)?\s+for|\bbook\b|\bbooking\b|"
    r"i\s+want\s+to\s+book|i('d| would)?\s+like\s+to\s+book"
    r")\b",
    re.IGNORECASE,
)

_CANCEL_REQUEST = re.compile(r"\b(cancel|cancellation)\b", re.IGNORECASE)
_RESCHEDULE_REQUEST = re.compile(r"\b(reschedule|move\s+(my|the)\s+appointment)\b", re.IGNORECASE)


def _scheduling_intent(message: str) -> IntentType | None:
    """Map clear scheduling language to an intent without calling triage LLM."""
    if not _SCHEDULING_REQUEST.search(message or ""):
        return None
    if _CANCEL_REQUEST.search(message) and not re.search(
        r"\b(book|booking|schedule|reserve)\b", message or "", re.IGNORECASE
    ):
        return IntentType.CANCEL
    if _RESCHEDULE_REQUEST.search(message) and not re.search(
        r"\b(book|booking|schedule|reserve)\b", message or "", re.IGNORECASE
    ):
        return IntentType.RESCHEDULE
    return IntentType.BOOKING


_RATE_LIMIT_MARKERS = ("rate_limit", "ratelimit", "tokens per minute", "tpm")


def _is_rate_limit_error(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "ratelimit" in name or any(marker in text for marker in _RATE_LIMIT_MARKERS)


def _kickoff_with_retry(crew: Crew, *, attempts: int = 3) -> object:
    """Run crew.kickoff with short backoff on Groq TPM rate limits."""
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return crew.kickoff()
        except Exception as exc:
            last_exc = exc
            if not _is_rate_limit_error(exc) or attempt >= attempts:
                raise
            wait_s = 12 * attempt
            logger.warning(
                "Groq rate limit on crew kickoff (attempt %s/%s); sleeping %ss",
                attempt,
                attempts,
                wait_s,
            )
            time.sleep(wait_s)
    assert last_exc is not None
    raise last_exc



class AgentManager:
    """Orchestrates the three reception agents with Groq-backed CrewAI crews."""

    def __init__(
        self,
        *,
        verbose: bool | None = None,
        faq_service: FaqService | None = None,
    ) -> None:
        settings = get_settings()
        self.verbose = settings.debug if verbose is None else verbose
        self.faq = faq_service or get_faq_service()
        self._settings = settings
        self._llm = None
        self._triage_agent = None
        self._booking_agent = None
        self._followup_agent = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_groq_llm()
        return self._llm

    @property
    def triage_agent(self):
        if self._triage_agent is None:
            self._triage_agent = create_triage_agent(self.llm, verbose=self.verbose)
        return self._triage_agent

    @property
    def booking_agent(self):
        if self._booking_agent is None:
            self._booking_agent = create_booking_agent(self.llm, verbose=self.verbose)
        return self._booking_agent

    @property
    def followup_agent(self):
        if self._followup_agent is None:
            self._followup_agent = create_followup_agent(self.llm, verbose=self.verbose)
        return self._followup_agent

    def handle_message(self, request: AgentRequest) -> AgentResponse:
        """Process one visitor message through triage → booking → follow-up."""
        session_id = request.session_id or str(uuid4())
        history_blob = self._format_history(request)

        # FAQ knowledge base first — answer from JSON without calling the LLM.
        triage = self._try_faq_answer(request.message)
        scheduled_intent = _scheduling_intent(request.message or "")
        if triage is None and scheduled_intent is not None:
            # Skip triage LLM for clear scheduling language (saves tokens / rate limits).
            triage = TriageResult(
                intent=scheduled_intent,
                confidence=0.9,
                response="",
                needs_escalation=False,
                escalate_reason=None,
                faq_matched=False,
                raw_output=None,
            )
        elif triage is None:
            triage = self._run_triage(request.message, history_blob)

        reply = triage.response
        booking: BookingResult | None = None

        if triage.needs_escalation or triage.intent == IntentType.ESCALATE:
            if not reply:
                reply = (
                    "I'm connecting you with a human receptionist. "
                    "Someone will assist you shortly."
                )
            triage.needs_escalation = True
        elif triage.intent in BOOKING_INTENTS:
            booking = self._run_booking(request.message, triage.intent.value, history_blob)
            reply = booking.response or reply

        if not reply:
            reply = (
                "Thanks for reaching out. Could you share a bit more about "
                "how I can help — booking, cancelling, or a general question?"
            )

        # FAQ answers come from JSON — skip CrewAI follow-up; ReceptionService logs the turn.
        # Also skip follow-up for booking turns to conserve Groq TPM on free tier.
        if triage.faq_matched or triage.intent in BOOKING_INTENTS:
            follow_up = FollowUpResult(
                logged=False,
                summary=(
                    "FAQ answered from local knowledge base"
                    if triage.faq_matched
                    else "Follow-up skipped for scheduling turn"
                ),
                reminder_scheduled=False,
                raw_output=None,
            )
        else:
            follow_up = self._run_followup(
                session_id=session_id,
                request=request,
                assistant_reply=reply,
                intent=triage.intent.value,
            )

        return AgentResponse(
            session_id=session_id,
            intent=triage.intent,
            reply=reply,
            needs_escalation=triage.needs_escalation,
            escalate_reason=triage.escalate_reason,
            triage=triage,
            booking=booking,
            follow_up=follow_up,
            metadata=request.metadata,
        )

    def _try_faq_answer(self, message: str) -> TriageResult | None:
        """If the message matches the FAQ JSON KB, return that answer (no LLM)."""
        if _SCHEDULING_REQUEST.search(message or ""):
            return None

        match = self.faq.find_match(message)
        if match is None:
            return None

        confidence = min(1.0, 0.55 + 0.1 * float(match["score"]))
        logger.info(
            "FAQ knowledge base hit: %s (score=%s)",
            match["question"],
            match["score"],
        )
        return TriageResult(
            intent=IntentType.FAQ,
            confidence=confidence,
            response=match["answer"],
            needs_escalation=False,
            escalate_reason=None,
            faq_matched=True,
            raw_output=json.dumps(
                {
                    "source": "faq_knowledge_base",
                    "question": match["question"],
                    "score": match["score"],
                }
            ),
        )

    def _run_triage(self, message: str, history_blob: str) -> TriageResult:
        task = build_triage_task(self.triage_agent, message, history_blob)
        crew = Crew(
            agents=[self.triage_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
            memory=False,
        )
        raw_text = crew_output_to_text(_kickoff_with_retry(crew))
        payload = extract_json_object(raw_text)

        intent = self._parse_intent(payload.get("intent"))
        return TriageResult(
            intent=intent,
            confidence=float(payload.get("confidence") or 0.0),
            response=str(payload.get("response") or raw_text or ""),
            needs_escalation=bool(payload.get("needs_escalation")),
            escalate_reason=payload.get("escalate_reason"),
            faq_matched=bool(payload.get("faq_matched")),
            raw_output=raw_text,
        )

    def _run_booking(
        self,
        message: str,
        intent: str,
        history_blob: str,
    ) -> BookingResult:
        # Prefer a single small LLM call + AppointmentService (avoids CrewAI TPM blowups).
        if intent in {IntentType.BOOKING.value, IntentType.AVAILABILITY.value, "booking", "availability"}:
            try:
                from app.agents.lightweight_booking import run_lightweight_booking

                return run_lightweight_booking(
                    message=message,
                    intent=intent,
                    history_blob=history_blob,
                )
            except Exception:
                logger.exception(
                    "Lightweight booking failed; falling back to CrewAI booking agent"
                )

        task = build_booking_task(self.booking_agent, message, intent, history_blob)
        crew = Crew(
            agents=[self.booking_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
            memory=False,
        )
        raw_text = crew_output_to_text(_kickoff_with_retry(crew))
        payload = extract_json_object(raw_text)

        return BookingResult(
            success=bool(payload.get("success")),
            action=payload.get("action"),
            response=str(payload.get("response") or raw_text or ""),
            appointment_details=dict(payload.get("appointment_details") or {}),
            raw_output=raw_text,
        )

    def _run_followup(
        self,
        *,
        session_id: str,
        request: AgentRequest,
        assistant_reply: str,
        intent: str,
    ) -> FollowUpResult:
        transcript = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        transcript.append({"role": "user", "content": request.message})
        transcript.append({"role": "assistant", "content": assistant_reply})

        task = build_followup_task(
            agent=self.followup_agent,
            session_id=session_id,
            transcript_json=json.dumps(transcript),
            assistant_reply=assistant_reply,
            intent=intent,
        )
        crew = Crew(
            agents=[self.followup_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
            memory=False,
        )

        try:
            raw_text = crew_output_to_text(_kickoff_with_retry(crew, attempts=2))
        except Exception:
            logger.exception("Follow-up agent failed; continuing without blocking reply")
            return FollowUpResult(
                logged=False,
                summary="",
                reminder_scheduled=False,
                raw_output=None,
            )

        payload = extract_json_object(raw_text)
        return FollowUpResult(
            logged=bool(payload.get("logged")),
            summary=str(payload.get("summary") or ""),
            reminder_scheduled=bool(payload.get("reminder_scheduled")),
            reminder_details=dict(payload.get("reminder_details") or {}),
            raw_output=raw_text,
        )

    @staticmethod
    def _format_history(request: AgentRequest) -> str:
        if not request.conversation_history:
            return ""
        lines = [
            f"{msg.role}: {msg.content}"
            for msg in request.conversation_history[-12:]
        ]
        return "\n".join(lines)

    @staticmethod
    def _parse_intent(value: object) -> IntentType:
        if isinstance(value, IntentType):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            try:
                return IntentType(normalized)
            except ValueError:
                aliases = {
                    "book": IntentType.BOOKING,
                    "schedule": IntentType.BOOKING,
                    "appointment": IntentType.BOOKING,
                    "human": IntentType.ESCALATE,
                    "agent": IntentType.ESCALATE,
                    "support": IntentType.ESCALATE,
                }
                return aliases.get(normalized, IntentType.GENERAL)
        return IntentType.GENERAL


_manager: AgentManager | None = None


def get_agent_manager() -> AgentManager:
    """Lazy singleton used by API / worker layers later."""
    global _manager
    if _manager is None:
        _manager = AgentManager()
    return _manager
