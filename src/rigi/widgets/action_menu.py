"""Action menu widget — vertical popup with numbered items and color support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from textual.app import ComposeResult
from textual.events import Click
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label


@dataclass
class ActionMenuItemData:
    label: str
    callback: Callable[[], Any] | None = None
    color: str | None = None
    disabled: bool = False


class _ActionItemClicked(Message):
    def __init__(self, item: ActionMenuItemData) -> None:
        super().__init__()
        self.item = item


class ActionMenuItem(Widget):
    can_focus = False

    def __init__(self, item: ActionMenuItemData, number: int) -> None:
        super().__init__()
        self._item = item
        self._number = number

    def compose(self) -> ComposeResult:
        num_str = f"[dim]{self._number}.[/dim] " if self._number > 0 else ""
        color_prefix = f"[{self._item.color}]" if self._item.color else ""
        color_suffix = f"[/{self._item.color}]" if self._item.color else ""
        label = self._item.label
        if self._item.disabled:
            label = f"[dim]{label}[/dim]"
        yield Label(f"{num_str}{color_prefix}{label}{color_suffix}")

    def on_click(self, event: Click) -> None:
        event.stop()
        if not self._item.disabled and self._item.callback is not None:
            self.post_message(_ActionItemClicked(self._item))


class ActionMenuPanel(Widget):
    def __init__(
        self,
        items: list[ActionMenuItemData],
        title: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._items = items
        if title:
            self.border_title = title

    def compose(self) -> ComposeResult:
        for i, item in enumerate(self._items, start=1):
            yield ActionMenuItem(item, number=i)

    def replace_items(self, items: list[ActionMenuItemData]) -> None:
        self._items = items
        self.remove_children()
        for i, item in enumerate(items, start=1):
            self.mount(ActionMenuItem(item, number=i))
