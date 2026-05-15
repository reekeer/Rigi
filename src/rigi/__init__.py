from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget

import rigi.core.console as console
import rigi.core.platform as platform
from rigi.commands.command import Command
from rigi.commands.parser import build_cli_parser, parse_inline
from rigi.commands.registry import CommandRegistry
from rigi.core.app import App
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
from rigi.core.settings_manager import Setting, SettingsManager, SettingsPage
from rigi.core.types import CommandArg, HelpEntry, StatusItem, SubtabDef, TabDef
from rigi.layout.pane import Card, HPane, Pane, ScrollPane, Split, VPane
from rigi.screens.hamburger import HamburgerScreen
from rigi.screens.help import HelpScreen
from rigi.themes import DARK as ThemeDark
from rigi.themes import LIGHT as ThemeLight
from rigi.themes import MONOKAI as ThemeMonokai
from rigi.themes import NORD as ThemeNord
from rigi.themes import Theme
from rigi.widgets.action_menu import ActionMenuItemData
from rigi.widgets.border_frame import BorderFrame
from rigi.widgets.bottom_panel import BottomPanel
from rigi.widgets.checkbox import Checkbox
from rigi.widgets.content_area import ContentArea
from rigi.widgets.gauge import Gauge, Sparkline
from rigi.widgets.hamburger_menu import (
    HamburgerPanel,
    MenuItem,
    MenuItemData,
    MenuPanel,
)
from rigi.widgets.help_overlay import HelpOverlay
from rigi.widgets.help_panel import ShortcutsBar, extract_help_annotation
from rigi.widgets.image import Image, TerminalImageProtocol, detect_image_protocol
from rigi.widgets.mouse import Clickable, Draggable, MouseMixin
from rigi.widgets.notifications import (
    NotificationRack as NotificationRack,
)
from rigi.widgets.notifications import (
    NotificationWidget as NotificationWidget,
)
from rigi.widgets.settings_overlay import SettingsOverlay
from rigi.widgets.settings_screen import SettingDef, SettingsScreen
from rigi.widgets.sidebar import Sidebar
from rigi.widgets.statusbar import StatusBar, StatusBarItem
from rigi.widgets.tab_group import TabGroup
from rigi.widgets.terminal_bar import TerminalBar

__version__ = "1.3.2"
__all__ = [
    # Textual primitives
    "Widget",
    "ComposeResult",
    "Screen",
    "ModalScreen",
    "reactive",
    # Core app
    "App",
    "Theme",
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
    "Pane",
    "HPane",
    "VPane",
    "ScrollPane",
    "Card",
    "Split",
    # Widgets
    "StatusBar",
    "StatusItem",
    "Sidebar",
    "TerminalBar",
    "BottomPanel",
    "Checkbox",
    "ContentArea",
    "BorderFrame",
    "HamburgerScreen",
    "MenuItem",
    "MenuPanel",
    "HamburgerPanel",
    "MenuItemData",
    "SettingsScreen",
    "SettingsOverlay",
    "SettingDef",
    "Setting",
    "SettingsPage",
    "SettingsManager",
    "Image",
    "TerminalImageProtocol",
    "detect_image_protocol",
    "MouseMixin",
    "Clickable",
    "Draggable",
    "HelpScreen",
    "HelpOverlay",
    "ShortcutsBar",
    "extract_help_annotation",
    "Gauge",
    "Sparkline",
    "NotificationRack",
    "NotificationWidget",
    "TabGroup",
    "ActionMenuItemData",
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
