from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Key, MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label

if TYPE_CHECKING:
    from rigi.commands.registry import CommandRegistry


class _TerminalInput(Input):
    def on_focus(self) -> None:
        bar = next((w for w in self.ancestors if isinstance(w, TerminalBar)), None)
        if bar is not None:
            bar._on_focus_changed(True)

    def on_blur(self) -> None:
        bar = next((w for w in self.ancestors if isinstance(w, TerminalBar)), None)
        if bar is not None:
            bar._on_focus_changed(False)


class _TerminalResizeHandle(Widget):
    def __init__(self) -> None:
        super().__init__()
        self._drag_y: int | None = None
        self._drag_h: int | None = None

    def render(self) -> str:
        return "─" * self.size.width

    def on_mouse_down(self, event: MouseDown) -> None:
        self.capture_mouse()
        self._drag_y = event.screen_y
        bar = next((w for w in self.ancestors if isinstance(w, TerminalBar)), None)
        if bar is not None:
            self._drag_h = bar.size.height

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._drag_y is None or self._drag_h is None:
            return
        delta = self._drag_y - event.screen_y
        new_h = max(2, self._drag_h + delta)
        bar = next((w for w in self.ancestors if isinstance(w, TerminalBar)), None)
        if bar is not None:
            bar.styles.height = new_h

    def on_mouse_up(self, _: MouseUp) -> None:
        self.release_mouse()
        self._drag_y = None
        self._drag_h = None


class TerminalBar(Widget):
    BINDINGS = [
        Binding("tab", "complete", "Complete", show=False),
    ]

    class CommandSubmitted(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def __init__(
        self,
        prompt_text: str,
        registry: CommandRegistry,
        history_file: Path | None = None,
    ) -> None:
        super().__init__()
        self._prompt_text = prompt_text
        self._cmd_registry = registry
        self._history: list[str] = []
        self._history_pos: int = -1
        self._completion_idx: int = -1
        self._completions: list[str] = []
        self._history_file = history_file
        if history_file:
            self._load_history(history_file)

    def compose(self) -> ComposeResult:
        yield _TerminalResizeHandle()
        with Horizontal(id="input-row"):
            yield Label(self._prompt_label(focused=False), id="terminal-prompt")
            yield _TerminalInput(placeholder="", id="terminal-input")

    def on_click(self) -> None:
        self._input.focus()

    def _prompt_label(self, focused: bool) -> str:
        icon = "[bold]●[/bold]" if focused else "[dim]○[/dim]"
        return f" {icon} {self._prompt_text}: "

    def _on_focus_changed(self, focused: bool) -> None:
        try:
            lbl = self.query_one("#terminal-prompt", Label)
            lbl.update(self._prompt_label(focused))
        except Exception:
            pass

    @property
    def prompt_text(self) -> str:
        return self._prompt_text

    @prompt_text.setter
    def prompt_text(self, value: str) -> None:
        self._prompt_text = value
        try:
            focused = self.query_one("#terminal-input", _TerminalInput).has_focus
            self._on_focus_changed(focused)
        except Exception:
            pass

    @property
    def _input(self) -> _TerminalInput:
        return self.query_one("#terminal-input", _TerminalInput)

    def focus_input(self) -> None:
        self._input.focus()

    def _load_history(self, path: Path) -> None:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            self._history = [ln for ln in lines if ln.strip()][-500:]
        except FileNotFoundError:
            pass
        except Exception:
            pass

    def save_history(self) -> None:
        if not self._history_file:
            return
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            self._history_file.write_text("\n".join(self._history[-500:]), encoding="utf-8")
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        self._completion_idx = -1
        self._completions = self._cmd_registry.completions(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        text = event.value.strip()
        if text:
            self._history.append(text)
            self._history_pos = -1
            self._input.value = ""
            self._completions = []
            self.post_message(TerminalBar.CommandSubmitted(text))

    def action_complete(self) -> None:
        if not self._completions:
            self._completions = self._cmd_registry.completions(self._input.value)
        if not self._completions:
            return
        self._completion_idx = (self._completion_idx + 1) % len(self._completions)
        completion = self._completions[self._completion_idx]
        current = self._input.value
        parts = current.split()
        if len(parts) <= 1 and not current.endswith(" "):
            self._input.value = completion + " "
        else:
            parts[-1] = completion
            self._input.value = " ".join(parts) + " "
        self._input.cursor_position = len(self._input.value)

    def on_key(self, event: Key) -> None:
        if not self._input.has_focus:
            return
        key = event.key
        if key == "up":
            if self._history:
                self._history_pos = min(self._history_pos + 1, len(self._history) - 1)
                self._input.value = self._history[-(self._history_pos + 1)]
                self._input.cursor_position = len(self._input.value)
                event.stop()
        elif key == "down":
            if self._history_pos > 0:
                self._history_pos -= 1
                self._input.value = self._history[-(self._history_pos + 1)]
                self._input.cursor_position = len(self._input.value)
                event.stop()
            elif self._history_pos == 0:
                self._history_pos = -1
                self._input.value = ""
                event.stop()
