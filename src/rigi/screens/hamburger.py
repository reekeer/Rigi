"""RigiHamburgerScreen — slide-in hamburger menu modal."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.screen import ModalScreen

from rigi.widgets.hamburger_menu import (
    RigiMenuItemData,
    RigiMenuPanel,
    _ItemClicked,
)


class RigiHamburgerScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "action_close_or_dismiss", show=False)]

    def __init__(self, sections: list[tuple[str, list[RigiMenuItemData]]]) -> None:
        super().__init__()
        self._current_sections = sections
        self._sections_stack: list[list[tuple[str, list[RigiMenuItemData]]]] = []

    def compose(self) -> ComposeResult:
        yield RigiMenuPanel(self._current_sections, id="rigi-main-menu")

    def on_mount(self) -> None:
        panel = self.query_one("#rigi-main-menu", RigiMenuPanel)
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
            self.dismiss(None)
            self.app.call_after_refresh(callback)

    def _enter_submenu(self, item: RigiMenuItemData) -> None:
        self._sections_stack.append(self._current_sections)
        back_item = RigiMenuItemData("Back", is_back=True)
        self._current_sections = [("", [back_item] + list(item.submenu or []))]
        panel = self.query_one("#rigi-main-menu", RigiMenuPanel)
        panel.border_title = item.label
        panel.replace_sections(self._current_sections)

    def _go_back(self) -> None:
        if self._sections_stack:
            self._current_sections = self._sections_stack.pop()
            panel = self.query_one("#rigi-main-menu", RigiMenuPanel)
            panel.border_title = ""
            panel.replace_sections(self._current_sections)
        else:
            self.dismiss(None)

    def on_click(self, event: Click) -> None:
        main = self.query_one("#rigi-main-menu", RigiMenuPanel)
        if not main.region.contains(event.x, event.y):
            self.dismiss(None)

    def action_close_or_dismiss(self) -> None:
        if self._sections_stack:
            self._go_back()
        else:
            self.dismiss(None)
