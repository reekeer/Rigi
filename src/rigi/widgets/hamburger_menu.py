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
class MenuItemData:
    label: str
    callback: Callable[[], Any] | None = None
    checked: bool = False
    submenu: list[MenuItemData] | None = None
    is_back: bool = False


class _ItemClicked(Message):
    def __init__(self, item: MenuItemData) -> None:
        super().__init__()
        self.item = item


class MenuItem(Widget):
    def __init__(self, item: MenuItemData) -> None:
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
    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        yield Label(f"── {self._title}")


class MenuPanel(Widget):
    def __init__(
        self,
        sections: list[tuple[str, list[MenuItemData]]],
        title: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._sections = sections
        self._sections_stack: list[list[tuple[str, list[MenuItemData]]]] = []
        if title:
            self.border_title = title

    def compose(self) -> ComposeResult:
        for title, items in self._sections:
            if title:
                yield _MenuSectionLabel(title)
            for item in items:
                yield MenuItem(item)

    def replace_sections(self, sections: list[tuple[str, list[MenuItemData]]]) -> None:
        self._sections = sections
        self.remove_children()
        for title, items in sections:
            if title:
                self.mount(_MenuSectionLabel(title))
            for item in items:
                self.mount(MenuItem(item))

    def on__item_clicked(self, event: _ItemClicked) -> None:
        event.stop()
        item = event.item
        if item.is_back:
            self._go_back()
        elif item.submenu is not None:
            self._enter_submenu(item)
        elif item.callback is not None:
            callback = item.callback
            self.remove()
            self.app.call_after_refresh(callback)

    def _enter_submenu(self, item: MenuItemData) -> None:
        self._sections_stack.append(self._sections)
        back_item = MenuItemData("Back", is_back=True)
        self._sections = [("", [back_item] + list(item.submenu or []))]
        self.border_title = item.label
        self.replace_sections(self._sections)

    def _go_back(self) -> None:
        if self._sections_stack:
            self._sections = self._sections_stack.pop()
            self.border_title = ""
            self.replace_sections(self._sections)
        else:
            self.remove()


HamburgerPanel = MenuPanel
