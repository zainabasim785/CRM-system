"""
Follow-up Agent — conversation memory and reminder specialist.

Responsibilities:
- Log conversations for CRM / reception records
- Generate concise conversation summaries
- Schedule follow-up reminders
"""

from __future__ import annotations

from crewai import Agent, LLM, Task

from app.agents.tools.followup_tools import get_followup_tools


FOLLOWUP_ROLE = "AI Reception Follow-up Specialist"
FOLLOWUP_GOAL = (
    "Capture an accurate conversation log, write a crisp summary, and schedule "
    "any useful follow-up reminder for the receptionist or visitor."
)
FOLLOWUP_BACKSTORY = (
    "You are the office's after-call clerk. You never omit important commitments, "
    "appointment changes, or escalation notes. You log first, summarize clearly, "
    "and only schedule reminders when there is a concrete next step or appointment."
)


def create_followup_agent(llm: LLM, *, verbose: bool = False) -> Agent:
    """Instantiate the Follow-up Agent with Groq LLM and follow-up tools."""
    return Agent(
        role=FOLLOWUP_ROLE,
        goal=FOLLOWUP_GOAL,
        backstory=FOLLOWUP_BACKSTORY,
        llm=llm,
        tools=get_followup_tools(),
        verbose=verbose,
        allow_delegation=False,
        max_iter=6,
    )


def build_followup_task(
    agent: Agent,
    session_id: str,
    transcript_json: str,
    assistant_reply: str,
    intent: str,
) -> Task:
    """Build the post-turn logging / summary / reminder task."""
    return Task(
        description=(
            f"Session ID: {session_id}\n"
            f"Intent handled this turn: {intent}\n"
            f"Latest assistant reply to include in the record:\n{assistant_reply}\n\n"
            f"Transcript JSON:\n{transcript_json}\n\n"
            "Instructions:\n"
            "1. Write a 2–4 sentence conversation summary covering visitor intent, "
            "outcome, and any open items.\n"
            "2. Call log_conversation with session_id, the transcript JSON "
            "(include the latest assistant reply as an assistant message if missing), "
            "and your summary.\n"
            "3. If there is an appointment, promised callback, or escalation, call "
            "schedule_reminder with an ISO-8601 remind_at (default +24 hours UTC if "
            "no better time is known) and a short note.\n"
            "4. If no reminder is warranted, skip scheduling.\n\n"
            "Return ONLY valid JSON with this shape:\n"
            "{\n"
            '  "logged": true,\n'
            '  "summary": "<summary>",\n'
            '  "reminder_scheduled": false,\n'
            '  "reminder_details": {}\n'
            "}"
        ),
        expected_output=(
            "A single JSON object with keys logged, summary, reminder_scheduled, "
            "reminder_details."
        ),
        agent=agent,
    )
