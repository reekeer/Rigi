"""Simple clickable checkbox widget for Rigi."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.events import Click, Key
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label


class RigiCheckbox(Widget):
    """A simple checkbox with a clickable label.

    Posts ``RigiCheckbox.Changed`` when toggled.
    """

    can_focus = True

    class Changed(Message):
        def __init__(self, value: bool) -> None:
            super().__init__()
            self.value = value

    def __init__(self, label: str = "", value: bool = False) -> None:
        super().__init__()
        self._label = label
        self._value = value

    def compose(self) -> ComposeResult:
        yield Label(self._render_text(), id="rigi-checkbox-label")

    def _render_text(self) -> str:
        box = "[green]✓[/green]" if self._value else " "
        return f"[{box}] {self._label}"

    def on_click(self, event: Click) -> None:
        event.stop()
        self.toggle()

    def on_key(self, event: Key) -> None:
        if event.key in ("enter", "space"):
            event.stop()
            self.toggle()

    def toggle(self) -> None:
        self._value = not self._value
        try:
            self.query_one("#rigi-checkbox-label", Label).update(self._render_text())
        except Exception:
            pass
        self.post_message(self.Changed(self._value))

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, v: bool) -> None:
        if v != self._value:
            self._value = v
            try:
                self.query_one("#rigi-checkbox-label", Label).update(self._render_text())
            except Exception:
                pass
