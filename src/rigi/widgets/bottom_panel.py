from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key, MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button, ContentSwitcher, Input, Label, RichLog, Select, Tab, Tabs

from rigi.core import log_store

if TYPE_CHECKING:
    from rigi.commands.registry import CommandRegistry


_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": "dim",
    "INFO": "cyan",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold red",
}


class _ResizeHandle(Widget):
    ALLOW_SELECT = False

    def __init__(self) -> None:
        super().__init__()
        self._drag_y: int | None = None
        self._drag_h: int | None = None

    def render(self) -> str:
        return "─" * self.size.width

    def on_mouse_down(self, event: MouseDown) -> None:
        self.capture_mouse()
        self._drag_y = event.screen_y
        panel = next((w for w in self.ancestors if isinstance(w, RigiBottomPanel)), None)
        if panel is not None:
            self._drag_h = panel.size.height

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._drag_y is None or self._drag_h is None:
            return
        delta = self._drag_y - event.screen_y
        new_h = max(4, self._drag_h + delta)
        panel = next((w for w in self.ancestors if isinstance(w, RigiBottomPanel)), None)
        if panel is not None:
            panel.styles.height = new_h

    def on_mouse_up(self, _: MouseUp) -> None:
        self.release_mouse()
        self._drag_y = None
        self._drag_h = None


class _TerminalInput(Input):
    def on_focus(self) -> None:
        panel = next((w for w in self.ancestors if isinstance(w, RigiBottomPanel)), None)
        if panel is not None:
            panel._on_focus_changed(True)

    def on_blur(self) -> None:
        panel = next((w for w in self.ancestors if isinstance(w, RigiBottomPanel)), None)
        if panel is not None:
            panel._on_focus_changed(False)


class _LogsView(Widget):
    def __init__(self) -> None:
        super().__init__()
        self._seen: int = 0
        self._logger_filter: str = "all"
        self._level_filter: str = "all"
        self._known_loggers: list[str] = []
        self._active: bool = False
        self._flush_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield RichLog(highlight=False, markup=True, id="logs-output", auto_scroll=True)
        with Widget(id="logs-controls"):
            yield Label("Logger:")
            yield Select(
                options=[("all", "all")],
                value="all",
                id="sel-logger",
                compact=True,
            )
            yield Label("Level:")
            yield Select(
                options=[
                    ("all", "all"),
                    ("DEBUG", "DEBUG"),
                    ("INFO", "INFO"),
                    ("WARNING", "WARNING"),
                    ("ERROR", "ERROR"),
                    ("CRITICAL", "CRITICAL"),
                ],
                value="all",
                id="sel-level",
                compact=True,
            )
            yield Button("Clear", id="btn-logs-clear", variant="default")

    def on_mount(self) -> None:
        pass

    def activate(self) -> None:
        self._active = True
        self._reset_seen()
        self._flush()
        if self._flush_timer is None:
            self._flush_timer = self.set_interval(0.5, self._flush)

    def deactivate(self) -> None:
        self._active = False
        if self._flush_timer is not None:
            self._flush_timer.stop()
            self._flush_timer = None

    def _flush(self) -> None:
        if not self._active:
            return
        self._refresh_logger_select()
        try:
            view = self.query_one("#logs-output", RichLog)
        except Exception:
            return
        records = log_store.get_records(
            logger_filter=self._logger_filter,
            level_filter=self._level_filter,
        )
        if self._seen > len(records):
            self._seen = 0
            view.clear()
        new_records = records[self._seen :]
        for rec in new_records:
            color = _LEVEL_COLORS.get(rec.level, "white")
            ms = rec.timestamp.microsecond // 1000
            ts = rec.timestamp.strftime("%H:%M:%S") + f".{ms:03d}"
            safe_message = rec.message.replace("[", "\\[")
            view.write(
                f"[dim]{ts}[/dim] "
                f"[bold cyan]{rec.logger_name:<20}[/bold cyan] "
                f"[{color}]{rec.level:<8}[/{color}] "
                f"{safe_message}"
            )
        if new_records:
            self._seen = len(records)

    def _refresh_logger_select(self) -> None:
        try:
            sel = self.query_one("#sel-logger", Select)
        except Exception:
            return
        known = log_store.known_loggers()
        if known == self._known_loggers:
            return
        self._known_loggers = known
        opts: list[tuple[str, str]] = [("all", "all")] + [(n, n) for n in known]
        current_value = sel.value
        sel.set_options(opts)
        if current_value in [v for _, v in opts]:
            sel.value = current_value

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        val = str(event.value) if event.value is not Select.NULL else "all"
        if event.select.id == "sel-logger":
            self._logger_filter = val
        elif event.select.id == "sel-level":
            self._level_filter = val
        self._reset_seen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "btn-logs-clear":
            log_store.clear()
            self._seen = 0
            try:
                self.query_one("#logs-output", RichLog).clear()
            except Exception:
                pass

    def _reset_seen(self) -> None:
        self._seen = 0
        try:
            self.query_one("#logs-output", RichLog).clear()
        except Exception:
            pass


class RigiBottomPanel(Widget):
    BINDINGS = [
        Binding("tab", "complete", "Complete", show=False),
    ]

    active_tab: reactive[str] = reactive("terminal")

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
        yield _ResizeHandle()
        yield Tabs(Tab("Terminal", id="tab-terminal"), Tab("Logs", id="tab-logs"))
        with ContentSwitcher(initial="bp-terminal", id="bp-switcher"):
            with Widget(id="bp-terminal"):
                yield RichLog(highlight=True, markup=True, id="term-history")
                with Widget(id="input-row"):
                    yield Label(self._prompt_label(focused=False), id="terminal-prompt")
                    yield _TerminalInput(placeholder="", id="terminal-input")
            with Widget(id="bp-logs"):
                yield _LogsView()

    @on(Tabs.TabActivated)
    def on_tab_activated(self, event: Tabs.TabActivated) -> None:
        event.stop()
        if event.tab and event.tab.id:
            self.active_tab = event.tab.id.removeprefix("tab-")

    def watch_active_tab(self, value: str) -> None:
        try:
            self.query_one("#bp-switcher", ContentSwitcher).current = f"bp-{value}"
        except Exception:
            pass
        try:
            logs_view = self.query_one(_LogsView)
            if value == "logs":
                logs_view.activate()
            else:
                logs_view.deactivate()
        except Exception:
            pass

    def on_click(self) -> None:
        if self.active_tab == "terminal":
            try:
                self.query_one("#terminal-input").focus()
            except Exception:
                pass

    def _prompt_label(self, focused: bool) -> str:
        icon = "[bold]●[/bold]" if focused else "[dim]○[/dim]"
        return f" {icon} {self._prompt_text}: "

    def _on_focus_changed(self, focused: bool) -> None:
        try:
            self.query_one("#terminal-prompt", Label).update(self._prompt_label(focused))
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

    def focus_input(self) -> None:
        try:
            self.query_one(Tabs).active = "tab-terminal"
        except Exception:
            pass
        try:
            self.query_one("#terminal-input", _TerminalInput).focus()
        except Exception:
            pass

    def _load_history(self, path: Path) -> None:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            self._history = [ln for ln in lines if ln.strip()][-500:]
        except (FileNotFoundError, OSError):
            pass

    def save_history(self) -> None:
        if not self._history_file:
            return
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            self._history_file.write_text("\n".join(self._history[-500:]), encoding="utf-8")
        except Exception:
            pass

    def write_output(self, line: str) -> None:
        try:
            self.query_one("#term-history", RichLog).write(line)
        except Exception:
            pass

    def clear_history_view(self) -> None:
        try:
            self.query_one("#term-history", RichLog).clear()
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "terminal-input":
            return
        event.stop()
        self._completion_idx = -1
        self._completions = self._cmd_registry.completions(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "terminal-input":
            return
        event.stop()
        text = event.value.strip()
        if not text:
            return
        self._history.append(text)
        self._history_pos = -1
        self._completions = []
        try:
            self.query_one("#terminal-input", _TerminalInput).value = ""
        except Exception:
            pass
        self.write_output(f"[bold green]{self._prompt_text}[/bold green] [dim]$[/dim] {text}")
        self.post_message(RigiBottomPanel.CommandSubmitted(text))

    def action_complete(self) -> None:
        if not self._completions:
            try:
                self._completions = self._cmd_registry.completions(
                    self.query_one("#terminal-input", _TerminalInput).value
                )
            except Exception:
                return
        if not self._completions:
            return
        self._completion_idx = (self._completion_idx + 1) % len(self._completions)
        completion = self._completions[self._completion_idx]
        try:
            inp = self.query_one("#terminal-input", _TerminalInput)
            current = inp.value
            parts = current.split()
            if len(parts) <= 1 and not current.endswith(" "):
                inp.value = completion + " "
            else:
                parts[-1] = completion
                inp.value = " ".join(parts) + " "
            inp.cursor_position = len(inp.value)
        except Exception:
            pass

    def on_key(self, event: Key) -> None:
        try:
            if not self.query_one("#terminal-input", _TerminalInput).has_focus:
                return
        except Exception:
            return
        key = event.key
        if key == "up":
            if self._history:
                self._history_pos = min(self._history_pos + 1, len(self._history) - 1)
                try:
                    inp = self.query_one("#terminal-input", _TerminalInput)
                    inp.value = self._history[-(self._history_pos + 1)]
                    inp.cursor_position = len(inp.value)
                except Exception:
                    pass
                event.stop()
        elif key == "down":
            try:
                inp = self.query_one("#terminal-input", _TerminalInput)
                if self._history_pos > 0:
                    self._history_pos -= 1
                    inp.value = self._history[-(self._history_pos + 1)]
                    inp.cursor_position = len(inp.value)
                    event.stop()
                elif self._history_pos == 0:
                    self._history_pos = -1
                    inp.value = ""
                    event.stop()
            except Exception:
                pass
