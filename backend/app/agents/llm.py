"""
Shared Groq LLM factory for all CrewAI agents.

CrewAI routes provider-prefixed models (e.g. groq/...) through LiteLLM.
Every agent must receive this LLM explicitly so CrewAI does not fall
back to OpenAI defaults.
"""

from __future__ import annotations

import os

from crewai import LLM

from app.core.config import get_settings


def get_groq_llm(
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> LLM:
    """Build a Groq-backed CrewAI LLM from application settings."""
    settings = get_settings()

    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Set it in the environment or .env file."
        )

    # Ensure LiteLLM / CrewAI see the key even if Settings was loaded first.
    os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)

    model = settings.groq_model
    if not model.startswith("groq/"):
        model = f"groq/{model}"

    return LLM(
        model=model,
        api_key=settings.groq_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
