"""Tests for help system."""

from rigi.commands.command import Command
from rigi.commands.registry import CommandRegistry


def test_command_terminal_help():
    """Test terminal help on command."""
    cmd = Command(name="test", help="Short help")
    cmd.set_terminal_help("This is detailed terminal help")

    assert cmd.terminal_help == "This is detailed terminal help"


def test_command_without_terminal_help():
    """Test command without terminal help."""
    cmd = Command(name="test", help="Short help")

    assert cmd.terminal_help == ""


def test_help_with_arguments():
    """Test help display with arguments."""
    cmd = Command(name="test", help="Test command")
    cmd.add_arg("name", help="Name argument", required=True)
    cmd.add_arg("verbose", help="Verbose flag", is_flag=True, short="v")
    cmd.set_terminal_help("Detailed help for test command")

    assert len(cmd.args) == 2
    assert cmd.terminal_help != ""


def test_help_with_subcommands():
    """Test help display with subcommands."""
    parent = Command(name="service", help="Service control")
    parent.add_subcommand(Command(name="start", help="Start service"))
    parent.add_subcommand(Command(name="stop", help="Stop service"))
    parent.add_subcommand(Command(name="restart", help="Restart service"))

    assert len(parent.subcommands) == 3


def test_help_with_aliases():
    """Test help display with aliases."""
    cmd = Command(name="quit", help="Exit application", aliases=["exit", "q"])

    assert "exit" in cmd.aliases
    assert "q" in cmd.aliases


def test_registry_help_listing():
    """Test getting all commands for help listing."""
    registry = CommandRegistry()

    cmd1 = Command(name="test", help="Test command")
    cmd2 = Command(name="quit", help="Quit command")
    cmd3 = Command(name="hidden", help="Hidden command", hidden=True)

    registry.register(cmd1)
    registry.register(cmd2)
    registry.register(cmd3)

    all_cmds = registry.all()
    visible_cmds = [c for c in all_cmds if not c.hidden]

    assert len(all_cmds) == 3
    assert len(visible_cmds) == 2


def test_help_command_structure():
    """Test help command structure."""
    help_cmd = Command(name="help", help="Show help")
    help_cmd.add_arg("command", help="Command to get help for", required=False)
    help_cmd.set_terminal_help(
        "Usage:\n" "  help          - Show all commands\n" "  help <cmd>    - Show detailed help"
    )

    assert len(help_cmd.args) == 1
    assert help_cmd.args[0].name == "command"
    assert help_cmd.args[0].required is False
    assert "Usage:" in help_cmd.terminal_help


def test_subcommand_help():
    """Test help for subcommands."""
    parent = Command(name="git", help="Git commands")

    commit = Command(name="commit", help="Commit changes")
    commit.add_arg("message", help="Commit message", required=True, short="m")
    commit.set_terminal_help("Commit staged changes to repository")

    push = Command(name="push", help="Push changes")
    push.set_terminal_help("Push commits to remote repository")

    parent.add_subcommand(commit)
    parent.add_subcommand(push)

    assert len(parent.subcommands) == 2
    assert parent.subcommands[0].terminal_help != ""
    assert parent.subcommands[1].terminal_help != ""
