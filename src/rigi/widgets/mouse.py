from __future__ import annotations

import asyncio
from typing import Any

from textual.events import (
    Click,
    MouseDown,
    MouseMove,
    MouseScrollDown,
    MouseScrollUp,
    MouseUp,
)
from textual.message import Message
from textual.widget import Widget


class MouseMixin:
    """
    Mixin for any Widget subclass to get convenient mouse event hooks.

    Usage:
        class MyWidget(MouseMixin, Widget):
            def on_rigi_click(self, x, y, button):
                ...
    """

    def on_click(self, event: Click) -> None:
        asyncio.create_task(self._rigi_dispatch_click(event))

    def on_mouse_down(self, event: MouseDown) -> None:
        asyncio.create_task(self._rigi_dispatch_mouse_down(event))

    def on_mouse_up(self, event: MouseUp) -> None:
        asyncio.create_task(self._rigi_dispatch_mouse_up(event))

    def on_mouse_move(self, event: MouseMove) -> None:
        asyncio.create_task(self._rigi_dispatch_mouse_move(event))

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        asyncio.create_task(self._rigi_dispatch_scroll(event, "down"))

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        asyncio.create_task(self._rigi_dispatch_scroll(event, "up"))

    async def _rigi_dispatch_click(self, event: Click) -> None:
        fn = getattr(self, "on_rigi_click", None)
        if fn:
            result = fn(event.x, event.y, event.button)
            if asyncio.iscoroutine(result):
                await result

    async def _rigi_dispatch_mouse_down(self, event: MouseDown) -> None:
        fn = getattr(self, "on_rigi_mouse_down", None)
        if fn:
            result = fn(event.x, event.y, event.button)
            if asyncio.iscoroutine(result):
                await result

    async def _rigi_dispatch_mouse_up(self, event: MouseUp) -> None:
        fn = getattr(self, "on_rigi_mouse_up", None)
        if fn:
            result = fn(event.x, event.y, event.button)
            if asyncio.iscoroutine(result):
                await result

    async def _rigi_dispatch_mouse_move(self, event: MouseMove) -> None:
        fn = getattr(self, "on_rigi_mouse_move", None)
        if fn:
            result = fn(event.x, event.y)
            if asyncio.iscoroutine(result):
                await result

    async def _rigi_dispatch_scroll(
        self, event: MouseScrollDown | MouseScrollUp, direction: str
    ) -> None:
        fn = getattr(self, "on_rigi_scroll", None)
        if fn:
            result = fn(event.x, event.y, direction)
            if asyncio.iscoroutine(result):
                await result


class Clickable(MouseMixin, Widget):
    """
    Widget that fires a Clicked message and calls on_rigi_click.

    Usage:
        btn = Clickable("Click me")
        btn.on_rigi_click = lambda x, y, btn: print("clicked")
    """

    class Clicked(Message):
        def __init__(self, x: int, y: int, button: int) -> None:
            super().__init__()
            self.x = x
            self.y = y
            self.button = button

    def __init__(self, label: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._label = label

    def render(self) -> str:
        return self._label

    def on_click(self, event: Click) -> None:
        self.post_message(Clickable.Clicked(event.x, event.y, event.button))
        super().on_click(event)


class Draggable(MouseMixin, Widget):
    """
    Widget that supports drag operations.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._drag_start: tuple[int, int] | None = None
        self._dragging = False

    def on_mouse_down(self, event: MouseDown) -> None:
        self._drag_start = (event.x, event.y)
        self._dragging = False
        self.capture_mouse()
        super().on_mouse_down(event)

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._drag_start is not None:
            self._dragging = True
            dx = event.x - self._drag_start[0]
            dy = event.y - self._drag_start[1]
            fn = getattr(self, "on_rigi_drag", None)
            if fn:
                result = fn(event.x, event.y, dx, dy)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
        super().on_mouse_move(event)

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            fn = getattr(self, "on_rigi_drag_end", None)
            if fn:
                result = fn(event.x, event.y)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
        self._drag_start = None
        self._dragging = False
        self.release_mouse()
        super().on_mouse_up(event)
