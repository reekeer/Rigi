"""Hamburger menu overlay widget — mounts directly on app, non-blocking."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.events import Click
from textual.widget import Widget

from rigi.widgets.hamburger_menu import MenuItemData, MenuPanel, _ItemClicked


class HamburgerOverlay(Widget):
    """Non-blocking overlay that hosts the hamburger menu panel."""

    def __init__(self, sections: list[tuple[str, list[MenuItemData]]]) -> None:
        super().__init__()
        self._current_sections = sections
        self._sections_stack: list[list[tuple[str, list[MenuItemData]]]] = []

    def compose(self) -> ComposeResult:
        yield MenuPanel(self._current_sections, id="rigi-main-menu")

    def on_mount(self) -> None:
        panel = self.query_one("#rigi-main-menu", MenuPanel)
        panel_w = 26
        x = max(0, self.app.size.width - panel_w - 1)
        panel.styles.offset = (x, 3)

    @on(_ItemClicked)
    def on_item_clicked(self, event: _ItemClicked) -> None:
        event.stop()
        item = event.item
        if item.is_back:
            self._go_back()
        elif item.submenu is not None:
            self._enter_submenu(item)
        elif item.callback is not None:
            callback = item.callback
            self._close()
            self.app.call_after_refresh(callback)

    def _enter_submenu(self, item: MenuItemData) -> None:
        self._sections_stack.append(self._current_sections)
        back_item = MenuItemData("Back", is_back=True)
        self._current_sections = [("", [back_item] + list(item.submenu or []))]
        panel = self.query_one("#rigi-main-menu", MenuPanel)
        panel.border_title = item.label
        panel.replace_sections(self._current_sections)

    def _go_back(self) -> None:
        if self._sections_stack:
            self._current_sections = self._sections_stack.pop()
            panel = self.query_one("#rigi-main-menu", MenuPanel)
            panel.border_title = ""
            panel.replace_sections(self._current_sections)
        else:
            self._close()

    def on_click(self, event: Click) -> None:
        main = self.query_one("#rigi-main-menu", MenuPanel)
        if not main.region.contains(event.x, event.y):
            self._close()

    def action_close_or_dismiss(self) -> None:
        if self._sections_stack:
            self._go_back()
        else:
            self._close()

    def _close(self) -> None:
        try:
            self.remove()
        except Exception:
            pass
