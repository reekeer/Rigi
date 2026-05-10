"""Built-in terminal command handlers for RigiApp."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rigi.core.console as _console
from rigi.widgets.bottom_panel import RigiBottomPanel

if TYPE_CHECKING:
    from rigi.core.app import RigiApp


async def cmd_terminal(app: RigiApp, **_: Any) -> None:
    nfo = _console.info()
    lines = [
        f"[bold]Terminal:[/bold]    {nfo['terminal']}",
        f"[bold]True color:[/bold]  {'yes' if nfo['true_color'] else 'no'}"
        f"  [dim](depth {nfo['color_depth']})[/dim]",
        f"[bold]Hyperlinks:[/bold]  {'yes' if nfo['hyperlinks'] else 'no'}",
        f"[bold]Unicode:[/bold]     {'yes' if nfo['unicode'] else 'no'}",
        f"[bold]Mouse:[/bold]       {'yes' if nfo['mouse'] else 'no'}",
        f"[bold]Kitty gfx:[/bold]   {'yes' if nfo['kitty_graphics'] else 'no'}",
        f"[bold]Multiplexer:[/bold] "
        f"{'tmux' if nfo['tmux'] else 'screen' if nfo['screen'] else 'none'}",
        f"[bold]Size:[/bold]        {nfo['columns']}×{nfo['lines']}",
    ]
    app.notify("\n".join(lines), title="Terminal Info", timeout=8)


async def cmd_help(app: RigiApp, **kwargs: Any) -> None:
    cmd_name = kwargs.get("command")
    registry = app.cmd_registry

    if cmd_name:
        cmd = registry.get(cmd_name)
        if cmd is None:
            app.notify(f"Unknown command: {cmd_name}", severity="error", title="help")
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

        app.notify("\n".join(lines), title=f"Help: {cmd.name}", timeout=15)
    else:
        lines = ["[bold]Available commands:[/bold]\n"]
        for cmd in registry.all():
            if not cmd.hidden:
                aliases = f" [dim]({', '.join(cmd.aliases)})[/dim]" if cmd.aliases else ""
                lines.append(f"  [cyan]{cmd.name}[/cyan]{aliases} - {cmd.help}")
        lines.append("\n[dim]Type 'help <command>' for detailed information[/dim]")
        lines.append("[dim]Type '!<shell command>' to run shell commands[/dim]")
        app.notify("\n".join(lines), title="Terminal Help", timeout=12)


async def cmd_quit(app: RigiApp, **_: Any) -> None:
    app.exit()


async def cmd_clear(app: RigiApp, **_: Any) -> None:
    try:
        app.query_one(RigiBottomPanel).clear_history_view()
    except Exception:
        pass
