"""RigiActionMenuScreen — modal popup action menu."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.screen import ModalScreen

from rigi.widgets.action_menu import (
    RigiActionMenuItemData,
    RigiActionMenuPanel,
    _ActionItemClicked,
)


class RigiActionMenuScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(
        self,
        items: list[RigiActionMenuItemData],
        title: str = "",
        anchor_x: int | None = None,
        anchor_y: int | None = None,
    ) -> None:
        super().__init__()
        self._items = items
        self._title = title
        self._anchor_x = anchor_x
        self._anchor_y = anchor_y

    def compose(self) -> ComposeResult:
        yield RigiActionMenuPanel(self._items, title=self._title, id="rigi-action-menu")

    def on_mount(self) -> None:
        panel = self.query_one("#rigi-action-menu", RigiActionMenuPanel)
        panel_w = 30
        panel_h = min(2 + len(self._items), 20)
        app_w = self.app.size.width
        app_h = self.app.size.height

        if self._anchor_x is not None and self._anchor_y is not None:
            x = min(self._anchor_x, max(0, app_w - panel_w - 1))
            y = min(self._anchor_y, max(0, app_h - panel_h - 1))
        else:
            x = max(0, (app_w - panel_w) // 2)
            y = max(0, (app_h - panel_h) // 2)

        panel.styles.offset = (x, y)
        panel.styles.width = panel_w
        panel.styles.height = panel_h

    @on(_ActionItemClicked)
    def on_item_clicked(self, event: _ActionItemClicked) -> None:
        event.stop()
        item = event.item
        if item.callback is not None:
            callback = item.callback
            self.dismiss(None)
            self.app.call_after_refresh(callback)

    def on_click(self, event: Click) -> None:
        panel = self.query_one("#rigi-action-menu", RigiActionMenuPanel)
        if not panel.region.contains(event.x, event.y):
            self.dismiss(None)

    def action_dismiss(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if hasattr(event, "key") and event.key.isdigit():
            idx = int(event.key) - 1
            if 0 <= idx < len(self._items):
                item = self._items[idx]
                if not item.disabled and item.callback is not None:
                    callback = item.callback
                    self.dismiss(None)
                    self.app.call_after_refresh(callback)
