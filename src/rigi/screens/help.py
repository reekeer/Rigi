"""RigiHelpScreen — full-screen keyboard-shortcut reference."""

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


class RigiHelpScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    RigiHelpScreen { align: center middle; }
    RigiHelpScreen > #help-container {
        width: 60; height: auto; max-height: 80%;
        border: round #30363d; background: #0d1117;
        padding: 1 2; overflow-y: auto;
    }
    RigiHelpScreen #help-title {
        text-style: bold; color: #58a6ff;
        width: 100%; content-align: center middle; margin-bottom: 1; height: 1;
    }
    RigiHelpScreen .help-category { color: #30363d; text-style: bold; margin-top: 1; height: 1; }
    RigiHelpScreen .help-row { layout: horizontal; height: 1; width: 100%; }
    RigiHelpScreen .help-key { width: 16; color: #e3b341; text-style: bold; }
    RigiHelpScreen .help-desc { width: 1fr; color: #8b949e; }
    RigiHelpScreen #help-dismiss {
        margin-top: 1; color: #6e7681; content-align: center middle; width: 100%; height: 1;
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
