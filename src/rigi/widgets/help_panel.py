from __future__ import annotations

import inspect
import re
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
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


class RigiHelpScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    RigiHelpScreen {
        align: center middle;
    }
    RigiHelpScreen > #help-container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: round #30363d;
        background: #0d1117;
        padding: 1 2;
    }
    RigiHelpScreen #help-title {
        text-style: bold;
        color: #58a6ff;
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    RigiHelpScreen .help-category {
        color: #30363d;
        text-style: bold;
        margin-top: 1;
    }
    RigiHelpScreen .help-row {
        layout: horizontal;
        height: 1;
        width: 100%;
    }
    RigiHelpScreen .help-key {
        width: 16;
        color: #e3b341;
        text-style: bold;
    }
    RigiHelpScreen .help-desc {
        width: 1fr;
        color: #8b949e;
    }
    RigiHelpScreen #help-dismiss {
        margin-top: 1;
        color: #6e7681;
        content-align: center middle;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("ctrl+h", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
    ]

    def __init__(self, entries: list[HelpEntry]) -> None:
        super().__init__()
        self._entries = entries

    def compose(self) -> ComposeResult:
        with Widget(id="help-container"):
            yield Label("  Help", id="help-title")

            all_entries = _BUILTIN_SHORTCUTS + self._entries
            categories: dict[str, list[HelpEntry]] = {}
            for e in all_entries:
                categories.setdefault(e.category, []).append(e)

            for cat, items in categories.items():
                yield Label(f"── {cat} ──", classes="help-category")
                for item in items:
                    yield Widget(
                        Label(item.key, classes="help-key"),
                        Label(item.description, classes="help-desc"),
                        classes="help-row",
                    )

            yield Label("Esc / Ctrl+H / q  →  close", id="help-dismiss")

    def on_click(self) -> None:
        self.dismiss()


class RigiShortcutsBar(Widget):
    DEFAULT_CSS = """
    RigiShortcutsBar {
        height: 1;
        border-top: solid #21262d;
        layout: horizontal;
        padding: 0 1;
    }
    RigiShortcutsBar Label {
        color: #6e7681;
        padding: 0 1;
    }
    RigiShortcutsBar .shortcut-key {
        color: #e3b341;
        text-style: bold;
    }
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
