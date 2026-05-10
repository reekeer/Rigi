from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget

import rigi.core.console as console
import rigi.core.platform as platform
from rigi.commands.command import Command
from rigi.commands.parser import build_cli_parser, parse_inline
from rigi.commands.registry import CommandRegistry
from rigi.core.app import RigiApp
from rigi.core.platform import (
    CAPS,
    IS_ISH,
    IS_LINUX,
    IS_MACOS,
    IS_SCREEN,
    IS_SSH,
    IS_TMUX,
    IS_WAYLAND,
    IS_WINDOWS,
    IS_WSL,
    PLATFORM_NAME,
    TERMINAL,
    TerminalCaps,
    app_dirs,
    bell,
    cache_dir,
    config_dir,
    copy_to_clipboard,
    data_dir,
    hyperlink,
    notify_desktop,
    notify_terminal,
    open_path,
    open_url,
    osc_clipboard_copy,
    set_progress,
    set_window_title,
    terminal_size,
    tmux_passthrough,
)
from rigi.core.types import CommandArg, HelpEntry, StatusItem, SubtabDef, TabDef
from rigi.layout.pane import RigiCard, RigiHPane, RigiPane, RigiScrollPane, RigiSplit, RigiVPane
from rigi.screens.hamburger import RigiHamburgerScreen
from rigi.screens.help import RigiHelpScreen
from rigi.themes import DARK as ThemeDark
from rigi.themes import LIGHT as ThemeLight
from rigi.themes import MONOKAI as ThemeMonokai
from rigi.themes import NORD as ThemeNord
from rigi.themes import RigiTheme
from rigi.widgets.border_frame import RigiBorderFrame
from rigi.widgets.bottom_panel import RigiBottomPanel
from rigi.widgets.content_area import RigiContentArea
from rigi.widgets.gauge import RigiGauge, RigiSparkline
from rigi.widgets.hamburger_menu import (
    RigiHamburgerPanel,
    RigiMenuItem,
    RigiMenuItemData,
    RigiMenuPanel,
)
from rigi.widgets.help_panel import RigiShortcutsBar, extract_help_annotation
from rigi.widgets.image import RigiImage, TerminalImageProtocol, detect_image_protocol
from rigi.widgets.mouse import RigiClickable, RigiDraggable, RigiMouseMixin
from rigi.widgets.notifications import (
    RigiNotificationRack as RigiNotificationRack,
)
from rigi.widgets.notifications import (
    RigiNotificationWidget as RigiNotificationWidget,
)
from rigi.widgets.settings_screen import RigiSettingDef, RigiSettingsScreen
from rigi.widgets.sidebar import RigiSidebar
from rigi.widgets.statusbar import RigiStatusBar, RigiStatusItem
from rigi.widgets.terminal_bar import RigiTerminalBar

__version__ = "1.0.0"
__all__ = [
    # Textual primitives
    "Widget",
    "ComposeResult",
    "Screen",
    "ModalScreen",
    "reactive",
    # Core app
    "RigiApp",
    "RigiTheme",
    "ThemeDark",
    "ThemeLight",
    "ThemeMonokai",
    "ThemeNord",
    # Commands
    "Command",
    "CommandArg",
    "CommandRegistry",
    "build_cli_parser",
    "parse_inline",
    # Types
    "StatusItem",
    "TabDef",
    "SubtabDef",
    "HelpEntry",
    # Layout
    "RigiPane",
    "RigiHPane",
    "RigiVPane",
    "RigiScrollPane",
    "RigiCard",
    "RigiSplit",
    # Widgets
    "RigiStatusBar",
    "RigiStatusItem",
    "RigiSidebar",
    "RigiTerminalBar",
    "RigiBottomPanel",
    "RigiContentArea",
    "RigiBorderFrame",
    "RigiHamburgerScreen",
    "RigiMenuItem",
    "RigiMenuPanel",
    "RigiHamburgerPanel",
    "RigiMenuItemData",
    "RigiSettingsScreen",
    "RigiSettingDef",
    "RigiImage",
    "TerminalImageProtocol",
    "detect_image_protocol",
    "RigiMouseMixin",
    "RigiClickable",
    "RigiDraggable",
    "RigiHelpScreen",
    "RigiShortcutsBar",
    "extract_help_annotation",
    "RigiGauge",
    "RigiSparkline",
    "RigiNotificationRack",
    "RigiNotificationWidget",
    # Platform utilities
    "platform",
    "console",
    "IS_WINDOWS",
    "IS_MACOS",
    "IS_LINUX",
    "IS_WAYLAND",
    "IS_WSL",
    "IS_SSH",
    "IS_ISH",
    "IS_TMUX",
    "IS_SCREEN",
    "PLATFORM_NAME",
    "TERMINAL",
    "CAPS",
    "TerminalCaps",
    "open_url",
    "open_path",
    "copy_to_clipboard",
    "osc_clipboard_copy",
    "notify_desktop",
    "notify_terminal",
    "bell",
    "hyperlink",
    "set_window_title",
    "set_progress",
    "tmux_passthrough",
    "config_dir",
    "data_dir",
    "cache_dir",
    "app_dirs",
    "terminal_size",
]
