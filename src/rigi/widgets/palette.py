"""Command palette screen — Ctrl+P fuzzy search over all commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option

if TYPE_CHECKING:
    from rigi.commands.registry import CommandRegistry


def _fuzzy_score(query: str, candidate: str) -> int | None:
    """Return a match score if all query chars appear in-order in candidate."""
    q = query.lower()
    c = candidate.lower()
    if not q:
        return 0
    pos = i = 0
    score = 0
    while i < len(q) and pos < len(c):
        if q[i] == c[pos]:
            # Bonus for consecutive matches and prefix match
            score += 2 if (i > 0 and pos > 0 and q[i - 1] == c[pos - 1]) else 1
            if pos == 0:
                score += 3
            i += 1
        pos += 1
    return score if i == len(q) else None


class RigiPaletteScreen(ModalScreen[str | None]):
    """Ctrl+P command palette with fuzzy search."""

    DEFAULT_CSS = """
    RigiPaletteScreen {
        align: center top;
        layer: overlay;
        background: rgba(0,0,0,0.5);
    }
    RigiPaletteScreen > #palette-container {
        width: 64;
        height: auto;
        max-height: 30;
        margin-top: 3;
        padding: 1 2;
        border: round #30363d;
        background: #0d1117;
    }
    RigiPaletteScreen Input {
        border: none;
        background: transparent;
        width: 100%;
        height: 1;
        padding: 0;
        color: #e6edf3;
    }
    RigiPaletteScreen Input:focus { border: none; }
    RigiPaletteScreen #palette-divider {
        height: 1;
        width: 100%;
        color: #30363d;
    }
    RigiPaletteScreen OptionList {
        border: none;
        padding: 0;
        background: transparent;
        height: auto;
        max-height: 22;
    }
    RigiPaletteScreen #palette-hint {
        height: 1;
        color: #6e7681;
        width: 100%;
        content-align: right middle;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Close", show=False),
        Binding("ctrl+p", "dismiss(None)", "Close", show=False),
    ]

    def __init__(self, registry: CommandRegistry) -> None:
        super().__init__()
        self._registry = registry
        self._all_cmds: list[tuple[str, str]] = [(c.name, c.help) for c in registry.visible()]

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-container"):
            yield Input(placeholder="  Search commands…", id="palette-input")
            yield Label("─" * 58, id="palette-divider")
            yield OptionList(*self._build_options(""), id="palette-list")
            yield Label("↑↓ navigate  Enter select  Esc close", id="palette-hint")

    def on_mount(self) -> None:
        self.query_one("#palette-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        self._refresh_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._select_current()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        name = event.option.id
        if name:
            self.dismiss(name)

    def on_key(self, event: Key) -> None:
        ol = self.query_one("#palette-list", OptionList)
        if event.key == "down":
            ol.action_cursor_down()
            event.stop()
        elif event.key == "up":
            ol.action_cursor_up()
            event.stop()

    def _select_current(self) -> None:
        ol = self.query_one("#palette-list", OptionList)
        try:
            idx = ol.highlighted
            if idx is not None:
                opt = ol.get_option_at_index(idx)
                if opt.id:
                    self.dismiss(opt.id)
                    return
        except Exception:
            pass
        opts = self._build_options(self.query_one("#palette-input", Input).value)
        if len(opts) == 1 and opts[0].id:
            self.dismiss(opts[0].id)
        else:
            self.dismiss(None)

    def _build_options(self, query: str) -> list[Option]:
        scored: list[tuple[int, str, str]] = []
        for name, help_text in self._all_cmds:
            score = _fuzzy_score(query, name)
            if score is not None:
                scored.append((-score, name, help_text))
        scored.sort(key=lambda x: (x[0], x[1]))
        return [
            Option(
                (
                    f"[bold]{name}[/bold]  [dim]{help_text}[/dim]"
                    if help_text
                    else f"[bold]{name}[/bold]"
                ),
                id=name,
            )
            for _, name, help_text in scored
        ]

    def _refresh_list(self, query: str) -> None:
        ol = self.query_one("#palette-list", OptionList)
        ol.clear_options()
        for opt in self._build_options(query):
            ol.add_option(opt)
