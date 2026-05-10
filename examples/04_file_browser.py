"""File browser — navigates local filesystem, shows file details."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from rigi import RigiApp, TabDef
from rigi.layout.pane import RigiCard, RigiPane
from rigi.widgets import DataTable, Label

app = RigiApp(name="files", version="1.0.0", description="Local filesystem browser")

_cwd: Path = Path.cwd()


def _size_str(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n //= 1024
    return f"{n} TB"


def _perms(p: Path) -> str:
    try:
        m = p.stat().st_mode
        return stat.filemode(m)
    except OSError:
        return "----------"


def make_browser():
    table = DataTable()
    table.add_columns("Name", "Size", "Permissions", "Type")

    entries: list[Path] = []
    try:
        entries = sorted(_cwd.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        pass

    if _cwd.parent != _cwd:
        table.add_row("[dim]..[/dim]", "", "", "[dim]dir[/dim]")

    for entry in entries:
        try:
            is_dir = entry.is_dir()
            size = "" if is_dir else _size_str(entry.stat().st_size)
            name = f"[bold cyan]{entry.name}/[/bold cyan]" if is_dir else entry.name
            kind = "[cyan]dir[/cyan]" if is_dir else _file_type(entry)
            table.add_row(name, size, _perms(entry), kind)
        except OSError:
            table.add_row(f"[dim]{entry.name}[/dim]", "?", "?", "?")

    info = RigiCard(
        Label(f"[bold]Path:[/bold]  {_cwd}"),
        Label(f"[bold]Items:[/bold] {len(entries)}"),
        Label(
            f"[bold]Free:[/bold]  {_size_str(os.statvfs(_cwd).f_bavail * os.statvfs(_cwd).f_frsize)}"
        ),
        title=" Current Directory",
    )

    return RigiPane(info, table)


def _file_type(p: Path) -> str:
    suffix = p.suffix.lower()
    type_map = {
        ".py": "[green]python[/green]",
        ".js": "[yellow]js[/yellow]",
        ".ts": "[yellow]ts[/yellow]",
        ".go": "[cyan]go[/cyan]",
        ".rs": "[yellow]rust[/yellow]",
        ".md": "[white]markdown[/white]",
        ".toml": "[white]toml[/white]",
        ".json": "[white]json[/white]",
        ".yaml": "[white]yaml[/white]",
        ".yml": "[white]yaml[/white]",
        ".sh": "[green]shell[/green]",
        ".txt": "[dim]text[/dim]",
    }
    return type_map.get(suffix, f"[dim]{suffix or 'file'}[/dim]")


app.add_tab(TabDef(name="Browser", key="1", icon="", widget_factory=make_browser))

app.add_status("path", "Path", lambda: str(_cwd), refresh_interval=1.0)


@app.command("cd", help="Change directory")
async def cmd_cd(app: RigiApp, **kwargs: object) -> None:
    global _cwd
    target = str(next(iter(kwargs.values()), "~"))
    try:
        new = (_cwd / target).resolve()
        if new.is_dir():
            _cwd = new
            app.invalidate_tab_cache()
        else:
            app.notify(f"Not a directory: {target}", severity="warning")
    except Exception as e:
        app.notify(str(e), severity="error")


@app.command("ls", help="List current directory", aliases=["dir"])
async def cmd_ls(app: RigiApp, **_: object) -> None:
    app.invalidate_tab_cache()
    app.navigate_to_tab("Browser")


@app.command("home", help="Go to home directory")
async def cmd_home(app: RigiApp, **_: object) -> None:
    global _cwd
    _cwd = Path.home()
    app.invalidate_tab_cache()
    app.navigate_to_tab("Browser")


if __name__ == "__main__":
    RigiApp.run_cli(app)
