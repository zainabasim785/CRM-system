"""Silence CrewAI Rich console output (emoji breaks Windows cp1252)."""

from __future__ import annotations


def silence_crewai_console() -> None:
    try:
        from crewai.utilities.events.event_listener import EventListener
        from crewai.utilities.events.utils.console_formatter import ConsoleFormatter

        def _noop(*_args, **_kwargs):
            return None

        listener = EventListener()
        listener.formatter.verbose = False
        listener.formatter.print = _noop  # type: ignore[method-assign]
        listener.formatter.print_panel = _noop  # type: ignore[method-assign]
        listener.formatter.create_crew_tree = lambda *_a, **_k: None  # type: ignore[method-assign]
        listener.formatter.update_crew_tree = _noop  # type: ignore[method-assign]

        ConsoleFormatter.print = _noop  # type: ignore[method-assign]
        ConsoleFormatter.print_panel = _noop  # type: ignore[method-assign]
    except Exception:
        pass
