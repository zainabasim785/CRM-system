"""
Lightweight booking path — one small Groq completion + AppointmentService.

Avoids CrewAI's large tool schemas so free-tier Groq TPM is less likely to fail.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import litellm

from app.agents.tools.calendar_tools import appointment_service_session
from app.core.config import get_settings
from app.schemas.agent import BookingResult
from app.utils.json_extract import extract_json_object

logger = logging.getLogger(__name__)

_EXTRACT_SYSTEM = (
    "You extract NEW appointment booking details only. Reply with ONLY JSON. "
    "For booking intents, action must be create or clarify — never cancel/reschedule. "
    "Correct obvious typos (jluy→July). Use the current year if missing. "
    "Default duration is 60 minutes when end is missing. "
    "Prefer PKT (+05:00) for naive local times unless the message says otherwise."
)


def _model_name() -> str:
    settings = get_settings()
    model = settings.groq_model
    if not model.startswith("groq/"):
        model = f"groq/{model}"
    return model


def _is_rate_limit_error(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "ratelimit" in name or "rate_limit" in text or "tokens per minute" in text


def _wait_seconds_from_error(exc: BaseException, default: float = 12.0) -> float:
    import re

    text = str(exc)
    match = re.search(r"try again in\s+([\d.]+)\s*s", text, re.IGNORECASE)
    if match:
        return min(60.0, max(1.0, float(match.group(1)) + 1.0))
    return default


def _looks_like_cancel_or_reschedule(message: str) -> bool:
    import re

    if re.search(r"\b(book|booking|schedule|reserve)\b", message or "", re.IGNORECASE):
        return False
    return bool(
        re.search(r"\b(cancel|reschedule|cancellation)\b", message or "", re.IGNORECASE)
    )


_CANCEL_SYSTEM = (
    "You extract cancel/reschedule appointment details. Reply with ONLY JSON. "
    "Use action: cancel, reschedule, list, or clarify. "
    "Include attendee_email when mentioned. Use ISO-8601 for new_start/new_end when rescheduling."
)


def _chat_json_with_system(
    user_prompt: str,
    system: str,
    *,
    attempts: int = 3,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)

    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = litellm.completion(
                model=_model_name(),
                api_key=settings.groq_api_key,
                temperature=0.1,
                max_tokens=400,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or ""
            return extract_json_object(content)
        except Exception as exc:
            last_exc = exc
            if not _is_rate_limit_error(exc) or attempt >= attempts:
                raise
            wait_s = _wait_seconds_from_error(exc, default=12.0 * attempt)
            logger.warning(
                "Groq rate limit (attempt %s/%s); sleep %.1fs",
                attempt,
                attempts,
                wait_s,
            )
            time.sleep(wait_s)
    assert last_exc is not None
    raise last_exc


def _chat_json(user_prompt: str, *, attempts: int = 3) -> dict[str, Any]:
    return _chat_json_with_system(user_prompt, _EXTRACT_SYSTEM, attempts=attempts)


def _pick_appointment(
    appointments: list[dict[str, Any]],
    *,
    appointment_id: str | None,
    attendee_email: str | None,
) -> dict[str, Any] | None:
    if appointment_id:
        for row in appointments:
            if row.get("appointment_id") == appointment_id:
                return row
    if attendee_email:
        matches = [
            row
            for row in appointments
            if (row.get("attendee_email") or "").lower() == attendee_email.lower()
        ]
        if len(matches) == 1:
            return matches[0]
    if len(appointments) == 1:
        return appointments[0]
    return None


def run_lightweight_cancel_reschedule(
    *,
    message: str,
    intent: str,
    history_blob: str,
) -> BookingResult:
    """Parse cancel/reschedule with one Groq call, then update via AppointmentService."""
    intent_norm = (intent or "cancel").lower().strip()
    if intent_norm not in {"cancel", "reschedule"}:
        if "reschedule" in (message or "").lower():
            intent_norm = "reschedule"
        else:
            intent_norm = "cancel"

    today = datetime.now(UTC).date().isoformat()
    prompt = (
        f"Today (UTC): {today}\n"
        f"Intent hint: {intent_norm}\n"
        f"History:\n{history_blob or '(none)'}\n\n"
        f"Latest message:\n{message}\n\n"
        "Return JSON:\n"
        '  "action": "cancel"|"reschedule"|"list"|"clarify",\n'
        '  "attendee_email": "email or null",\n'
        '  "appointment_id": "uuid or null",\n'
        '  "new_start": "ISO-8601 or null",\n'
        '  "new_end": "ISO-8601 or null",\n'
        '  "response": "short clarify message if action=clarify"\n'
    )
    payload = _chat_json_with_system(prompt, _CANCEL_SYSTEM)
    action = str(payload.get("action") or intent_norm).lower().strip()
    email = payload.get("attendee_email")
    appointment_id = payload.get("appointment_id")

    with appointment_service_session() as service:
        listing = service.list_appointments(
            attendee_email=str(email) if email else None,
            limit=10,
        )
        appointments = listing.get("appointments") or []

        if action == "list" or (action == "clarify" and appointments):
            if not appointments:
                return BookingResult(
                    success=False,
                    action="clarify",
                    response=(
                        "I couldn't find upcoming appointments. "
                        "Share the email used when booking."
                    ),
                    appointment_details={},
                    raw_output=json.dumps(payload),
                )
            lines = "\n".join(
                f"- {a.get('label')} ({a.get('attendee_email') or 'no email'})"
                for a in appointments[:5]
            )
            return BookingResult(
                success=False,
                action="list",
                response=(
                    "Here are upcoming appointments:\n"
                    f"{lines}\n\n"
                    "Reply with which to cancel or reschedule and the new time if moving."
                ),
                appointment_details={"appointments": appointments},
                raw_output=json.dumps(payload),
            )

        if action == "clarify":
            clarify = str(payload.get("response") or "").strip()
            if not clarify:
                clarify = (
                    "To cancel or reschedule, tell me the email on the booking "
                    "and the date/time (example: cancel julia@example.com on July 31 at 3pm)."
                )
            return BookingResult(
                success=False,
                action="clarify",
                response=clarify,
                appointment_details={},
                raw_output=json.dumps(payload),
            )

        target = _pick_appointment(
            appointments,
            appointment_id=str(appointment_id) if appointment_id else None,
            attendee_email=str(email) if email else None,
        )
        if target is None:
            hint = listing.get("message") or "No matching appointment found."
            return BookingResult(
                success=False,
                action="clarify",
                response=(
                    f"{hint} "
                    "Include the attendee email or pick from your upcoming appointments."
                ),
                appointment_details={"appointments": appointments},
                raw_output=json.dumps(payload),
            )

        appt_id = target.get("appointment_id")
        if action == "cancel":
            result = service.cancel_appointment(appointment_id=appt_id)
        else:
            new_start = payload.get("new_start")
            new_end = payload.get("new_end")
            if not new_start:
                return BookingResult(
                    success=False,
                    action="clarify",
                    response=(
                        f"Found “{target.get('summary')}”. "
                        "What new date and time would you like?"
                    ),
                    appointment_details={"appointment": target},
                    raw_output=json.dumps(payload),
                )
            if not new_end:
                try:
                    start_dt = datetime.fromisoformat(str(new_start).replace("Z", "+00:00"))
                    new_end = (start_dt + timedelta(hours=1)).isoformat()
                except ValueError:
                    return BookingResult(
                        success=False,
                        action="clarify",
                        response="I couldn't parse the new time. Try “July 31 at 4pm”.",
                        appointment_details={},
                        raw_output=json.dumps(payload),
                    )
            result = service.reschedule_appointment(
                appointment_id=appt_id,
                new_start=str(new_start),
                new_end=str(new_end),
            )

    success = bool(result.get("success"))
    response = str(result.get("message") or result.get("confirmation") or "")
    return BookingResult(
        success=success,
        action=action,
        response=response or ("Done." if success else "Could not complete that request."),
        appointment_details={
            k: result.get(k)
            for k in (
                "appointment_id",
                "event_id",
                "starts_at",
                "ends_at",
                "status",
            )
            if result.get(k) is not None
        },
        raw_output=json.dumps({"extract": payload, "result": result}, default=str),
    )


def run_lightweight_booking(
    *,
    message: str,
    intent: str,
    history_blob: str,
) -> BookingResult:
    """Parse slots with one small LLM call, then book via AppointmentService."""
    intent_norm = (intent or "booking").lower().strip()

    # Never dump the cancel stub for a new booking request.
    if intent_norm in {"booking", "availability"} and not _looks_like_cancel_or_reschedule(
        message
    ):
        pass
    elif _looks_like_cancel_or_reschedule(message) or intent_norm in {
        "cancel",
        "reschedule",
    }:
        from app.agents.lightweight_booking import run_lightweight_cancel_reschedule

        return run_lightweight_cancel_reschedule(
            message=message,
            intent=intent_norm,
            history_blob=history_blob,
        )

    today = datetime.now(UTC).date().isoformat()
    prompt = (
        f"Today's date (UTC): {today}\n"
        f"Intent: {intent_norm} (NEW booking — use action create or clarify only)\n"
        f"History:\n{history_blob or '(none)'}\n\n"
        f"Latest message:\n{message}\n\n"
        "Return JSON with keys:\n"
        '  "action": "create"|"clarify",\n'
        '  "summary": "short title including visitor name if known",\n'
        '  "start": "ISO-8601 start or null",\n'
        '  "end": "ISO-8601 end or null",\n'
        '  "attendee_email": "email or null",\n'
        '  "attendee_name": "name or null",\n'
        '  "missing": ["list of missing fields"],\n'
        '  "response": "short visitor-facing clarify message if action=clarify"\n'
    )
    payload = _chat_json(prompt)
    action = str(payload.get("action") or "clarify").lower().strip()
    if action in {"cancel", "reschedule"}:
        action = "create" if payload.get("start") else "clarify"

    start = payload.get("start")
    end = payload.get("end")
    summary = str(payload.get("summary") or "").strip() or "Appointment"
    email = payload.get("attendee_email")
    name = payload.get("attendee_name")

    if action != "create" or not start:
        clarify = str(payload.get("response") or "").strip()
        missing = payload.get("missing") or []
        if not clarify:
            needed = (
                ", ".join(str(m) for m in missing) if missing else "date, time, and email"
            )
            clarify = (
                f"I still need a few details to book: {needed}. "
                "Example: Book Julia on July 31 at 3pm, email julia@example.com"
            )
        return BookingResult(
            success=False,
            action="clarify",
            response=clarify,
            appointment_details={},
            raw_output=json.dumps(payload),
        )

    if not end:
        try:
            start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
            end = (start_dt + timedelta(hours=1)).isoformat()
        except ValueError:
            return BookingResult(
                success=False,
                action="clarify",
                response=(
                    "I couldn't parse that start time. "
                    "Please send a date and time like July 31 at 3pm."
                ),
                appointment_details={},
                raw_output=json.dumps(payload),
            )

    with appointment_service_session() as appointments:
        result = appointments.book_appointment(
            summary=summary,
            start=str(start),
            end=str(end),
            attendee_email=str(email) if email else None,
            attendee_name=str(name) if name else None,
            description=None,
            calendar_id="primary",
        )

    success = bool(result.get("success"))
    response = str(result.get("message") or result.get("confirmation") or "")
    if not response and success:
        response = f'Booked "{summary}" from {start} to {end}.'
    if not response and not success:
        alts = result.get("alternative_slots") or []
        if alts:
            response = (
                "That time isn't available. Here are some alternatives:\n"
                + "\n".join(
                    f"- {a.get('starts_at', a.get('start'))} → {a.get('ends_at', a.get('end'))}"
                    for a in alts[:3]
                )
            )
        else:
            response = result.get("message") or "I couldn't complete that booking."

    details = {
        k: result.get(k)
        for k in (
            "appointment_id",
            "event_id",
            "google_event_id",
            "starts_at",
            "ends_at",
            "html_link",
            "summary",
        )
        if result.get(k) is not None
    }

    return BookingResult(
        success=success,
        action="create" if success else "clarify",
        response=response,
        appointment_details=details,
        raw_output=json.dumps({"extract": payload, "book": result}, default=str),
    )
