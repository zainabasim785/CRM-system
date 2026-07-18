"""Helpers for parsing structured agent outputs."""

from __future__ import annotations

import json
import re
from typing import Any


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    """
    Best-effort parse of a JSON object from an LLM response.

    Handles fenced code blocks and trailing prose.
    """
    if not text:
        return {}

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = _JSON_OBJECT_RE.search(cleaned)
    if not match:
        return {}

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def crew_output_to_text(result: Any) -> str:
    """Normalize CrewAI kickoff result into plain text."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    raw = getattr(result, "raw", None)
    if isinstance(raw, str):
        return raw
    return str(result)
