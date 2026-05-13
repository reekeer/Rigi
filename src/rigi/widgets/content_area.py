"""ContentArea with resizable support."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.events import MouseDown, MouseMove, MouseUp
from textual.widget import Widget
from textual.widgets import Label

_ui_log = logging.getLogger("rigi.ui")


class _ContentResizeHandle(Widget):
    """Вертикальный handle для изменения ширины content area."""

    def __init__(self) -> None:
        super().__init__()
        self._drag_x: int | None = None
        self._drag_w: int | None = None

    def render(self) -> str:
        return "│" * self.size.height

    def on_mouse_down(self, event: MouseDown) -> None:
        try:
            self.capture_mouse()
            self._drag_x = event.screen_x
            content = next((w for w in self.ancestors if isinstance(w, ContentArea)), None)
            if content is not None:
                self._drag_w = content.size.width
                _ui_log.debug("Started resizing content area")
        except Exception as e:
            _ui_log.error(f"Error in content resize mouse_down: {e}", exc_info=True)

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._drag_x is None or self._drag_w is None:
            return
        try:
            delta = event.screen_x - self._drag_x
            new_w = max(20, self._drag_w + delta)
            content = next((w for w in self.ancestors if isinstance(w, ContentArea)), None)
            if content is not None:
                content.styles.width = new_w
        except Exception as e:
            _ui_log.error(f"Error in content resize mouse_move: {e}", exc_info=True)

    def on_mouse_up(self, event: MouseUp) -> None:
        event.stop()
        try:
            self.release_mouse()
            self._drag_x = None
            self._drag_w = None
            _ui_log.debug("Finished resizing content area")
        except Exception as e:
            _ui_log.error(f"Error in content resize mouse_up: {e}", exc_info=True)


class _EmptyState(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Select a section from the sidebar")


class ContentArea(Widget):
    def __init__(self) -> None:
        super().__init__()
        self._current: Widget | None = None

    def compose(self) -> ComposeResult:
        yield _ContentResizeHandle()
        with Widget(id="content-main"):
            yield _EmptyState(id="rigi-empty-state")

    def show_widget(self, widget: Widget) -> None:
        try:
            if self._current is widget:
                return

            if self._current is not None:
                self._current.display = False
            else:
                self._hide_empty_state()

            self._current = widget
            content_main = self.query_one("#content-main")
            if not widget.is_mounted:
                content_main.mount(widget)
            widget.display = True
        except Exception as e:
            _ui_log.error(f"Error showing widget: {e}", exc_info=True)

    def _hide_empty_state(self) -> None:
        try:
            self.query_one("#rigi-empty-state").display = False
        except Exception as e:
            _ui_log.debug(f"Error hiding empty state: {e}")

    def _show_empty_state(self) -> None:
        try:
            self.query_one("#rigi-empty-state").display = True
        except Exception:
            try:
                content_main = self.query_one("#content-main")
                content_main.mount(_EmptyState(id="rigi-empty-state"))
            except Exception as e:
                _ui_log.error(f"Error showing empty state: {e}", exc_info=True)

    def clear(self) -> None:
        try:
            if self._current is not None:
                self._current.display = False
                self._current = None
            self._show_empty_state()
        except Exception as e:
            _ui_log.error(f"Error clearing content: {e}", exc_info=True)
