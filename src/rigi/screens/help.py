"""HelpScreen — full-screen keyboard-shortcut reference."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Label

from rigi.core.types import HelpEntry

BUILTIN_SHORTCUTS: list[HelpEntry] = [
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


class HelpScreen(ModalScreen[None]):
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

            all_entries = BUILTIN_SHORTCUTS + self._entries
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
