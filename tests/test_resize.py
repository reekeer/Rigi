"""Tests for resize functionality."""

import pytest
from textual.app import App
from textual.events import MouseDown, MouseMove, MouseUp

from rigi.commands.registry import CommandRegistry
from rigi.widgets.bottom_panel import RigiBottomPanel, _ResizeHandle
from rigi.widgets.content_area import RigiContentArea
from rigi.widgets.sidebar import _VerticalResizeHandle


@pytest.mark.asyncio
async def test_vertical_resize_handle_render():
    """Test vertical resize handle rendering."""

    class TestApp(App[None]):
        def compose(self):
            yield _VerticalResizeHandle("test-target")

    app = TestApp()
    async with app.run_test() as _:
        handle = app.query_one(_VerticalResizeHandle)
        rendered = handle.render()
        assert "│" in rendered


@pytest.mark.asyncio
async def test_horizontal_resize_handle_render():
    """Test horizontal resize handle rendering."""

    class TestApp(App[None]):
        def compose(self):
            yield RigiBottomPanel(prompt_text="test", registry=CommandRegistry(), history_file=None)

    app = TestApp()
    async with app.run_test() as _:
        handle = app.query_one(_ResizeHandle)
        rendered = handle.render()
        assert "─" in rendered


@pytest.mark.asyncio
async def test_resize_handle_mouse_events():
    """Test resize handle responds to mouse events."""

    class TestApp(App[None]):
        def compose(self):
            yield _VerticalResizeHandle("test-target")

    app = TestApp()
    async with app.run_test() as _:
        handle = app.query_one(_VerticalResizeHandle)

        # Test mouse down
        event = MouseDown(None, 0, 0, 0, 0, 0, False, False, False)
        handle.on_mouse_down(event)
        assert handle._drag_x is not None

        # Test mouse up
        event_up = MouseUp(None, 0, 0, 0, 0, 0, False, False, False)
        handle.on_mouse_up(event_up)
        assert handle._drag_x is None


@pytest.mark.asyncio
async def test_resize_minimum_size():
    """Test that resize respects minimum sizes."""

    class TestApp(App[None]):
        def compose(self):
            yield RigiBottomPanel(prompt_text="test", registry=CommandRegistry(), history_file=None)

    app = TestApp()
    async with app.run_test() as _:
        handle = app.query_one(_ResizeHandle)
        panel = app.query_one(RigiBottomPanel)

        # Simulate drag to very small size
        handle._drag_y = 100
        handle._drag_h = 10

        event = MouseMove(None, 0, 200, 0, 0, 0, False, False, False)
        handle.on_mouse_move(event)

        # Should be at least 4
        height = panel.styles.height
        assert height is not None and height.value >= 4
