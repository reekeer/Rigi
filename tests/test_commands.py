"""Tests for command system."""
import pytest
from rigi.commands.command import Command
from rigi.commands.registry import CommandRegistry


def test_command_creation():
    """Test basic command creation."""
    cmd = Command(name="test", help="Test command")
    assert cmd.name == "test"
    assert cmd.help == "Test command"
    assert cmd.handler is None
    assert len(cmd.subcommands) == 0


def test_command_with_handler():
    """Test command with handler."""
    called = []
    
    def handler(app=None):
        called.append(True)
    
    cmd = Command(name="test", help="Test")
    cmd.set_handler(handler)
    assert cmd.handler is not None


def test_command_terminal_help():
    """Test terminal help functionality."""
    cmd = Command(name="test", help="Short help")
    cmd.set_terminal_help("Detailed terminal help")
    assert cmd.terminal_help == "Detailed terminal help"


def test_command_subcommand_handler():
    """Test subcommand handler registration."""
    cmd = Command(name="test", help="Test")
    
    def action_handler(app=None):
        pass
    
    cmd.add_subcommand_handler("start", action_handler)
    assert "start" in cmd.subcommand_handlers
    assert cmd.subcommand_handlers["start"] == action_handler


def test_command_args():
    """Test command arguments."""
    cmd = Command(name="test", help="Test")
    cmd.add_arg("name", help="Name argument", required=True)
    cmd.add_arg("verbose", help="Verbose flag", is_flag=True, short="v")
    
    assert len(cmd.args) == 2
    assert cmd.args[0].name == "name"
    assert cmd.args[0].required is True
    assert cmd.args[1].is_flag is True
    assert cmd.args[1].short == "v"


def test_command_aliases():
    """Test command aliases."""
    cmd = Command(name="quit", help="Quit", aliases=["exit", "q"])
    assert "exit" in cmd.aliases
    assert "q" in cmd.aliases


def test_command_registry():
    """Test command registry."""
    registry = CommandRegistry()
    cmd = Command(name="test", help="Test")
    registry.register(cmd)
    
    assert registry.get("test") == cmd
    assert cmd in registry.all()


def test_command_registry_aliases():
    """Test registry with aliases."""
    registry = CommandRegistry()
    cmd = Command(name="quit", help="Quit", aliases=["exit"])
    registry.register(cmd)
    
    assert registry.get("quit") == cmd
    assert registry.get("exit") == cmd


def test_command_completion():
    """Test command completion hints."""
    cmd = Command(name="test", help="Test")
    cmd.add_arg("verbose", is_flag=True, short="v")
    cmd.add_subcommand(Command(name="start", help="Start"))
    cmd.add_subcommand(Command(name="stop", help="Stop"))
    
    hints = cmd.completion_hints("st")
    assert "start" in hints
    assert "stop" in hints
    
    hints = cmd.completion_hints("--v")
    assert "--verbose" in hints


@pytest.mark.asyncio
async def test_command_execute():
    """Test command execution."""
    called = []
    
    async def handler(app=None, name=None):
        called.append(name)
    
    cmd = Command(name="test", help="Test")
    cmd.add_arg("name", required=True)
    cmd.set_handler(handler)
    
    await cmd.execute({"name": "Alice"}, app=None)
    assert called == ["Alice"]


@pytest.mark.asyncio
async def test_command_execute_with_subcommand_handler():
    """Test command execution with subcommand handler."""
    called = []
    
    async def start_handler(app=None):
        called.append("start")
    
    async def stop_handler(app=None):
        called.append("stop")
    
    cmd = Command(name="service", help="Service control")
    cmd.add_subcommand_handler("start", start_handler)
    cmd.add_subcommand_handler("stop", stop_handler)
    
    await cmd.execute({"action": "start"}, app=None)
    assert called == ["start"]
    
    await cmd.execute({"action": "stop"}, app=None)
    assert called == ["start", "stop"]
