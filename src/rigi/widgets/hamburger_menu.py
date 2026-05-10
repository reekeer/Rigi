"""Hamburger menu panel widgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from textual.app import ComposeResult
from textual.events import Click
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label


@dataclass
class RigiMenuItemData:
    label: str
    callback: Callable[[], Any] | None = None
    checked: bool = False
    submenu: list[RigiMenuItemData] | None = None
    is_back: bool = False


class _ItemClicked(Message):
    def __init__(self, item: RigiMenuItemData) -> None:
        super().__init__()
        self.item = item


class RigiMenuItem(Widget):
    DEFAULT_CSS = """
    RigiMenuItem { height: 1; width: 100%; padding: 0 1; background: transparent; }
    RigiMenuItem:hover { background: #1c2128; }
    """

    def __init__(self, item: RigiMenuItemData) -> None:
        super().__init__()
        self._item = item

    def compose(self) -> ComposeResult:
        if self._item.is_back:
            yield Label("← Back")
            return
        mark = "[bold]●[/bold] " if self._item.checked else "  "
        arrow = "  [dim]▶[/dim]" if self._item.submenu is not None else ""
        yield Label(f"{mark}{self._item.label}{arrow}")

    def on_click(self, event: Click) -> None:
        event.stop()
        self.post_message(_ItemClicked(self._item))


class _MenuSectionLabel(Widget):
    DEFAULT_CSS = """
    _MenuSectionLabel {
        height: 1; width: 100%; padding: 0 1;
        color: #3d444d; text-style: bold; background: transparent;
    }
    """

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        yield Label(f"── {self._title}")


class RigiMenuPanel(Widget):
    DEFAULT_CSS = """
    RigiMenuPanel {
        width: 26; height: auto; max-height: 24;
        border: round #30363d; border-title-color: #c9d1d9;
        background: #0d1117; padding: 0; overflow-y: auto;
    }
    """

    def __init__(
        self,
        sections: list[tuple[str, list[RigiMenuItemData]]],
        title: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._sections = sections
        if title:
            self.border_title = title

    def compose(self) -> ComposeResult:
        for title, items in self._sections:
            if title:
                yield _MenuSectionLabel(title)
            for item in items:
                yield RigiMenuItem(item)

    def replace_sections(self, sections: list[tuple[str, list[RigiMenuItemData]]]) -> None:
        self._sections = sections
        self.remove_children()
        for title, items in sections:
            if title:
                self.mount(_MenuSectionLabel(title))
            for item in items:
                self.mount(RigiMenuItem(item))


RigiHamburgerPanel = RigiMenuPanel
