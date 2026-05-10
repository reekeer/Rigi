"""Developer/sudo command suite for Rigi apps.

Invoke with:  sudo <subcmd>   or   !sudo <subcmd>

All commands are hidden from normal autocomplete.
Run `sudo help` for a list.
"""

from __future__ import annotations

import gc as _gc
import importlib
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rigi.commands.command import Command

if TYPE_CHECKING:
    from rigi.core.app import RigiApp

# Создаем специализированные логгеры
_log = logging.getLogger("rigi.dev")
_ui_log = logging.getLogger("rigi.ui")
_terminal_log = logging.getLogger("rigi.terminal")


# ── Helpers ────────────────────────────────────────────────────────────────────


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n //= 1024
    return f"{n:.1f} TB"


def _widget_path(widget: Any) -> str:
    parts: list[str] = []
    w = widget
    while w is not None:
        name = type(w).__name__
        wid = getattr(w, "id", None)
        if wid:
            name += f"#{wid}"
        parts.append(name)
        w = getattr(w, "parent", None)
        if hasattr(w, "_app"):
            break
    return " > ".join(reversed(parts))


def _tree_lines(widget: Any, depth: int = 0, max_depth: int = 4) -> list[str]:
    if depth > max_depth:
        return []
    indent = "  " * depth
    name = type(widget).__name__
    wid = getattr(widget, "id", None)
    label = f"{indent}{name}{'#' + wid if wid else ''}"
    lines = [label]
    for child in getattr(widget, "children", []):
        lines.extend(_tree_lines(child, depth + 1, max_depth))
    return lines


# ── Command handlers ───────────────────────────────────────────────────────────


async def _cmd_help(app: RigiApp, **_: Any) -> None:
    lines = ["[bold]sudo commands[/bold] (hidden from normal autocomplete):\n"]
    for sub in _SUBCOMMANDS:
        aliases = f"  [dim]({', '.join(sub.aliases)})[/dim]" if sub.aliases else ""
        lines.append(f"  [bold cyan]sudo {sub.name}[/bold cyan]{aliases} — {sub.help}")
    lines.append("\n[dim]Prefix with ! to skip sudo:  !sudo tree[/dim]")
    lines.append("[dim]Run shell commands directly:   !ls -la[/dim]")
    app.notify("\n".join(lines), title="Dev Commands", timeout=15)


async def _cmd_clear_cache(app: RigiApp, **_: Any) -> None:
    n = len(app._rigi_widget_cache)
    app.invalidate_tab_cache()
    app.notify(f"Cleared {n} cached widget(s)", title="sudo cc", timeout=3)


async def _cmd_reload(app: RigiApp, **_: Any) -> None:
    app.invalidate_tab_cache()
    app.refresh(layout=True)
    app.notify("All caches cleared + layout refreshed", title="sudo reload", timeout=3)


async def _cmd_reload_css(app: RigiApp, **_: Any) -> None:
    try:
        app.refresh_css(animate=False)
        app.notify("CSS reloaded", title="sudo rcss", timeout=3)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo rcss")


async def _cmd_css(app: RigiApp, **kwargs: Any) -> None:
    rule = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not rule:
        app.notify(
            "Usage: sudo css <rule>  (e.g. sudo css 'RigiCard { opacity: 0.8; }')",
            severity="warning",
        )
        return
    try:
        app.stylesheet.add_source(
            rule,
            read_from=("__sudo_css__", "__sudo_css__"),
            is_default_css=False,
            tie_breaker=9999,
        )
        app.refresh_css(animate=False)
        app.notify(f"Injected: {rule[:80]}", title="sudo css", timeout=4)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo css")


async def _cmd_dump_theme(app: RigiApp, **_: Any) -> None:
    css = app._theme.to_css()
    path = Path(f"/tmp/rigi_theme_{app._prog_name}.css")
    path.write_text(css, encoding="utf-8")
    app.notify(f"Written to {path}\n\n{css[:400]}…", title="sudo dump_theme", timeout=10)


async def _cmd_inspect(app: RigiApp, **_: Any) -> None:
    focused = app.focused
    if focused is None:
        app.notify("No focused widget", severity="warning", title="sudo inspect")
        return
    w = focused
    lines = [
        f"[bold]Type:[/bold]    {type(w).__name__}",
        f"[bold]Module:[/bold]  {type(w).__module__}",
        f"[bold]ID:[/bold]      {getattr(w, 'id', None) or '(none)'}",
        f"[bold]Classes:[/bold] {' '.join(w.classes) or '(none)'}",
        f"[bold]Size:[/bold]    {w.size.width}×{w.size.height}",
        f"[bold]Offset:[/bold]  {w.region.x},{w.region.y}",
        f"[bold]Visible:[/bold] {w.visible}",
        f"[bold]Focusable:[/bold] {w.focusable}",
        f"[bold]Path:[/bold]    {_widget_path(w)}",
    ]
    app.notify("\n".join(lines), title="sudo inspect", timeout=10)


async def _cmd_tree(app: RigiApp, **_: Any) -> None:
    try:
        screen = app.screen
        lines = _tree_lines(screen, max_depth=4)
        text = "\n".join(lines[:60])
        if len(lines) > 60:
            text += f"\n[dim]… ({len(lines) - 60} more)[/dim]"
        app.notify(text, title="sudo tree", timeout=12)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo tree")


async def _cmd_focus(app: RigiApp, **_: Any) -> None:
    focused = app.focused
    if focused is None:
        app.notify("No widget focused", title="sudo focus", timeout=4)
    else:
        app.notify(_widget_path(focused), title="sudo focus", timeout=6)


async def _cmd_mem(app: RigiApp, **_: Any) -> None:
    lines: list[str] = []
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = usage.ru_maxrss
        if sys.platform != "darwin":
            rss *= 1024  # Linux reports in KB
        lines.append(f"[bold]RSS:[/bold]      {_fmt_bytes(rss)}")
        lines.append(f"[bold]User time:[/bold] {usage.ru_utime:.2f}s")
        lines.append(f"[bold]Sys time:[/bold]  {usage.ru_stime:.2f}s")
    except ImportError:
        pass
    try:
        import tracemalloc

        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            lines.append(f"[bold]Traced:[/bold]   {_fmt_bytes(current)} (peak {_fmt_bytes(peak)})")
        else:
            lines.append("[dim]tracemalloc not active (sudo tracemalloc to start)[/dim]")
    except ImportError:
        pass
    counts = _gc.get_count()
    lines.append(f"[bold]GC counts:[/bold] gen0={counts[0]} gen1={counts[1]} gen2={counts[2]}")
    app.notify("\n".join(lines) or "Memory info unavailable", title="sudo mem", timeout=8)


async def _cmd_gc(app: RigiApp, **_: Any) -> None:
    before = sum(_gc.get_count())
    n = _gc.collect()
    after = sum(_gc.get_count())
    app.notify(f"Collected {n} objects  (count {before}→{after})", title="sudo gc", timeout=4)


async def _cmd_tracemalloc(app: RigiApp, **_: Any) -> None:
    import tracemalloc

    if tracemalloc.is_tracing():
        tracemalloc.stop()
        app.notify("tracemalloc stopped", title="sudo tracemalloc", timeout=3)
    else:
        tracemalloc.start()
        app.notify(
            "tracemalloc started (run 'sudo mem' to see results)",
            title="sudo tracemalloc",
            timeout=4,
        )


async def _cmd_screenshot(app: RigiApp, **_: Any) -> None:
    try:
        svg = app.export_screenshot()
        path = Path(f"/tmp/rigi_{app._prog_name}_{os.getpid()}.svg")
        path.write_text(svg, encoding="utf-8")
        app.notify(f"Saved: {path}", title="sudo screenshot", timeout=5)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo screenshot")


async def _cmd_env(app: RigiApp, **kwargs: Any) -> None:
    query = " ".join(str(v) for v in kwargs.values() if v).strip().lower()
    items = sorted(os.environ.items())
    if query:
        items = [(k, v) for k, v in items if query in k.lower() or query in v.lower()]
    if not items:
        app.notify(f"No env vars matching '{query}'", severity="warning", title="sudo env")
        return
    lines = [f"[bold]{k}[/bold]={v[:60]}{'…' if len(v) > 60 else ''}" for k, v in items[:30]]
    if len(items) > 30:
        lines.append(f"[dim]… ({len(items) - 30} more)[/dim]")
    app.notify("\n".join(lines), title=f"sudo env{' [' + query + ']' if query else ''}", timeout=12)


async def _cmd_tabs(app: RigiApp, **_: Any) -> None:
    lines: list[str] = []
    for i, tab in enumerate(app._rigi_tabs):
        cached_keys = [k for k in app._rigi_widget_cache if k[0] == i]
        cached = (
            f"[green]{len(cached_keys)} cached[/green]" if cached_keys else "[dim]not cached[/dim]"
        )
        lines.append(f"  [{i}] [bold]{tab.name}[/bold]  {cached}")
        for j, sub in enumerate(tab.subtabs):
            sub_cached = (i, j) in app._rigi_widget_cache
            mark = "[green]●[/green]" if sub_cached else "[dim]○[/dim]"
            lines.append(f"       {mark} {sub.name}")
    app.notify("\n".join(lines) or "(no tabs)", title="sudo tabs", timeout=10)


async def _cmd_cmds(app: RigiApp, **_: Any) -> None:
    all_cmds = app._cmd_registry.all()
    lines = ["[bold]All registered commands (including hidden):[/bold]\n"]
    for cmd in sorted(all_cmds, key=lambda c: c.name):
        hidden_mark = " [dim](hidden)[/dim]" if cmd.hidden else ""
        aliases = f" [dim]| {', '.join(cmd.aliases)}[/dim]" if cmd.aliases else ""
        subs = f" [dim]+{len(cmd.subcommands)} sub[/dim]" if cmd.subcommands else ""
        lines.append(f"  [cyan]{cmd.name}[/cyan]{aliases}{subs}{hidden_mark} — {cmd.help}")
    app.notify("\n".join(lines), title="sudo cmds", timeout=12)


async def _cmd_bell(app: RigiApp, **_: Any) -> None:
    from rigi.core import console

    console.write_escape(console.bell())
    app.notify("🔔", title="sudo bell", timeout=2)


async def _cmd_dn_test(app: RigiApp, **_: Any) -> None:
    from rigi.core import platform

    ok = platform.notify_desktop("Rigi Dev", f"Test from {app._prog_name}")
    app.notify(
        "Desktop notification sent" if ok else "Desktop notifications unavailable",
        severity="information" if ok else "warning",
        title="sudo dn_test",
    )


async def _cmd_crash(app: RigiApp, **kwargs: Any) -> None:
    msg = " ".join(str(v) for v in kwargs.values() if v).strip() or "Test crash from sudo crash"
    raise RuntimeError(msg)


async def _cmd_python(app: RigiApp, **kwargs: Any) -> None:
    expr = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not expr:
        app.notify("Usage: sudo python <expression>", severity="warning")
        return
    try:
        result = eval(expr, {"app": app, "sys": sys, "os": os})  # noqa: S307
        app.notify(repr(result)[:800], title="sudo python", timeout=8)
    except Exception:
        tb = traceback.format_exc(limit=3)
        app.notify(tb[:800], severity="error", title="sudo python")


async def _cmd_log(app: RigiApp, **kwargs: Any) -> None:
    msg = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not msg:
        app.notify("Usage: sudo log <message>", severity="warning")
        return
    _log.debug("[%s] %s", app._prog_name, msg)
    app.notify(f"Logged: {msg}", title="sudo log", timeout=3)


async def _cmd_log_level(app: RigiApp, **kwargs: Any) -> None:
    level_str = " ".join(str(v) for v in kwargs.values() if v).strip().upper()
    level = getattr(logging, level_str, None)
    if not isinstance(level, int):
        app.notify(
            f"Unknown level '{level_str}'. Use: DEBUG INFO WARNING ERROR",
            severity="warning",
            title="sudo log_level",
        )
        return
    logging.getLogger("rigi").setLevel(level)
    app.notify(f"rigi logger → {level_str}", title="sudo log_level", timeout=3)


async def _cmd_perf(app: RigiApp, **_: Any) -> None:
    try:
        import time

        refresh_count = getattr(app, "_refresh_count", "n/a")
        start = getattr(app, "_start_time", None)
        uptime = f"{time.time() - start:.1f}s" if start else "n/a"
        lines = [
            f"[bold]Uptime:[/bold]   {uptime}",
            f"[bold]Refreshes:[/bold] {refresh_count}",
            f"[bold]Widgets:[/bold]  {len(list(app.query('*')))}",
            f"[bold]Screens:[/bold]  {len(app.screen_stack)}",
            f"[bold]Cache entries:[/bold] {len(app._rigi_widget_cache)}",
        ]
        app.notify("\n".join(lines), title="sudo perf", timeout=8)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo perf")


async def _cmd_set_theme(app: RigiApp, **kwargs: Any) -> None:
    from rigi.themes import DARK, LIGHT, MONOKAI, NORD

    name = " ".join(str(v) for v in kwargs.values() if v).strip().lower()
    themes = {"dark": DARK, "light": LIGHT, "monokai": MONOKAI, "nord": NORD}
    t = themes.get(name)
    if t is None:
        app.notify(f"Unknown theme '{name}'. Choices: {', '.join(themes)}", severity="warning")
        return
    app.set_theme(t)
    app.notify(f"Theme → {name}", title="sudo set_theme", timeout=2)


async def _cmd_console_info(app: RigiApp, **_: Any) -> None:
    from rigi.core import console

    nfo = console.info()
    lines = [
        f"[bold]Terminal:[/bold]    {nfo['terminal']}",
        f"[bold]True color:[/bold]  {'✓' if nfo['true_color'] else '✗'}",
        f"[bold]Color depth:[/bold] {nfo['color_depth']}",
        f"[bold]Hyperlinks:[/bold]  {'✓' if nfo['hyperlinks'] else '✗'}",
        f"[bold]Kitty gfx:[/bold]   {'✓' if nfo['kitty_graphics'] else '✗'}",
        f"[bold]Sixel:[/bold]       {'✓' if nfo['sixel'] else '✗'}",
        f"[bold]Unicode:[/bold]     {'✓' if nfo['unicode'] else '✗'}",
        f"[bold]Mouse:[/bold]       {'✓' if nfo['mouse'] else '✗'}",
        f"[bold]Multiplexer:[/bold] {'tmux' if nfo['tmux'] else 'screen' if nfo['screen'] else 'none'}",
        f"[bold]Size:[/bold]        {nfo['columns']}×{nfo['lines']}",
    ]
    app.notify("\n".join(lines), title="sudo console", timeout=10)


async def _cmd_widget_styles(app: RigiApp, **_: Any) -> None:
    focused = app.focused
    if focused is None:
        app.notify("No focused widget", severity="warning", title="sudo styles")
        return
    try:
        styles = focused.styles
        lines = [
            f"[bold]background:[/bold] {styles.background}",
            f"[bold]color:[/bold]      {styles.color}",
            f"[bold]width:[/bold]      {styles.width}",
            f"[bold]height:[/bold]     {styles.height}",
            f"[bold]padding:[/bold]    {styles.padding}",
            f"[bold]border:[/bold]     {styles.border_top}",
        ]
        app.notify("\n".join(lines), title=f"sudo styles ({type(focused).__name__})", timeout=8)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo styles")


async def _cmd_hotkeys(app: RigiApp, **_: Any) -> None:
    lines = ["[bold]Active bindings:[/bold]\n"]
    try:
        from textual.binding import Binding as _Binding

        for binding in app.BINDINGS:
            if isinstance(binding, _Binding):
                lines.append(f"  [cyan]{binding.key}[/cyan] → {binding.action}")
    except Exception:
        pass
    app.notify("\n".join(lines), title="sudo hotkeys", timeout=8)


async def _cmd_reload_module(app: RigiApp, **kwargs: Any) -> None:
    mod_name = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not mod_name:
        app.notify("Usage: sudo reload_module <module>", severity="warning")
        return
    try:
        mod = sys.modules.get(mod_name)
        if mod is None:
            app.notify(
                f"Module '{mod_name}' not loaded", severity="warning", title="sudo reload_module"
            )
            return
        importlib.reload(mod)
        app.notify(f"Reloaded: {mod_name}", title="sudo reload_module", timeout=3)
    except Exception as e:
        app.notify(str(e), severity="error", title="sudo reload_module")


# ── Command registry ───────────────────────────────────────────────────────────


def _sub(name: str, help: str, handler: Any, aliases: list[str] | None = None) -> Command:
    cmd = Command(name=name, help=help, aliases=aliases or [], hidden=True)
    cmd.set_handler(handler)
    return cmd


_SUBCOMMANDS: list[Command] = [
    _sub("help", "List all sudo commands", _cmd_help, ["h", "?"]),
    _sub("clear_cache", "Clear widget cache", _cmd_clear_cache, ["cc"]),
    _sub("reload", "Clear cache + refresh layout", _cmd_reload, ["rl"]),
    _sub("reload_css", "Reload all CSS", _cmd_reload_css, ["rcss"]),
    _sub("css", "Inject a CSS rule snippet", _cmd_css),
    _sub("dump_theme", "Dump current theme CSS to /tmp/", _cmd_dump_theme, ["dt"]),
    _sub("inspect", "Show focused widget details", _cmd_inspect, ["i"]),
    _sub("tree", "Show widget DOM tree", _cmd_tree, ["wt"]),
    _sub("focus", "Show currently focused widget path", _cmd_focus),
    _sub("styles", "Show computed styles of focused widget", _cmd_widget_styles, ["st"]),
    _sub("mem", "Show process memory usage", _cmd_mem),
    _sub("gc", "Run garbage collection", _cmd_gc),
    _sub("tracemalloc", "Toggle tracemalloc (memory profiling)", _cmd_tracemalloc, ["tm"]),
    _sub("perf", "Show performance stats", _cmd_perf),
    _sub("screenshot", "Save SVG screenshot to /tmp/", _cmd_screenshot, ["ss"]),
    _sub("env", "Dump environment variables [filter]", _cmd_env),
    _sub("tabs", "List tabs + cache state", _cmd_tabs),
    _sub("cmds", "List all commands (incl. hidden)", _cmd_cmds),
    _sub("hotkeys", "Show active key bindings", _cmd_hotkeys, ["hk"]),
    _sub("bell", "Ring the terminal bell", _cmd_bell),
    _sub("dn_test", "Test desktop notification", _cmd_dn_test),
    _sub("set_theme", "Force a theme: dark|light|monokai|nord", _cmd_set_theme, ["st2"]),
    _sub("console", "Show terminal capability info", _cmd_console_info, ["con"]),
    _sub("python", "Eval Python expression in app context", _cmd_python, ["py"]),
    _sub("log", "Write message to rigi logger at DEBUG", _cmd_log),
    _sub("log_level", "Set rigi log level: DEBUG INFO WARNING …", _cmd_log_level, ["ll"]),
    _sub("reload_module", "Reload a loaded Python module", _cmd_reload_module, ["rm"]),
    _sub("crash", "Raise a test exception", _cmd_crash),
]


def register_dev_commands(registry: Any) -> None:
    """Register the hidden `sudo` command tree into *registry*."""
    sudo_cmd = Command(
        name="sudo",
        help="Developer commands (hidden from autocomplete)",
        hidden=True,
        subcommands=list(_SUBCOMMANDS),
    )
    registry.register(sudo_cmd)
