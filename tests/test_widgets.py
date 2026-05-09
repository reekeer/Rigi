"""Tests for widgets."""
import pytest
from textual.app import App
from rigi.widgets.content_area import RigiContentArea
from rigi.widgets.settings_screen import RigiSettingDef
from textual.widgets import Label


@pytest.mark.asyncio
async def test_content_area_show_widget():
    """Test showing widget in content area."""
    class TestApp(App):
        def compose(self):
            yield RigiContentArea()
    
    app = TestApp()
    async with app.run_test() as pilot:
        content = app.query_one(RigiContentArea)
        test_widget = Label("Test")
        
        content.show_widget(test_widget)
        assert content._current == test_widget
        assert test_widget.display is True


@pytest.mark.asyncio
async def test_content_area_clear():
    """Test clearing content area."""
    class TestApp(App):
        def compose(self):
            yield RigiContentArea()
    
    app = TestApp()
    async with app.run_test() as pilot:
        content = app.query_one(RigiContentArea)
        test_widget = Label("Test")
        
        content.show_widget(test_widget)
        assert content._current == test_widget
        
        content.clear()
        assert content._current is None


def test_setting_def_get_value():
    """Test getting setting value."""
    setting = RigiSettingDef(
        category="Test",
        label="Test Setting",
        value_fn=lambda: "test_value"
    )
    
    assert setting.get_value() == "test_value"


def test_setting_def_set_value():
    """Test setting value."""
    stored = []
    
    def write_fn(value):
        stored.append(value)
    
    setting = RigiSettingDef(
        category="Test",
        label="Test Setting",
        write_fn=write_fn
    )
    
    setting.set_value("new_value")
    assert stored == ["new_value"]


def test_setting_def_with_error():
    """Test setting with error in value_fn."""
    def error_fn():
        raise ValueError("Test error")
    
    setting = RigiSettingDef(
        category="Test",
        label="Test Setting",
        value_fn=error_fn
    )
    
    # Should not raise, should return empty string
    assert setting.get_value() == ""


def test_setting_def_cached_value():
    """Test cached value in setting."""
    call_count = []
    
    def value_fn():
        call_count.append(1)
        return "value"
    
    setting = RigiSettingDef(
        category="Test",
        label="Test Setting",
        value_fn=value_fn
    )
    
    # First call
    val1 = setting.get_value()
    assert val1 == "value"
    assert len(call_count) == 1
    
    # Set cached value
    setting.set_value("cached")
    
    # Should return cached value without calling value_fn
    val2 = setting.get_value()
    assert val2 == "cached"
    assert len(call_count) == 1  # Not called again
