"""RigiShortcutsBar and help annotation utilities."""

from __future__ import annotations

import inspect
import re
from typing import Callable

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from rigi.core.types import HelpEntry

_BUILTIN_SHORTCUTS: list[HelpEntry] = [
    HelpEntry("Ctrl+Q", "Quit the application", "Navigation"),
    HelpEntry("Ctrl+T", "Focus the terminal input", "Navigation"),
    HelpEntry("Ctrl+H", "Open / close this help panel", "Navigation"),
    HelpEntry("Ctrl+P", "Open command palette (fuzzy search)", "Navigation"),
    HelpEntry("↑ / ↓", "Move through sidebar items", "Navigation"),
    HelpEntry("→ / ←", "Enter / leave subtab group", "Navigation"),
    HelpEntry("Ctrl+C", "Copy focused cell / label to clipboard", "Navigation"),
    HelpEntry("Tab", "Auto-complete command in terminal", "Terminal"),
    HelpEntry("↑ / ↓", "Browse command history", "Terminal"),
    HelpEntry("Enter", "Submit command", "Terminal"),
]


def extract_help_annotation(fn: Callable[..., object] | None) -> str | None:
    if fn is None:
        return None
    doc = inspect.getdoc(fn) or (getattr(fn, "__doc__", "") or "")
    m = re.search(r"@comment_help\s+(.+?)(?:\n\n|\Z)", doc, re.DOTALL)
    return m.group(1).strip() if m else None


class RigiShortcutsBar(Widget):
    DEFAULT_CSS = """
    RigiShortcutsBar {
        height: 1;
        border-top: solid #21262d;
        layout: horizontal;
        padding: 0 1;
    }
    RigiShortcutsBar Label { color: #6e7681; padding: 0 1; }
    """

    HINTS: list[tuple[str, str]] = [
        ("Ctrl+H", "Help"),
        ("Ctrl+P", "Commands"),
        ("↑↓", "Navigate"),
        ("Ctrl+C", "Copy"),
        ("Ctrl+T", "Terminal"),
        ("Ctrl+Q", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        for key, desc in self.HINTS:
            yield Label(f"[bold #e3b341]{key}[/] {desc}")
