"""Built-in terminal command handlers for App."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rigi.core.console as _console
from rigi.widgets.bottom_panel import BottomPanel

if TYPE_CHECKING:
    from rigi.core.app import App


async def cmd_terminal(app: App, **_: Any) -> None:
    from rigi.widgets.bottom_panel import BottomPanel

    nfo = _console.info()
    lines = [
        "[bold]Terminal Info[/bold]",
        f"  Terminal:    {nfo['terminal']}",
        f"  True color:  {'yes' if nfo['true_color'] else 'no'}"
        f"  (depth {nfo['color_depth']})",
        f"  Hyperlinks:  {'yes' if nfo['hyperlinks'] else 'no'}",
        f"  Unicode:     {'yes' if nfo['unicode'] else 'no'}",
        f"  Mouse:       {'yes' if nfo['mouse'] else 'no'}",
        f"  Kitty gfx:   {'yes' if nfo['kitty_graphics'] else 'no'}",
        f"  Multiplexer: "
        f"{'tmux' if nfo['tmux'] else 'screen' if nfo['screen'] else 'none'}",
        f"  Size:        {nfo['columns']}×{nfo['lines']}",
    ]
    try:
        app.query_one(BottomPanel).write_output("\n".join(lines))
    except Exception:
        app.notify("\n".join(lines), title="Terminal Info", timeout=8)


async def cmd_help(app: App, **kwargs: Any) -> None:
    from rigi.widgets.bottom_panel import BottomPanel

    cmd_name = kwargs.get("command")
    registry = app.cmd_registry

    def _output(text: str) -> None:
        try:
            app.query_one(BottomPanel).write_output(text)
        except Exception:
            app.notify(text, title="Help", timeout=12)

    if cmd_name:
        cmd = registry.get(cmd_name)
        if cmd is None:
            _output(f"[red]Unknown command: {cmd_name}[/red]")
            return

        lines = [f"[bold cyan]{cmd.name}[/bold cyan]"]
        if cmd.aliases:
            lines.append(f"[dim]Aliases: {', '.join(cmd.aliases)}[/dim]")
        lines.append(f"\n{cmd.help}")
        if cmd.terminal_help:
            lines.append(f"\n{cmd.terminal_help}")
        if cmd.args:
            lines.append("\n[bold]Arguments:[/bold]")
            for arg in cmd.args:
                flag = f"--{arg.name}"
                if arg.short:
                    flag += f", -{arg.short}"
                req = " [red](required)[/red]" if arg.required else ""
                lines.append(f"  {flag}{req}")
                if arg.help:
                    lines.append(f"    {arg.help}")
        if cmd.subcommands:
            lines.append("\n[bold]Subcommands:[/bold]")
            for sub in cmd.subcommands:
                if not sub.hidden:
                    lines.append(f"  [cyan]{sub.name}[/cyan] - {sub.help}")

        _output("\n".join(lines))
    else:
        lines = ["[bold]Available commands:[/bold]\n"]
        for cmd in registry.all():
            if not cmd.hidden:
                aliases = f" [dim]({', '.join(cmd.aliases)})[/dim]" if cmd.aliases else ""
                lines.append(f"  [cyan]{cmd.name}[/cyan]{aliases} - {cmd.help}")
        lines.append("\n[dim]Type 'help <command>' for detailed information[/dim]")
        lines.append("[dim]Type '!<shell command>' to run shell commands[/dim]")
        _output("\n".join(lines))


async def cmd_quit(app: App, **_: Any) -> None:
    app.exit()


async def cmd_clear(app: App, **_: Any) -> None:
    try:
        app.query_one(BottomPanel).clear_history_view()
    except Exception:
        pass
