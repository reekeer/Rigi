from __future__ import annotations

from uuid import uuid4

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.notifications import SeverityLevel
from textual.widget import Widget
from textual.widgets import Button, Label

_SEVERITY_STYLE: dict[str, str] = {
    "information": "bold cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
}


class _DismissNotification(Message):
    def __init__(self, notification_id: str) -> None:
        super().__init__()
        self.notification_id = notification_id


class RigiNotificationWidget(Widget):
    def __init__(
        self,
        notification_id: str,
        title: str,
        message: str,
        severity: SeverityLevel = "information",
        timeout: float = 5.0,
    ) -> None:
        super().__init__()
        self._notification_id = notification_id
        self._title = title
        self._message = message
        self._severity = severity
        self._timeout = timeout
        self.add_class(f"notif--{severity}")

    def compose(self) -> ComposeResult:
        style = _SEVERITY_STYLE.get(self._severity, "bold white")
        with Widget(classes="notif-header"):
            title_text = f"[{style}]{self._title}[/{style}]" if self._title else " "
            yield Label(title_text, classes="notif-title", markup=True)
            yield Button("×", classes="notif-close")
        if self._message:
            yield Label(self._message, classes="notif-message", markup=True)

    def on_mount(self) -> None:
        if self._timeout > 0:
            self.set_timer(self._timeout, self._expire)

    def _expire(self) -> None:
        self.post_message(_DismissNotification(self._notification_id))

    @on(Button.Pressed, ".notif-close")
    def on_close_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self._expire()


class RigiNotificationRack(Widget):
    def compose(self) -> ComposeResult:
        yield from []

    def add_notification(
        self,
        title: str,
        message: str,
        severity: SeverityLevel = "information",
        timeout: float = 5.0,
    ) -> str:
        notification_id = str(uuid4())
        notif = RigiNotificationWidget(notification_id, title, message, severity, timeout)
        self.mount(notif)
        return notification_id

    @on(_DismissNotification)
    def on_dismiss(self, event: _DismissNotification) -> None:
        event.stop()
        for widget in self.query(RigiNotificationWidget):
            if widget._notification_id == event.notification_id:
                widget.remove()
                return
