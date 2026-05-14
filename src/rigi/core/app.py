from __future__ import annotations

import asyncio
import getpass
import logging
import os
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from textual import on
from textual.app import App as _TextualApp
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.notifications import SeverityLevel
from textual.widget import Widget

from rigi.commands.command import Command
from rigi.commands.parser import build_cli_parser, parse_inline
from rigi.commands.provider import CommandProvider
from rigi.commands.registry import CommandRegistry
from rigi.core import console as _console
from rigi.core import log_store
from rigi.core import platform as _platform_utils
from rigi.core._cmd_handlers import cmd_clear, cmd_help, cmd_quit, cmd_terminal
from rigi.core.dev_commands import register_dev_commands
from rigi.core.settings_manager import SettingsManager
from rigi.core.types import HandlerFn, HelpEntry, StatusItem, SubtabDef, TabDef
from rigi.screens.settings import SettingDef
from rigi.themes import DARK as _DEFAULT_THEME
from rigi.themes import Theme
from rigi.widgets.action_menu import ActionMenuItemData, ActionMenuPanel
from rigi.widgets.border_frame import BorderFrame
from rigi.widgets.bottom_panel import BottomPanel
from rigi.widgets.content_area import ContentArea
from rigi.widgets.hamburger_menu import MenuItemData, MenuPanel
from rigi.widgets.help_overlay import HelpOverlay
from rigi.widgets.help_panel import ShortcutsBar, extract_help_annotation
from rigi.widgets.notifications import NotificationRack
from rigi.widgets.settings_overlay import SettingsOverlay
from rigi.widgets.sidebar import Sidebar
from rigi.widgets.statusbar import (
    StatusBar,
    _HamburgerButton,
    _HomeButton,
)

_ui_log = logging.getLogger("rigi.ui")
_terminal_log = logging.getLogger("rigi.terminal")

_CSS_PATH = Path(__file__).parent.parent / "css" / "default.tcss"


class _Body(Widget):
    def compose(self) -> ComposeResult:
        yield from []


class App(_TextualApp[None]):
    CSS_PATH = str(_CSS_PATH)

    COMMANDS = {CommandProvider}

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
        theme: Theme | None = None,
        home_tab: str | None = None,
        persist_history: bool = True,
    ) -> None:
        super().__init__()
        self._prog_name = name
        self._version = version
        self._description = description
        self._username = username or getpass.getuser()
        self._persist_history = persist_history

        env_width = os.environ.get("RIGI_SIDEBAR_WIDTH")
        self._sidebar_width = int(env_width) if env_width and env_width.isdigit() else sidebar_width

        self._terminal_label = terminal_label

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
        self._theme: Theme = resolved_theme if resolved_theme is not None else _DEFAULT_THEME
        self._theme_tie_breaker: int = 200
        self._home_tab_name: str | None = home_tab

        self._cmd_registry = CommandRegistry()
        self._rigi_tabs: list[TabDef] = []
        self._rigi_status_items: list[StatusItem] = []
        self._rigi_startup_hooks: list[Callable[[App], Awaitable[None] | None]] = []
        self._rigi_widget_cache: dict[tuple[int, ...], Widget] = {}
        self._rigi_extra_css: list[Path] = []
        self._rigi_help_entries: list[HelpEntry] = []
        self._rigi_menu_items: list[tuple[str, str, Callable[[], None]]] = []
        self._settings_manager = SettingsManager()
        self._transparent_enabled: bool = False
        self._transparent_percent: int = 50

        self._disable_notifications = True
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        help_cmd = Command(
            name="help", help="Show available commands or detailed help for a command"
        )
        help_cmd.add_arg("command", help="Command name to get detailed help", required=False)
        help_cmd.set_handler(cmd_help)
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
        quit_cmd.set_handler(cmd_quit)
        quit_cmd.set_terminal_help("Exit the application immediately. No confirmation required.")
        self._cmd_registry.register(quit_cmd)

        clear_cmd = Command(name="clear", help="Clear the terminal history", aliases=["cls"])
        clear_cmd.set_handler(cmd_clear)
        clear_cmd.set_terminal_help("Clear all terminal output history. Logs are not affected.")
        self._cmd_registry.register(clear_cmd)

        term_cmd = Command(name="terminal", help="Show terminal capabilities", aliases=["term"])
        term_cmd.set_handler(cmd_terminal)
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

    def compose(self) -> ComposeResult:
        status_bar = StatusBar()
        for item in self._rigi_status_items:
            status_bar._items.append(item)

        with BorderFrame(self._prog_name, self._version):
            yield status_bar

            with _Body():
                yield Sidebar()
                yield ContentArea()

            yield ShortcutsBar()
            prompt = self._terminal_label or f"{self._username}@{self._prog_name}"
            history_file: Path | None = None
            if self._persist_history:
                try:
                    history_file = _platform_utils.config_dir(self._prog_name) / "terminal_history"
                except Exception:
                    pass
            yield BottomPanel(
                prompt_text=prompt,
                registry=self._cmd_registry,
                history_file=history_file,
            )
        yield NotificationRack()

    def on_mount(self) -> None:
        self.title = f"{self._prog_name} v{self._version}"
        self.sub_title = self._description

        self.set_theme(self._theme)

        for css_path in self._rigi_extra_css:
            self._apply_css_file(css_path)

        sidebar = self.query_one(Sidebar)
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
        self._reposition_notifications()

    def on_resize(self) -> None:
        self._reposition_notifications()

    def _reposition_notifications(self) -> None:
        try:
            rack = self.query_one(NotificationRack)
            rack_w = 52
            rack.styles.offset = (max(0, self.size.width - rack_w), 3)
        except Exception:
            pass

    def _set_terminal_title(self) -> None:
        seq = _console.set_title(f"{self._prog_name} {self._version}")
        try:
            with open("/dev/tty", "w") as tty:
                tty.write(seq)
        except Exception:
            pass

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: float | None = 5.0,
        markup: bool = True,
    ) -> None:
        if not markup:
            message = message.replace("[", "\\[")
        effective_timeout = timeout if timeout is not None else 5.0
        try:
            self.query_one(NotificationRack).add_notification(
                title, message, severity, effective_timeout
            )
        except Exception:
            pass

    @property
    def terminal(self) -> str:
        return _console.detect_terminal()

    @property
    def terminal_info(self) -> dict[str, object]:
        return _console.info()

    def hyperlink(self, url: str, text: str) -> str:
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

    def register_css(self, path: str | Path) -> None:
        p = Path(path).expanduser().resolve()
        self._rigi_extra_css.append(p)
        if self.is_running:
            self._apply_css_file(p)

    def set_theme(self, theme: Theme) -> None:
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
            self._apply_transparency()
            _ui_log.info(f"Theme changed to: {theme.name}")
        except Exception as exc:
            _ui_log.error(f"Theme error: {exc}", exc_info=True)
            self.notify(f"Theme error: {exc}", severity="error")

    def _toggle_transparency(self) -> None:
        self._transparent_enabled = not self._transparent_enabled
        self._apply_transparency()

    def _set_transparency_percent(self, value: str) -> None:
        try:
            self._transparent_percent = max(0, min(100, int(value)))
        except ValueError:
            pass
        self._apply_transparency()

    def _apply_transparency(self) -> None:
        if not self.is_running:
            return
        try:
            if self._transparent_enabled:
                alpha = max(0.0, min(1.0, 1.0 - (self._transparent_percent / 100.0)))
                bg = self._theme.bg_color
                if bg.startswith("#") and len(bg) == 7:
                    r = int(bg[1:3], 16)
                    g = int(bg[3:5], 16)
                    b = int(bg[5:7], 16)
                    rgba = f"rgb({r} {g} {b} / {alpha})"
                else:
                    rgba = bg
                css = f"""
App, Screen {{
    background: transparent;
}}
BorderFrame, _Body, Sidebar, ContentArea, #content-main,
_MainNav, _SubNav, BottomPanel, TerminalBar,
StatusBar, ShortcutsBar, _VerticalResizeHandle, _ContentResizeHandle {{
    background: {rgba};
}}
"""
            else:
                css = f"""
App, Screen {{
    background: {self._theme.bg_color};
}}
BorderFrame, _Body, Sidebar, ContentArea, #content-main,
_MainNav, _SubNav, BottomPanel, TerminalBar,
StatusBar, ShortcutsBar, _VerticalResizeHandle, _ContentResizeHandle {{
    background: {self._theme.bg_color};
}}
"""
            self._theme_tie_breaker += 1
            self.stylesheet.add_source(
                css,
                read_from=(
                    f"__rigi_transparency_{self._theme_tie_breaker}__",
                    f"__rigi_transparency_{self._theme_tie_breaker}__",
                ),
                is_default_css=False,
                tie_breaker=self._theme_tie_breaker,
            )
            self.refresh_css(animate=False)
        except Exception as exc:
            _ui_log.error(f"Transparency error: {exc}", exc_info=True)

    def _cycle_theme(self) -> None:
        from rigi.themes import DARK, LIGHT, MONOKAI, NORD

        _themes = [DARK, LIGHT, MONOKAI, NORD]
        names = [t.name for t in _themes]
        try:
            idx = (names.index(self._theme.name) + 1) % len(_themes)
        except ValueError:
            idx = 0
        self.set_theme(_themes[idx])

    @on(Sidebar.NavigationChanged)
    def on_sidebar_nav(self, event: Sidebar.NavigationChanged) -> None:
        self._navigate_to(event.tab_idx, event.subtab_path)
        self._update_home_button()
        try:
            self.query_one("#rigi-action-panel", ActionMenuPanel).remove()
        except Exception:
            pass

    def _home_tab_idx(self) -> int:
        if self._home_tab_name:
            for i, tab in enumerate(self._rigi_tabs):
                if tab.name.lower() == self._home_tab_name.lower():
                    return i
        return 0

    def _update_home_button(self) -> None:
        try:
            sidebar = self.query_one(Sidebar)
            on_home = sidebar._active_tab == self._home_tab_idx() and sidebar._active_path == []
            self.query_one(StatusBar).set_home_active(on_home)
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

            self.query_one(ContentArea).show_widget(self._rigi_widget_cache[cache_key])
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

    def navigate_to_tab(self, name: str) -> bool:
        for idx, tab in enumerate(self._rigi_tabs):
            if tab.name.lower() == name.lower():
                self.query_one(Sidebar).jump_to_tab_by_key(tab.key or "")
                self._navigate_to(idx, [])
                return True
        return False

    def invalidate_tab_cache(self, tab_name: str | None = None) -> None:
        content = self.query_one(ContentArea) if self.is_running else None

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

    @on(BottomPanel.CommandSubmitted)
    def on_command_submitted(self, event: BottomPanel.CommandSubmitted) -> None:
        self.run_worker(self._handle_command(event.text), name="rigi-cmd", exclusive=False)

    async def _handle_command(self, text: str) -> None:
        stripped = text.strip()
        _terminal_log.debug(f"Command received: {stripped}")

        if stripped.startswith("!") and not stripped[1:].lstrip().lower().startswith("sudo"):
            await self._run_shell(stripped[1:].strip())
            return

        if stripped.startswith("!"):
            stripped = stripped[1:].strip()

        cmd, parsed = parse_inline(stripped, self._cmd_registry)
        if "_error" in parsed:
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

        nav_tab = next((t for t in self._rigi_tabs if t.name.lower() == cmd.name.lower()), None)
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
            raw = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()
            display = (raw[:1200] if raw else "(no output)").replace("[", "\\[")
            _terminal_log.info(f"Shell command completed: {cmd}")
            try:
                self.query_one(BottomPanel).write_output(display)
            except Exception:
                self.notify(display, title=f"$ {cmd[:40]}", timeout=12)
        except Exception as exc:
            msg = str(exc).replace("[", "\\[")
            _terminal_log.error(f"Shell command failed: {cmd}", exc_info=True)
            try:
                self.query_one(BottomPanel).write_output(f"[red]{msg}[/red]")
            except Exception:
                self.notify(msg, severity="error", title=f"$ {cmd[:30]}")

    @on(_HamburgerButton.Clicked)
    def on_hamburger_clicked(self, event: _HamburgerButton.Clicked) -> None:
        event.stop()
        self._open_hamburger()

    def _open_hamburger(self) -> None:
        try:
            existing = self.query_one("#rigi-main-menu", MenuPanel)
            existing.remove()
            return
        except Exception:
            pass
        panel = MenuPanel(self._build_hamburger_sections(), id="rigi-main-menu")
        panel.styles.layer = "overlay"
        panel_w = 16
        x = max(0, self.size.width - panel_w - 1)
        panel.styles.offset = (x, 3)
        self.mount(panel)

    def _build_hamburger_sections(self) -> list[tuple[str, list[MenuItemData]]]:
        from rigi.themes import DARK, LIGHT, MONOKAI, NORD

        builtin_themes = [DARK, LIGHT, MONOKAI, NORD]
        theme_submenu = [
            MenuItemData(
                label=t.name.capitalize(),
                callback=lambda _t=t: self.set_theme(_t),
                checked=(t.name == self._theme.name),
            )
            for t in builtin_themes
        ]

        main_items: list[MenuItemData] = [
            MenuItemData("Theme", submenu=theme_submenu),
            MenuItemData("Settings", callback=self._open_settings),
            MenuItemData(
                "Help",
                callback=lambda: self.run_worker(self.action_show_help(), name="rigi-help"),
            ),
        ]

        by_section: dict[str, list[MenuItemData]] = {}
        for sec, lbl, cb in self._rigi_menu_items:
            by_section.setdefault(sec, []).append(MenuItemData(lbl, cb))

        sections: list[tuple[str, list[MenuItemData]]] = [("", main_items)]
        for sec_name, items in by_section.items():
            sections.append((sec_name, items))
        return sections

    @property
    def settings(self) -> SettingsManager:
        return self._settings_manager

    def _open_settings(self) -> None:
        builtin: list[SettingDef] = [
            SettingDef(
                category="Appearance",
                label="Theme",
                description="Color theme for the interface",
                value_fn=lambda: self._theme.name.capitalize(),
                action_fn=self._cycle_theme,
                action_label="Cycle",
            ),
            SettingDef(
                category="Terminal",
                label="Emulator",
                description="Detected terminal application",
                value_fn=lambda: _console.detect_terminal(),
            ),
            SettingDef(
                category="Terminal",
                label="True color",
                description="24-bit color support",
                value_fn=lambda: "yes" if _console.supports_true_color() else "no",
            ),
            SettingDef(
                category="Terminal",
                label="Hyperlinks",
                description="OSC 8 clickable link support",
                value_fn=lambda: "yes" if _console.supports_hyperlinks() else "no",
            ),
            SettingDef(
                category="Terminal",
                label="Multiplexer",
                description="Running inside tmux or screen",
                value_fn=lambda: (
                    "tmux" if _console.IS_TMUX else ("screen" if _console.IS_SCREEN else "none")
                ),
            ),
            SettingDef(
                category="Terminal",
                label="Unicode",
                description="UTF-8 output encoding",
                value_fn=lambda: "yes" if _console.supports_unicode() else "no",
            ),
            SettingDef(
                category="Appearance",
                label="Transparent",
                description="Enable transparent background with adjustable opacity",
                value_fn=lambda: str(self._transparent_percent),
                checkbox_fn=lambda: self._transparent_enabled,
                toggle_fn=self._toggle_transparency,
                write_fn=self._set_transparency_percent,
            ),
        ]
        try:
            existing = self.query_one("#rigi-settings-overlay", SettingsOverlay)
            existing.remove()
            return
        except Exception:
            pass
        overlay = SettingsOverlay(builtin + self._settings_manager.all_defs())
        overlay.styles.layer = "overlay"
        self.mount(overlay)

    def _terminal_input_focused(self) -> bool:
        try:
            return self.query_one("#terminal-input").has_focus
        except Exception:
            return False

    def action_nav_up(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(Sidebar).navigate(-1)

    def action_nav_down(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(Sidebar).navigate(1)

    def action_nav_right(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(Sidebar).navigate_right()

    def action_nav_left(self) -> None:
        if not self._terminal_input_focused():
            self.query_one(Sidebar).navigate_left()

    def action_focus_terminal(self) -> None:
        self.query_one(BottomPanel).focus_input()

    async def action_show_help(self) -> None:
        try:
            existing = self.query_one("#rigi-help-overlay", HelpOverlay)
            existing.remove()
            return
        except Exception:
            pass
        overlay = HelpOverlay(self._rigi_help_entries)
        overlay.styles.layer = "overlay"
        self.mount(overlay)

    def action_copy_focused(self) -> None:
        text = self._extract_focused_text()
        if text:
            if _platform_utils.copy_to_clipboard(text):
                self.notify("Copied to clipboard", timeout=2)
            else:
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

    async def action_quit(self) -> None:
        try:
            self.query_one(BottomPanel).save_history()
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
            self.query_one(StatusBar).add_item(item)
        return item

    def add_menu_item(
        self,
        label: str,
        callback: Callable[[], None],
        section: str = "Settings",
    ) -> None:
        self._rigi_menu_items.append((section, label, callback))

    def set_terminal_label(self, label: str) -> None:
        self._terminal_label = label
        try:
            self.query_one(BottomPanel).prompt_text = label
        except Exception:
            pass

    def open_url(self, url: str, *, new_tab: bool = True) -> None:
        if not _platform_utils.open_url(url):
            super().open_url(url, new_tab=new_tab)

    def open_path(self, path: str | Path) -> bool:
        return _platform_utils.open_path(path)

    def show_action_menu(
        self,
        items: list[ActionMenuItemData],
        title: str = "",
        x: int | None = None,
        y: int | None = None,
    ) -> None:
        panel_w = max((len(item.label) + 6 for item in items), default=22)
        panel_h = min(2 + len(items), 20)
        app_w, app_h = self.size.width, self.size.height
        if x is not None and y is not None:
            px = min(x, max(0, app_w - panel_w - 1))
            py = min(y, max(0, app_h - panel_h - 1))
        else:
            px = max(0, (app_w - panel_w) // 2)
            py = max(0, (app_h - panel_h) // 2)
        try:
            existing = self.query_one("#rigi-action-panel", ActionMenuPanel)
            existing.replace_items(items)
            existing.styles.offset = (px, py)
            existing.styles.width = panel_w
            existing.styles.height = panel_h
            existing.focus()
            return
        except Exception:
            pass
        panel = ActionMenuPanel(items, title=title, id="rigi-action-panel")
        panel.styles.layer = "overlay"
        panel.styles.offset = (px, py)
        panel.styles.width = panel_w
        panel.styles.height = panel_h
        self.mount(panel)

    def on_click(self, event: Any) -> None:
        if hasattr(event, "button") and event.button == 3:
            items = self._context_menu_items()
            if items:
                self.show_action_menu(items, x=event.x, y=event.y)
                return
        try:
            panel = self.query_one("#rigi-main-menu", MenuPanel)
            if panel not in event.chain:
                panel.remove()
        except Exception:
            pass
        try:
            overlay = self.query_one("#rigi-help-overlay", HelpOverlay)
            if overlay not in event.chain:
                overlay.remove()
        except Exception:
            pass
        try:
            overlay = self.query_one("#rigi-settings-overlay", SettingsOverlay)
            if overlay not in event.chain:
                overlay.remove()
        except Exception:
            pass
        try:
            panel = self.query_one("#rigi-action-panel", ActionMenuPanel)
            if panel not in event.chain:
                panel.remove()
        except Exception:
            pass

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            for selector, cls in (
                ("#rigi-action-panel", ActionMenuPanel),
                ("#rigi-main-menu", MenuPanel),
                ("#rigi-settings-overlay", SettingsOverlay),
                ("#rigi-help-overlay", HelpOverlay),
            ):
                try:
                    widget = self.query_one(selector, cls)
                    widget.remove()
                    event.stop()
                    return
                except Exception:
                    pass

    def _context_menu_items(self) -> list[ActionMenuItemData]:
        return []

    def set_context_menu(self, items: list[ActionMenuItemData]) -> None:
        self._context_menu_items = lambda: items

    def notify_desktop(self, title: str, body: str = "", urgency: str = "normal") -> bool:
        return _platform_utils.notify_desktop(title, body, urgency)

    def schedule_task(
        self,
        coro: Any,
        *,
        name: str = "rigi-task",
        on_done: Callable[[Any], None] | None = None,
    ) -> asyncio.Task[Any]:
        async def _wrapped() -> Any:
            result = await (coro if asyncio.iscoroutine(coro) else coro())
            if on_done is not None:
                on_done(result)
            return result

        return asyncio.create_task(_wrapped(), name=name)

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
        self, fn: Callable[[App], Awaitable[None] | None]
    ) -> Callable[[App], Awaitable[None] | None]:
        self._rigi_startup_hooks.append(fn)
        return fn

    @property
    def cmd_registry(self) -> CommandRegistry:
        return self._cmd_registry

    @classmethod
    def run_cli(cls, app_instance: App) -> None:
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
