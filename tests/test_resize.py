"""Tests for resize functionality."""
import pytest
from textual.app import App
from textual.events import MouseDown, MouseMove, MouseUp
from rigi.widgets.sidebar import _VerticalResizeHandle
from rigi.widgets.content_area import _ContentResizeHandle, RigiContentArea
from rigi.widgets.bottom_panel import _ResizeHandle, RigiBottomPanel
from rigi.commands.registry import CommandRegistry


@pytest.mark.asyncio
async def test_vertical_resize_handle_render():
    """Test vertical resize handle rendering."""
    class TestApp(App):
        def compose(self):
            yield _VerticalResizeHandle("test-target")
    
    app = TestApp()
    async with app.run_test() as pilot:
        handle = app.query_one(_VerticalResizeHandle)
        rendered = handle.render()
        assert "│" in rendered


@pytest.mark.asyncio
async def test_content_resize_handle_render():
    """Test content resize handle rendering."""
    class TestApp(App):
        def compose(self):
            yield RigiContentArea()
    
    app = TestApp()
    async with app.run_test() as pilot:
        handle = app.query_one(_ContentResizeHandle)
        rendered = handle.render()
        assert "│" in rendered


@pytest.mark.asyncio
async def test_horizontal_resize_handle_render():
    """Test horizontal resize handle rendering."""
    class TestApp(App):
        def compose(self):
            yield RigiBottomPanel(
                prompt_text="test",
                registry=CommandRegistry(),
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        handle = app.query_one(_ResizeHandle)
        rendered = handle.render()
        assert "─" in rendered


@pytest.mark.asyncio
async def test_resize_handle_mouse_events():
    """Test resize handle responds to mouse events."""
    class TestApp(App):
        def compose(self):
            yield _VerticalResizeHandle("test-target")
    
    app = TestApp()
    async with app.run_test() as pilot:
        handle = app.query_one(_VerticalResizeHandle)
        
        # Test mouse down
        event = MouseDown(0, 0, 0, 0, 0, 0, False, False, False)
        handle.on_mouse_down(event)
        assert handle._drag_x is not None
        
        # Test mouse up
        event_up = MouseUp(0, 0, 0, 0, 0, 0, False, False, False)
        handle.on_mouse_up(event_up)
        assert handle._drag_x is None


@pytest.mark.asyncio
async def test_resize_minimum_size():
    """Test that resize respects minimum sizes."""
    class TestApp(App):
        def compose(self):
            yield RigiBottomPanel(
                prompt_text="test",
                registry=CommandRegistry(),
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        handle = app.query_one(_ResizeHandle)
        panel = app.query_one(RigiBottomPanel)
        
        # Simulate drag to very small size
        handle._drag_y = 100
        handle._drag_h = 10
        
        event = MouseMove(0, 0, 200, 0, 0, 0, False, False, False)
        handle.on_mouse_move(event)
        
        # Should be at least 4
        assert panel.styles.height.value >= 4
