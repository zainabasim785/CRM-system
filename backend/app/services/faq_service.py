"""
FAQ knowledge base loaded from a local JSON file.

Used to answer FAQ intents without calling the LLM when a match exists.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_FAQ_PATH = Path(__file__).resolve().parent.parent / "data" / "faqs.json"


def _contains_whole_word(haystack: str, needle: str) -> bool:
    """True when `needle` appears as a whole word (not a substring of another word)."""
    if not needle:
        return False
    return re.search(rf"\b{re.escape(needle)}\b", haystack) is not None


class FaqService:
    """Load and match FAQs from `app/data/faqs.json`."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_FAQ_PATH
        self._entries: list[dict[str, Any]] | None = None

    def load(self) -> list[dict[str, Any]]:
        if self._entries is not None:
            return self._entries

        if not self.path.exists():
            logger.warning("FAQ knowledge base not found at %s", self.path)
            self._entries = []
            return self._entries

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to load FAQ knowledge base from %s", self.path)
            self._entries = []
            return self._entries

        if not isinstance(raw, list):
            logger.error("FAQ knowledge base must be a JSON array: %s", self.path)
            self._entries = []
            return self._entries

        entries: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question") or "").strip()
            answer = str(item.get("answer") or "").strip()
            if not question or not answer:
                continue
            keywords = item.get("keywords") or []
            if isinstance(keywords, str):
                keyword_list = [k.strip() for k in keywords.split() if k.strip()]
            elif isinstance(keywords, list):
                keyword_list = [str(k).strip().lower() for k in keywords if str(k).strip()]
            else:
                keyword_list = []
            entries.append(
                {
                    "question": question,
                    "answer": answer,
                    "keywords": keyword_list,
                }
            )

        self._entries = entries
        logger.info("Loaded %s FAQ entries from %s", len(entries), self.path)
        return self._entries

    def find_match(self, query: str, *, min_score: int = 3) -> dict[str, Any] | None:
        """
        Return the best FAQ match for `query`, or None if below `min_score`.

        Scoring: keyword hits + overlapping question tokens (length > 3).
        """
        normalized = (query or "").lower().strip()
        if not normalized:
            return None

        best: dict[str, Any] | None = None
        best_score = 0

        for entry in self.load():
            # Whole-word matches only — avoid "book" matching inside "booking".
            score = sum(
                1 for keyword in entry["keywords"] if _contains_whole_word(normalized, keyword)
            )
            score += sum(
                1
                for token in entry["question"].lower().split()
                if len(token) > 3 and _contains_whole_word(normalized, token)
            )
            if score > best_score:
                best_score = score
                best = entry

        if best is None or best_score < min_score:
            return None

        return {
            "question": best["question"],
            "answer": best["answer"],
            "score": best_score,
        }

    def answer(self, query: str) -> dict[str, Any] | None:
        """Convenience wrapper used by AgentManager / tools."""
        return self.find_match(query)


@lru_cache
def get_faq_service() -> FaqService:
    return FaqService()
