"""Vertical tab groups for in-page navigation."""

from __future__ import annotations

from typing import Any, Callable

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Label


class _VerticalTabItem(Widget):
    can_focus = False

    def __init__(self, label: str, idx: int) -> None:
        super().__init__()
        self._label = label
        self._idx = idx

    def compose(self) -> ComposeResult:
        yield Label(self._label)

    def set_active(self, active: bool) -> None:
        self.set_class(active, "--active")

    def on_click(self) -> None:
        self.post_message(_VerticalTabClicked(self._idx))
        self.app.set_focus(None)


class _VerticalTabClicked(Message):
    def __init__(self, idx: int) -> None:
        super().__init__()
        self.idx = idx


class RigiVerticalTabs(Widget):
    def __init__(
        self,
        tabs: list[tuple[str, Callable[[], Widget]]],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._tab_defs = tabs
        self._active_idx: int = 0

    def compose(self) -> ComposeResult:
        with Widget(id="vt-nav"):
            for i, (name, _) in enumerate(self._tab_defs):
                item = _VerticalTabItem(name, i)
                item.set_active(i == self._active_idx)
                yield item
        with ContentSwitcher(initial="vt-content-0", id="vt-switcher"):
            for i, _ in enumerate(self._tab_defs):
                yield Widget(id=f"vt-content-{i}")

    def on_mount(self) -> None:
        for i, (_, factory) in enumerate(self._tab_defs):
            try:
                container = self.query_one(f"#vt-content-{i}", Widget)
                container.mount(factory())
            except Exception:
                pass

    def set_active(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._tab_defs):
            return
        self._active_idx = idx
        for item in self.query(_VerticalTabItem):
            item.set_active(item._idx == idx)
        try:
            switcher = self.query_one("#vt-switcher", ContentSwitcher)
            switcher.current = f"vt-content-{idx}"
        except Exception:
            pass

    def on__vertical_tab_clicked(self, event: _VerticalTabClicked) -> None:
        event.stop()
        self.set_active(event.idx)
