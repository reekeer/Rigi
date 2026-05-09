from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label

from rigi.core.types import StatusItem


class RigiStatusItem(Widget):
    DEFAULT_CSS = """
    RigiStatusItem {
        height: 1;
        padding: 0 1;
        width: auto;
        content-align: left middle;
        background: transparent;
    }
    """

    def __init__(self, item: StatusItem) -> None:
        super().__init__(id=f"status-{item.key}")
        self._item = item

    def compose(self) -> ComposeResult:
        yield Label("", id=f"slbl-{self._item.key}")

    def on_mount(self) -> None:
        self._refresh_value()
        self.set_interval(self._item.refresh_interval, self._refresh_value)

    def _refresh_value(self) -> None:
        try:
            val = self._item.value_fn()
            lbl = self.query_one(f"#slbl-{self._item.key}", Label)
            lbl.update(f"[{self._item.style}]{self._item.label}:[/] {val}")
        except Exception:
            pass


class _StatusSpacer(Widget):
    DEFAULT_CSS = """
    _StatusSpacer { width: 1fr; height: 1; background: transparent; }
    """

    def render(self) -> str:
        return ""


class _IconButton(Widget):
    """Generic icon button for the status bar."""

    DEFAULT_CSS = """
    _IconButton {
        width: 3;
        height: 1;
        content-align: center middle;
        color: #6e7681;
        background: transparent;
    }
    _IconButton:hover { color: #c9d1d9; }
    """

    class Clicked(Message):
        def __init__(self, key: str) -> None:
            super().__init__()
            self.key = key

    def __init__(self, icon: str, key: str) -> None:
        super().__init__()
        self._icon = icon
        self._key = key

    def compose(self) -> ComposeResult:
        yield Label(self._icon)

    def on_click(self) -> None:
        self.post_message(_IconButton.Clicked(self._key))


class _HamburgerButton(Widget):
    DEFAULT_CSS = """
    _HamburgerButton {
        width: 5;
        height: 1;
        content-align: center middle;
        color: #6e7681;
        background: transparent;
    }
    _HamburgerButton:hover { color: #c9d1d9; }
    """

    class Clicked(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Label("☰")

    def on_click(self) -> None:
        self.post_message(_HamburgerButton.Clicked())


class _HomeButton(Widget):
    DEFAULT_CSS = """
    _HomeButton {
        width: 5;
        height: 1;
        padding: 0 0 0 1;
        content-align: left middle;
        color: #6e7681;
        background: transparent;
    }
    _HomeButton:hover { color: #c9d1d9; }
    _HomeButton.--active { color: #58a6ff; }
    """

    class Clicked(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Label("⌂")

    def on_click(self) -> None:
        self.post_message(_HomeButton.Clicked())

    def set_active(self, active: bool) -> None:
        self.set_class(active, "--active")


class RigiStatusBar(Widget):
    DEFAULT_CSS = """
    RigiStatusBar {
        height: 2;
        layout: horizontal;
        padding: 0 1;
        background: transparent;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._items: list[StatusItem] = []

    def add_item(self, item: StatusItem) -> None:
        self._items.append(item)
        if self.is_mounted:
            spacer = self.query_one(_StatusSpacer)
            self.mount(RigiStatusItem(item), before=spacer)

    def set_home_active(self, active: bool) -> None:
        try:
            self.query_one(_HomeButton).set_active(active)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield _HomeButton()
        for item in self._items:
            yield RigiStatusItem(item)
        yield _StatusSpacer()
        yield _HamburgerButton()
