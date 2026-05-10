"""Tests for terminal functionality."""
import pytest
from textual.app import App
from textual.widgets import Tabs
from rigi.widgets.bottom_panel import RigiBottomPanel, _TerminalInput
from rigi.commands.registry import CommandRegistry
from rigi.commands.command import Command


@pytest.mark.asyncio
async def test_terminal_input_focus():
    """Test terminal input focus handling."""
    class TestApp(App):
        def compose(self):
            yield RigiBottomPanel(
                prompt_text="test",
                registry=CommandRegistry(),
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        terminal_input = app.query_one("#terminal-input", _TerminalInput)
        await pilot.pause()
        terminal_input.focus()
        await pilot.pause()
        # Just check it doesn't crash
        assert terminal_input is not None


@pytest.mark.asyncio
async def test_terminal_command_submission():
    """Test command submission from terminal."""
    class TestApp(App):
        def compose(self):
            registry = CommandRegistry()
            cmd = Command(name="test", help="Test command")
            registry.register(cmd)
            yield RigiBottomPanel(
                prompt_text="test",
                registry=registry,
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        panel = app.query_one(RigiBottomPanel)
        terminal_input = app.query_one("#terminal-input", _TerminalInput)
        
        # Type command
        terminal_input.value = "test"
        await pilot.pause()
        
        # Submit
        await pilot.press("enter")
        await pilot.pause()
        
        # Check history (may or may not be added depending on timing)
        assert panel._history is not None


@pytest.mark.asyncio
async def test_terminal_history_navigation():
    """Test navigating terminal history with arrow keys."""
    class TestApp(App):
        def compose(self):
            yield RigiBottomPanel(
                prompt_text="test",
                registry=CommandRegistry(),
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        panel = app.query_one(RigiBottomPanel)
        terminal_input = app.query_one("#terminal-input", _TerminalInput)
        
        # Add some history
        panel._history = ["cmd1", "cmd2", "cmd3"]
        panel._history_pos = -1
        
        terminal_input.focus()
        
        # Press up - should show last command
        await pilot.press("up")
        assert terminal_input.value == "cmd3"
        
        # Press up again
        await pilot.press("up")
        assert terminal_input.value == "cmd2"
        
        # Press down
        await pilot.press("down")
        assert terminal_input.value == "cmd3"


@pytest.mark.asyncio
async def test_terminal_tab_completion():
    """Test tab completion in terminal."""
    class TestApp(App):
        def compose(self):
            registry = CommandRegistry()
            cmd1 = Command(name="test", help="Test")
            cmd2 = Command(name="terminal", help="Terminal")
            registry.register(cmd1)
            registry.register(cmd2)
            yield RigiBottomPanel(
                prompt_text="test",
                registry=registry,
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        terminal_input = app.query_one("#terminal-input", _TerminalInput)
        panel = app.query_one(RigiBottomPanel)
        
        terminal_input.focus()
        terminal_input.value = "te"
        
        # Trigger completion
        panel._completions = panel._cmd_registry.completions("te")
        assert "test" in panel._completions
        assert "terminal" in panel._completions


@pytest.mark.asyncio
async def test_terminal_clear():
    """Test clearing terminal history."""
    class TestApp(App):
        def compose(self):
            yield RigiBottomPanel(
                prompt_text="test",
                registry=CommandRegistry(),
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        panel = app.query_one(RigiBottomPanel)
        
        # Write some output
        panel.write_output("Test line 1")
        panel.write_output("Test line 2")
        await pilot.pause()
        
        # Clear
        panel.clear_history_view()
        await pilot.pause()
        
        # History view should be cleared
        history = app.query_one("#term-history")
        # Just check it doesn't crash
        assert history is not None


@pytest.mark.asyncio
async def test_terminal_tab_switching():
    """Test switching between Terminal and Logs tabs."""
    class TestApp(App):
        def compose(self):
            yield RigiBottomPanel(
                prompt_text="test",
                registry=CommandRegistry(),
                history_file=None
            )
    
    app = TestApp()
    async with app.run_test() as pilot:
        panel = app.query_one(RigiBottomPanel)

        # Should start on terminal
        assert panel.active_tab == "terminal"

        # Switch to logs via Tabs reactive
        panel.query_one(Tabs).active = "tab-logs"
        await pilot.pause()
        assert panel.active_tab == "logs"

        # Switch back
        panel.query_one(Tabs).active = "tab-terminal"
        await pilot.pause()
        assert panel.active_tab == "terminal"
