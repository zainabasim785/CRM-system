"""
Booking Agent — Google Calendar scheduling specialist.

Responsibilities:
- Check calendar availability
- Create appointments
- Cancel appointments
- Reschedule appointments
"""

from __future__ import annotations

from crewai import Agent, LLM, Task

from app.agents.tools.calendar_tools import get_booking_tools


BOOKING_ROLE = "AI Reception Booking Specialist"
BOOKING_GOAL = (
    "Help visitors check availability and manage appointments — create, cancel, "
    "or reschedule — keeping Google Calendar and the database synchronized."
)
BOOKING_BACKSTORY = (
    "You are a reliable office scheduler. You never invent free slots or IDs. "
    "You always use tools to check availability, create, list, cancel, or "
    "reschedule. Prefer appointment_id from prior bookings or list_appointments. "
    "When required details are missing, ask clearly instead of guessing."
)


def create_booking_agent(llm: LLM, *, verbose: bool = False) -> Agent:
    """Instantiate the Booking Agent with Groq LLM and calendar tools."""
    return Agent(
        role=BOOKING_ROLE,
        goal=BOOKING_GOAL,
        backstory=BOOKING_BACKSTORY,
        llm=llm,
        tools=get_booking_tools(),
        verbose=verbose,
        allow_delegation=False,
        max_iter=8,
    )


def build_booking_task(
    agent: Agent,
    user_message: str,
    intent: str,
    history_blob: str,
) -> Task:
    """Build a booking / cancel / reschedule / availability task."""
    return Task(
        description=(
            f"Detected scheduling intent: {intent}\n\n"
            f"Conversation history:\n{history_blob or '(none)'}\n\n"
            f"Latest visitor message:\n{user_message}\n\n"
            "Instructions:\n"
            "1. For availability or new bookings: call check_calendar_availability "
            "before create_appointment when a concrete time range is known.\n"
            "2. For new bookings: call create_appointment with summary, start, end, "
            "and attendee_email when available. On success, use the tool's "
            "confirmation / message (includes date and time) as the visitor reply. "
            "If the tool returns available=false with alternative_slots, offer those "
            "three options instead of confirming.\n"
            "3. For cancellations or reschedules: if appointment_id / event_id is "
            "unknown, call list_appointments first (filter by attendee_email when "
            "known), then use the matching appointment_id.\n"
            "4. For cancellations: call cancel_appointment with appointment_id "
            "(preferred) or event_id. Confirm the cancelled date/time in your reply.\n"
            "5. For reschedules: call reschedule_appointment with appointment_id "
            "(preferred) or event_id, plus new_start and new_end. If unavailable, "
            "offer alternative_slots. On success, confirm the new date/time.\n"
            "6. Datetimes must be ISO-8601. If critical details are missing, ask "
            "for them instead of calling tools.\n"
            "7. Put appointment_id, event_id, starts_at, and ends_at from the tool "
            "into appointment_details when available.\n\n"
            "Return ONLY valid JSON with this shape:\n"
            "{\n"
            '  "success": true,\n'
            '  "action": "availability|create|cancel|reschedule|clarify",\n'
            '  "response": "<visitor facing reply with confirmed date and time>",\n'
            '  "appointment_details": {}\n'
            "}"
        ),
        expected_output=(
            "A single JSON object with keys success, action, response, "
            "appointment_details."
        ),
        agent=agent,
    )
