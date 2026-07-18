"""
Triage Agent — first-line reception intelligence.

Responsibilities:
- Classify user intent (FAQ, booking, cancel, reschedule, escalate, general)
- Answer FAQs from the knowledge base
- Detect when a human receptionist must take over
"""

from __future__ import annotations

from crewai import Agent, LLM, Task

from app.agents.tools.triage_tools import get_triage_tools


TRIAGE_ROLE = "AI Reception Triage Specialist"
TRIAGE_GOAL = (
    "Classify every inbound visitor message, answer FAQs accurately, and decide "
    "whether to escalate to a human or hand off to booking / follow-up flows."
)
TRIAGE_BACKSTORY = (
    "You are the front desk of a professional office. You are calm, concise, and "
    "never invent company policy. You use the FAQ tool before answering common "
    "questions. You escalate when the visitor is upset, asks for a human, reports "
    "an emergency, or needs something outside scheduling and FAQ scope."
)


def create_triage_agent(llm: LLM, *, verbose: bool = False) -> Agent:
    """Instantiate the Triage Agent with Groq LLM and triage tools."""
    return Agent(
        role=TRIAGE_ROLE,
        goal=TRIAGE_GOAL,
        backstory=TRIAGE_BACKSTORY,
        llm=llm,
        tools=get_triage_tools(),
        verbose=verbose,
        allow_delegation=False,
        max_iter=5,
    )


def build_triage_task(agent: Agent, user_message: str, history_blob: str) -> Task:
    """Build the triage classification / FAQ task for a single turn."""
    return Task(
        description=(
            "Analyze the visitor message and recent conversation history.\n\n"
            f"Conversation history:\n{history_blob or '(none)'}\n\n"
            f"Latest visitor message:\n{user_message}\n\n"
            "Instructions:\n"
            "1. Prefer faq_lookup for common policy questions; if it returns "
            "matched=true, set intent=faq, faq_matched=true, and use its answer "
            "verbatim as response (do not rewrite policy).\n"
            "2. Use flag_escalation when a human is required.\n"
            "3. Classify intent as exactly one of: "
            "faq, booking, cancel, reschedule, availability, escalate, general, follow_up.\n"
            "4. Produce a short visitor-facing reply for FAQ/general/escalate cases.\n"
            "5. For booking/cancel/reschedule/availability, keep the reply brief; "
            "a specialist agent will continue.\n\n"
            "Return ONLY valid JSON with this shape:\n"
            "{\n"
            '  "intent": "<intent>",\n'
            '  "confidence": 0.0,\n'
            '  "response": "<visitor facing reply>",\n'
            '  "needs_escalation": false,\n'
            '  "escalate_reason": null,\n'
            '  "faq_matched": false\n'
            "}"
        ),
        expected_output=(
            "A single JSON object with keys intent, confidence, response, "
            "needs_escalation, escalate_reason, faq_matched."
        ),
        agent=agent,
    )
