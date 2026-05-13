"""Horizontal tab groups for in-page navigation."""

from __future__ import annotations

from typing import Any, Callable

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ContentSwitcher


class _TabItem(Widget):
    can_focus = False

    def __init__(self, label: str, idx: int) -> None:
        super().__init__()
        self._label = label
        self._idx = idx

    def render(self) -> str:
        return self._label

    def set_active(self, active: bool) -> None:
        self.set_class(active, "--active")

    def on_click(self) -> None:
        self.post_message(_TabClicked(self._idx))
        self.app.set_focus(None)


class _TabClicked(Message):
    def __init__(self, idx: int) -> None:
        super().__init__()
        self.idx = idx


class TabGroup(Widget):
    def __init__(
        self,
        tabs: list[tuple[str, Callable[[], Widget]]],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._tab_defs = tabs
        self._active_idx: int = 0

    def compose(self) -> ComposeResult:
        with Widget(id="tabgroup-nav"):
            for i, (name, _) in enumerate(self._tab_defs):
                item = _TabItem(name, i)
                item.set_active(i == self._active_idx)
                yield item
        with ContentSwitcher(
            initial="tab-content-0", id="tabgroup-switcher"
        ):
            for i, _ in enumerate(self._tab_defs):
                yield Widget(id=f"tab-content-{i}")

    def on_mount(self) -> None:
        for i, (_, factory) in enumerate(self._tab_defs):
            try:
                container = self.query_one(f"#tab-content-{i}", Widget)
                container.mount(factory())
            except Exception:
                pass

    def set_active(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._tab_defs):
            return
        self._active_idx = idx
        for item in self.query(_TabItem):
            item.set_active(item._idx == idx)
        try:
            switcher = self.query_one("#tabgroup-switcher", ContentSwitcher)
            switcher.current = f"tab-content-{idx}"
        except Exception:
            pass

    def on__tab_clicked(self, event: _TabClicked) -> None:
        event.stop()
        self.set_active(event.idx)
