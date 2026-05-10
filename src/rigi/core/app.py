from __future__ import annotations

import asyncio
import getpass
import logging
import os
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget

from rigi.commands.command import Command
from rigi.commands.parser import build_cli_parser, parse_inline
from rigi.commands.provider import RigiCommandProvider
from rigi.commands.registry import CommandRegistry
from rigi.core import console as _console
from rigi.core import log_store
from rigi.core import platform as _platform_utils
from rigi.core.dev_commands import register_dev_commands
from rigi.core.types import HandlerFn, HelpEntry, StatusItem, SubtabDef, TabDef
from rigi.screens.hamburger import RigiHamburgerScreen
from rigi.screens.help import RigiHelpScreen
from rigi.screens.settings import RigiSettingDef, RigiSettingsScreen
from rigi.themes import DARK as _DEFAULT_THEME
from rigi.themes import RigiTheme
from rigi.widgets.border_frame import RigiBorderFrame
from rigi.widgets.bottom_panel import RigiBottomPanel
from rigi.widgets.content_area import RigiContentArea
from rigi.widgets.hamburger_menu import RigiMenuItemData
from rigi.widgets.help_panel import RigiShortcutsBar, extract_help_annotation
from rigi.widgets.sidebar import RigiSidebar
from rigi.widgets.statusbar import (
    RigiStatusBar,
    _HamburgerButton,
    _HomeButton,
)

# Логгеры
_ui_log = logging.getLogger("rigi.ui")
_terminal_log = logging.getLogger("rigi.terminal")

_CSS_PATH = Path(__file__).parent.parent / "css" / "default.tcss"


class _RigiBody(Widget):
    DEFAULT_CSS = """
    _RigiBody {
        layout: horizontal;
        height: 1fr;
        width: 100%;
        background: transparent;
    }
    """

    def compose(self) -> ComposeResult:
        yield from []


class RigiApp(App[None]):
    CSS_PATH = str(_CSS_PATH)

    COMMANDS = {RigiCommandProvider}

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "copy_focused", "Copy", show=False, priority=True),
        Binding("ctrl+t", "focus_terminal", "Terminal", show=False),
        Binding("ctrl+h", "show_help", "Help", show=False),
        Binding("up", "nav_up", "Up", show=False),
        Binding("down", "nav_down", "Down", show=False),
        Binding("right", "nav_right", "Enter", show=False),
        Binding("left", "nav_left", "Back", show=False),
    ]

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        username: str | None = None,
        sidebar_width: int = 20,
        terminal_label: str | None = None,
        theme: RigiTheme | None = None,
        home_tab: str | None = None,
        persist_history: bool = True,
    ) -> None:
        super().__init__()
        self._prog_name = name
        self._version = version
        self._description = description
        self._username = username or getpass.getuser()
        self._persist_history = persist_history

        # Environment variable overrides
        env_width = os.environ.get("RIGI_SIDEBAR_WIDTH")
        self._sidebar_width = int(env_width) if env_width and env_width.isdigit() else sidebar_width

        self._terminal_label = terminal_label

        # Theme: explicit arg → RIGI_THEME env → default
        resolved_theme = theme
        if resolved_theme is None:
            env_theme = os.environ.get("RIGI_THEME", "").lower()
            if env_theme:
                from rigi.themes import DARK, LIGHT, MONOKAI, NORD

                resolved_theme = {
                    "dark": DARK,
                    "light": LIGHT,
                    "monokai": MONOKAI,
                    "nord": NORD,
                }.get(env_theme)
        self._theme: RigiTheme = resolved_theme if resolved_theme is not None else _DEFAULT_THEME
        self._theme_tie_breaker: int = 200
        self._home_tab_name: str | None = home_tab

        self._cmd_registry = CommandRegistry()
        self._rigi_tabs: list[TabDef] = []
        self._rigi_status_items: list[StatusItem] = []
        self._rigi_startup_hooks: list[Callable[[RigiApp], Awaitable[None] | None]] = []
        self._rigi_widget_cache: dict[tuple[int, ...], Widget] = {}
        self._rigi_extra_css: list[Path] = []
        self._rigi_help_entries: list[HelpEntry] = []
        self._rigi_menu_items: list[tuple[str, str, Callable[[], None]]] = []
        self._rigi_settings: list[RigiSettingDef] = []

        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        help_cmd = Command(
            name="help", help="Show available commands or detailed help for a command"
        )
        help_cmd.add_arg("command", help="Command name to get detailed help", required=False)
        help_cmd.set_handler(self._cmd_help)
        help_cmd.set_terminal_help(
            "[bold]Usage:[/bold]\n"
            "  help          - Show all available commands\n"
            "  help <cmd>    - Show detailed help for a specific command\n\n"
            "[bold]Examples:[/bold]\n"
            "  help\n"
            "  help quit\n"
            "  help terminal"
        )
        self._cmd_registry.register(help_cmd)

        quit_cmd = Command(name="quit", help="Exit the application", aliases=["exit", "q"])
        quit_cmd.set_handler(self._cmd_quit)
        quit_cmd.set_terminal_help("Exit the application immediately. No confirmation required.")
        self._cmd_registry.register(quit_cmd)

        clear_cmd = Command(name="clear", help="Clear the terminal history", aliases=["cls"])
        clear_cmd.set_handler(self._cmd_clear)
        clear_cmd.set_terminal_help("Clear all terminal output history. Logs are not affected.")
        self._cmd_registry.register(clear_cmd)

        term_cmd = Command(name="terminal", help="Show terminal capabilities", aliases=["term"])
        term_cmd.set_handler(self._cmd_terminal)
        term_cmd.set_terminal_help(
            "Display information about the current terminal:\n"
            "  - Terminal emulator name\n"
            "  - Color support (true color, depth)\n"
            "  - Feature support (hyperlinks, unicode, mouse, graphics)\n"
            "  - Multiplexer detection (tmux, screen)\n"
            "  - Terminal size"
        )
        self._cmd_registry.register(term_cmd)

        register_dev_commands(self._cmd_registry)

    async def _cmd_terminal(self, app: RigiApp, **_: Any) -> None:
        nfo = _console.info()
        lines = [
            f"[bold]Terminal:[/bold]   {nfo['terminal']}",
            f"[bold]True color:[/bold] {'yes' if nfo['true_color'] else 'no'}  "
            f"[dim](depth {nfo['color_depth']})[/dim]",
            f"[bold]Hyperlinks:[/bold] {'yes' if nfo['hyperlinks'] else 'no'}",
            f"[bold]Unicode:[/bold]    {'yes' if nfo['unicode'] else 'no'}",
            f"[bold]Mouse:[/bold]      {'yes' if nfo['mouse'] else 'no'}",
            f"[bold]Kitty gfx:[/bold]  {'yes' if nfo['kitty_graphics'] else 'no'}",
            f"[bold]Multiplexer:[/bold]{'tmux' if nfo['tmux'] else 'screen' if nfo['screen'] else 'none'}",
            f"[bold]Size:[/bold]       {nfo['columns']}×{nfo['lines']}",
        ]
        app.notify("\n".join(lines), title="Terminal Info", timeout=8)

    async def _cmd_help(self, app: RigiApp, **kwargs: Any) -> None:
        # Проверяем, запрашивается ли помощь по конкретной команде
        cmd_name = kwargs.get("command")

        if cmd_name:
            # Показываем подробную помощь по команде
            cmd = self._cmd_registry.get(cmd_name)
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
            # Показываем список всех команд
            lines = ["[bold]Available commands:[/bold]\n"]
            for cmd in self._cmd_registry.all():
                if not cmd.hidden:
                    aliases = f" [dim]({', '.join(cmd.aliases)})[/dim]" if cmd.aliases else ""
                    lines.append(f"  [cyan]{cmd.name}[/cyan]{aliases} - {cmd.help}")

            lines.append("\n[dim]Type 'help <command>' for detailed information[/dim]")
            lines.append("[dim]Type '!<shell command>' to run shell commands[/dim]")
            app.notify("\n".join(lines), title="Terminal Help", timeout=12)

    async def _cmd_quit(self, **_: Any) -> None:
        self.exit()

    async def _cmd_clear(self, **_: Any) -> None:
        try:
            self.query_one(RigiBottomPanel).clear_history_view()
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        status_bar = RigiStatusBar()
        for item in self._rigi_status_items:
            status_bar._items.append(item)

        with RigiBorderFrame(self._prog_name, self._version):
            yield status_bar

            with _RigiBody():
                yield RigiSidebar()
                yield RigiContentArea()

            yield RigiShortcutsBar()
            prompt = self._terminal_label or f"{self._username}@{self._prog_name}"
            history_file: Path | None = None
            if self._persist_history:
                try:
                    history_file = _platform_utils.config_dir(self._prog_name) / "terminal_history"
                except Exception:
                    pass
            yield RigiBottomPanel(
                prompt_text=prompt,
                registry=self._cmd_registry,
                history_file=history_file,
            )

    def on_mount(self) -> None:
        self.title = f"{self._prog_name} v{self._version}"
        self.sub_title = self._description

        self.set_theme(self._theme)

        for css_path in self._rigi_extra_css:
            self._apply_css_file(css_path)

        sidebar = self.query_one(RigiSidebar)
        sidebar.set_tabs(self._rigi_tabs)

        if self._rigi_tabs:
            self._navigate_to(0, [])

        self._update_home_button()

        for hook in self._rigi_startup_hooks:
            result = hook(self)
            if asyncio.iscoroutine(result):
                self.run_worker(result, name="rigi-startup-hook")

        self._set_terminal_title()
        self.set_focus(None)
        log_store.install()

    def _set_terminal_title(self) -> None:
        title = f"{self._prog_name} {self._version}"
        seq = _console.set_title(title)
        try:
            with open("/dev/tty", "w") as tty:
                tty.write(seq)
        except Exception:
            pass

    @property
    def terminal(self) -> str:
        """Name of the running terminal (kitty, iterm2, wezterm, etc.)."""
        return _console.detect_terminal()

    @property
    def terminal_info(self) -> dict[str, object]:
        """Dict of terminal capabilities: true_color, unicode, hyperlinks, …"""
        return _console.info()

    def hyperlink(self, url: str, text: str) -> str:
        """Return an OSC 8 hyperlink if the terminal supports it, else plain text."""
        return _console.hyperlink(url, text)

    def _apply_css_file(self, path: Path) -> None:
        try:
            css_text = path.read_text(encoding="utf-8")
            self.stylesheet.add_source(
                css_text,
                read_from=(str(path), str(path)),
                is_default_css=False,
                tie_breaker=100,
            )
            self.refresh_css(animate=False)
            _ui_log.info(f"CSS loaded: {path.name}")
        except Exception as exc:
            _ui_log.error(f"CSS load error ({path.name}): {exc}", exc_info=True)
            self.notify(f"CSS load error ({path.name}): {exc}", severity="error")

    @on(RigiSidebar.NavigationChanged)
    def on_sidebar_nav(self, event: RigiSidebar.NavigationChanged) -> None:
        self._navigate_to(event.tab_idx, event.subtab_path)
        self._update_home_button()

    def _home_tab_idx(self) -> int:
        if self._home_tab_name:
            for i, tab in enumerate(self._rigi_tabs):
                if tab.name.lower() == self._home_tab_name.lower():
                    return i
        return 0

    def _update_home_button(self) -> None:
        try:
            sidebar = self.query_one(RigiSidebar)
            on_home = sidebar._active_tab == self._home_tab_idx() and sidebar._active_path == []
            self.query_one(RigiStatusBar).set_home_active(on_home)
        except Exception:
            pass

    @on(_HomeButton.Clicked)
    def on_home_clicked(self, event: _HomeButton.Clicked) -> None:
        event.stop()
        idx = self._home_tab_idx()
        if idx < len(self._rigi_tabs):
            tab = self._rigi_tabs[idx]
            self.navigate_to_tab(tab.name)
            self._update_home_button()

    def _navigate_to(self, tab_idx: int, subtab_path: list[int]) -> None:
        try:
            if tab_idx >= len(self._rigi_tabs):
                _ui_log.warning(f"Invalid tab index: {tab_idx}")
                return
            tab = self._rigi_tabs[tab_idx]
            cache_key = (tab_idx, *subtab_path)

            if cache_key not in self._rigi_widget_cache:
                factory = self._resolve_factory(tab, subtab_path)
                if factory is None:
                    _ui_log.warning(f"No factory found for tab {tab_idx}, path {subtab_path}")
                    return
                self._rigi_widget_cache[cache_key] = factory()

            content = self.query_one(RigiContentArea)
            content.show_widget(self._rigi_widget_cache[cache_key])
        except Exception as e:
            _ui_log.error(f"Error navigating to tab {tab_idx}: {e}", exc_info=True)
            self.notify("Navigation error - check logs", severity="error")

    def _resolve_factory(self, tab: TabDef, path: list[int]) -> Callable[[], Widget] | None:
        if not path:
            return tab.widget_factory
        try:
            node: SubtabDef = tab.subtabs[path[0]]
            for idx in path[1:]:
                node = node.children[idx]
            return node.widget_factory
        except (IndexError, AttributeError):
            return None

    @on(RigiBottomPanel.CommandSubmitted)
    def on_command_submitted(self, event: RigiBottomPanel.CommandSubmitted) -> None:
        self.run_worker(self._handle_command(event.text), name="rigi-cmd", exclusive=False)

    async def _handle_command(self, text: str) -> None:
        stripped = text.strip()
        _terminal_log.debug(f"Command received: {stripped}")

        # !<shell command>  (not !sudo)
        if stripped.startswith("!") and not stripped[1:].lstrip().lower().startswith("sudo"):
            await self._run_shell(stripped[1:].strip())
            return

        # Strip leading ! before sudo  (!sudo ... → sudo ...)
        if stripped.startswith("!"):
            stripped = stripped[1:].strip()

        cmd, parsed = parse_inline(stripped, self._cmd_registry)
        if "_error" in parsed:
            # Better error for unknown sudo subcommand
            if stripped.lower().startswith("sudo"):
                parts = stripped.split()
                sub = parts[1] if len(parts) > 1 else ""
                self.notify(
                    f"Unknown sudo command: {sub!r}\nType 'sudo help' for a list.",
                    severity="error",
                )
            else:
                self.notify(parsed["_error"], severity="error")
            _terminal_log.warning(f"Command error: {parsed.get('_error', 'Unknown error')}")
            return
        if cmd is None:
            return

        nav_tab = next(
            (t for t in self._rigi_tabs if t.name.lower() == cmd.name.lower()),
            None,
        )
        if nav_tab is not None and cmd.handler is None:
            self.navigate_to_tab(nav_tab.name)
            _terminal_log.info(f"Navigated to tab: {nav_tab.name}")
            return

        try:
            await cmd.execute(parsed, self)
            _terminal_log.info(f"Command executed successfully: {cmd.name}")
        except Exception as exc:
            self.notify(str(exc), severity="error")
            _terminal_log.error(f"Command execution failed: {cmd.name}", exc_info=True)

    async def _run_shell(self, cmd: str) -> None:
        if not cmd:
            return
        _terminal_log.debug(f"Executing shell command: {cmd}")
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
            except asyncio.TimeoutError:
                proc.kill()
                self.notify(
                    "Shell command timed out (15s)", severity="error", title=f"$ {cmd[:30]}"
                )
                _terminal_log.error(f"Shell command timed out: {cmd}")
                return
            out = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()
            display = out[:1200] if out else "(no output)"
            _terminal_log.info(f"Shell command completed: {cmd}")
            try:
                self.query_one(RigiBottomPanel).write_output(display)
            except Exception:
                self.notify(display, title=f"$ {cmd[:40]}", timeout=12)
        except Exception as exc:
            msg = str(exc)
            _terminal_log.error(f"Shell command failed: {cmd}", exc_info=True)
            try:
                self.query_one(RigiBottomPanel).write_output(f"[red]{msg}[/red]")
            except Exception:
                self.notify(msg, severity="error", title=f"$ {cmd[:30]}")

    @on(_HamburgerButton.Clicked)
    def on_hamburger_clicked(self, event: _HamburgerButton.Clicked) -> None:
        event.stop()
        self.push_screen(RigiHamburgerScreen(self._build_hamburger_sections()))

    def _build_hamburger_sections(
        self,
    ) -> list[tuple[str, list[RigiMenuItemData]]]:
        from rigi.themes import DARK, LIGHT, MONOKAI, NORD

        builtin_themes = [DARK, LIGHT, MONOKAI, NORD]

        theme_submenu = [
            RigiMenuItemData(
                label=t.name.capitalize(),
                callback=lambda _t=t: self.set_theme(_t),
                checked=(t.name == self._theme.name),
            )
            for t in builtin_themes
        ]

        main_items: list[RigiMenuItemData] = [
            RigiMenuItemData("Theme", submenu=theme_submenu),
            RigiMenuItemData("Settings", callback=self._open_settings),
            RigiMenuItemData(
                "Help",
                callback=lambda: self.run_worker(self.action_show_help(), name="rigi-help"),
            ),
        ]

        by_section: dict[str, list[RigiMenuItemData]] = {}
        for sec, lbl, cb in self._rigi_menu_items:
            by_section.setdefault(sec, []).append(RigiMenuItemData(lbl, cb))

        sections: list[tuple[str, list[RigiMenuItemData]]] = [("", main_items)]
        for sec_name, items in by_section.items():
            sections.append((sec_name, items))

        return sections

    def _open_settings(self) -> None:
        builtin = [
            RigiSettingDef(
                category="Appearance",
                label="Theme",
                description="Color theme for the interface",
                value_fn=lambda: self._theme.name.capitalize(),
                action_fn=self._cycle_theme,
                action_label="Cycle",
            ),
            RigiSettingDef(
                category="Terminal",
                label="Emulator",
                description="Detected terminal application",
                value_fn=lambda: _console.detect_terminal(),
            ),
            RigiSettingDef(
                category="Terminal",
                label="True color",
                description="24-bit color support",
                value_fn=lambda: "yes" if _console.supports_true_color() else "no",
            ),
            RigiSettingDef(
                category="Terminal",
                label="Hyperlinks",
                description="OSC 8 clickable link support",
                value_fn=lambda: "yes" if _console.supports_hyperlinks() else "no",
            ),
            RigiSettingDef(
                category="Terminal",
                label="Multiplexer",
                description="Running inside tmux or screen",
                value_fn=lambda: (
                    "tmux" if _console.IS_TMUX else ("screen" if _console.IS_SCREEN else "none")
                ),
            ),
            RigiSettingDef(
                category="Terminal",
                label="Unicode",
                description="UTF-8 output encoding",
                value_fn=lambda: "yes" if _console.supports_unicode() else "no",
            ),
        ]
        self.push_screen(RigiSettingsScreen(builtin + self._rigi_settings))

    def _cycle_theme(self) -> None:
        from rigi.themes import DARK, LIGHT, MONOKAI, NORD

        _themes = [DARK, LIGHT, MONOKAI, NORD]
        names = [t.name for t in _themes]
        try:
            idx = (names.index(self._theme.name) + 1) % len(_themes)
        except ValueError:
            idx = 0
        self.set_theme(_themes[idx])

    def _terminal_input_focused(self) -> bool:
        try:
            return self.query_one("#terminal-input").has_focus
        except Exception:
            return False

    def action_nav_up(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(RigiSidebar).navigate(-1)

    def action_nav_down(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(RigiSidebar).navigate(1)

    def action_nav_right(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(RigiSidebar).navigate_right()

    def action_nav_left(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(RigiSidebar).navigate_left()

    def action_focus_terminal(self) -> None:
        self.query_one(RigiBottomPanel).focus_input()

    async def action_show_help(self) -> None:
        await self.push_screen(RigiHelpScreen(self._rigi_help_entries))

    def action_copy_focused(self) -> None:
        text = self._extract_focused_text()
        if text:
            if _platform_utils.copy_to_clipboard(text):
                self.notify("Copied to clipboard", timeout=2)
            else:
                # Textual built-in fallback
                try:
                    self.copy_to_clipboard(text)
                    self.notify("Copied to clipboard", timeout=2)
                except Exception:
                    self.notify("Clipboard unavailable", severity="warning", timeout=2)
        else:
            self.notify("Nothing to copy", severity="warning", timeout=2)

    def _extract_focused_text(self) -> str:
        from rich.text import Text as RichText
        from textual.widgets import DataTable, Input, Label

        focused = self.focused
        if focused is None:
            return ""

        if isinstance(focused, Input):
            return focused.value

        if isinstance(focused, DataTable):
            try:
                coord = focused.cursor_coordinate
                row_key, _ = focused.coordinate_to_cell_key(coord)
                cols = list(focused.columns)
                row: list[str] = []
                for ck in cols:
                    try:
                        row.append(str(focused.get_cell(row_key, ck)))
                    except Exception:
                        pass
                return "\t".join(row) if row else str(focused.get_cell_at(coord))
            except Exception:
                pass

        if isinstance(focused, Label):
            try:
                rendered = focused.render()
                if isinstance(rendered, str):
                    return rendered
                if isinstance(rendered, RichText):
                    return rendered.plain
            except Exception:
                pass

        return ""

    def open_url(self, url: str, *, new_tab: bool = True) -> None:
        """Open *url* in the default browser."""
        if not _platform_utils.open_url(url):
            super().open_url(url, new_tab=new_tab)

    def open_path(self, path: str | Path) -> bool:
        """Open a file or directory with the OS default application."""
        return _platform_utils.open_path(path)

    def notify_desktop(self, title: str, body: str = "", urgency: str = "normal") -> bool:
        """Send an OS desktop notification (notify-send / osascript / PowerShell)."""
        return _platform_utils.notify_desktop(title, body, urgency)

    def schedule_task(
        self,
        coro: Any,
        *,
        name: str = "rigi-task",
        on_done: Callable[[Any], None] | None = None,
    ) -> asyncio.Task[Any]:
        """Schedule *coro* as a background asyncio task.

        ``on_done`` is called with the return value when the task finishes.
        """

        async def _wrapped() -> Any:
            result = await (coro if asyncio.iscoroutine(coro) else coro())
            if on_done is not None:
                on_done(result)
            return result

        return asyncio.create_task(_wrapped(), name=name)

    async def action_quit(self) -> None:
        try:
            self.query_one(RigiBottomPanel).save_history()
        except Exception:
            pass
        self.exit()

    def add_tab(self, tab: TabDef) -> TabDef:
        self._rigi_tabs.append(tab)
        return tab

    def add_status(
        self,
        key: str,
        label: str,
        value_fn: Callable[[], Any],
        style: str = "bold white",
        refresh_interval: float = 1.0,
    ) -> StatusItem:
        item = StatusItem(
            key=key, label=label, value_fn=value_fn, style=style, refresh_interval=refresh_interval
        )
        self._rigi_status_items.append(item)
        if self.is_running:
            self.query_one(RigiStatusBar).add_item(item)
        return item

    def add_menu_item(
        self,
        label: str,
        callback: Callable[[], None],
        section: str = "Settings",
    ) -> None:
        self._rigi_menu_items.append((section, label, callback))

    def add_setting(
        self,
        category: str,
        label: str,
        description: str = "",
        value_fn: Callable[[], str] | None = None,
        action_fn: Callable[[], None] | None = None,
        action_label: str = "Change",
    ) -> RigiSettingDef:
        s = RigiSettingDef(category, label, description, value_fn, action_fn, action_label)
        self._rigi_settings.append(s)
        return s

    def register_css(self, path: str | Path) -> None:
        p = Path(path).expanduser().resolve()
        self._rigi_extra_css.append(p)
        if self.is_running:
            self._apply_css_file(p)

    def set_theme(self, theme: RigiTheme) -> None:
        try:
            self._theme = theme
            self._theme_tie_breaker += 1
            self.stylesheet.add_source(
                theme.to_css(),
                read_from=(
                    f"__rigi_theme_{self._theme_tie_breaker}__",
                    f"__rigi_theme_{self._theme_tie_breaker}__",
                ),
                is_default_css=False,
                tie_breaker=self._theme_tie_breaker,
            )
            self.refresh_css(animate=False)
            _ui_log.info(f"Theme changed to: {theme.name}")
        except Exception as exc:
            _ui_log.error(f"Theme error: {exc}", exc_info=True)
            self.notify(f"Theme error: {exc}", severity="error")

    def set_terminal_label(self, label: str) -> None:
        self._terminal_label = label
        try:
            self.query_one(RigiBottomPanel).prompt_text = label
        except Exception:
            pass

    def command(
        self,
        name: str,
        help: str = "",
        aliases: list[str] | None = None,
    ) -> Callable[[HandlerFn], HandlerFn]:
        def decorator(fn: HandlerFn) -> HandlerFn:
            cmd = Command(name=name, help=help, aliases=aliases or [])
            cmd.set_handler(fn)
            self._cmd_registry.register(cmd)
            ann = extract_help_annotation(fn)
            if ann:
                self._rigi_help_entries.append(HelpEntry(key=name, description=ann))
            return fn

        return decorator

    def register_command(self, cmd: Command) -> Command:
        self._cmd_registry.register(cmd)
        if cmd.handler:
            ann = extract_help_annotation(cmd.handler)
            if ann:
                self._rigi_help_entries.append(HelpEntry(key=cmd.name, description=ann))
        return cmd

    def on_startup(
        self, fn: Callable[[RigiApp], Awaitable[None] | None]
    ) -> Callable[[RigiApp], Awaitable[None] | None]:
        self._rigi_startup_hooks.append(fn)
        return fn

    def navigate_to_tab(self, name: str) -> bool:
        for idx, tab in enumerate(self._rigi_tabs):
            if tab.name.lower() == name.lower():
                self.query_one(RigiSidebar).jump_to_tab_by_key(tab.key or "")
                self._navigate_to(idx, [])
                return True
        return False

    def invalidate_tab_cache(self, tab_name: str | None = None) -> None:
        content = self.query_one(RigiContentArea) if self.is_running else None

        def _evict(widget: Widget) -> None:
            if content and widget is content._current:
                content.clear()
            if widget.is_mounted:
                widget.remove()

        if tab_name is None:
            for w in list(self._rigi_widget_cache.values()):
                _evict(w)
            self._rigi_widget_cache.clear()
            return

        for idx, tab in enumerate(self._rigi_tabs):
            if tab.name.lower() == tab_name.lower():
                for key in list(self._rigi_widget_cache):
                    if key[0] == idx:
                        _evict(self._rigi_widget_cache.pop(key))

    @property
    def cmd_registry(self) -> CommandRegistry:
        return self._cmd_registry

    @classmethod
    def run_cli(cls, app_instance: RigiApp) -> None:
        parser = build_cli_parser(
            prog_name=app_instance._prog_name,
            version=app_instance._version,
            registry=app_instance._cmd_registry,
            description=app_instance._description,
        )

        args = sys.argv[1:]
        if not args:
            app_instance.run()
            return

        parsed, _ = parser.parse_known_args(args)
        ns = vars(parsed)
        cmd_name = ns.pop("_command", None)

        if cmd_name is None:
            app_instance.run()
            return

        cmd = app_instance._cmd_registry.get(cmd_name)
        if cmd is None:
            parser.print_help()
            sys.exit(1)

        tab = next((t for t in app_instance._rigi_tabs if t.name.lower() == cmd_name.lower()), None)
        if tab and cmd.handler is None:

            async def _nav() -> None:
                app_instance.navigate_to_tab(tab.name)

            app_instance._rigi_startup_hooks.append(lambda _: _nav())
            app_instance.run()
            return

        asyncio.run(cmd.execute(ns, app_instance))
