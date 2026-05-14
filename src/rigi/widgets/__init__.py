# Re-export common Textual primitives and widgets — import from rigi, not textual
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Collapsible,
    ContentSwitcher,
    DataTable,
    Digits,
    DirectoryTree,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    Log,
    Markdown,
    OptionList,
    ProgressBar,
    RadioButton,
    RadioSet,
    RichLog,
    Rule,
    Select,
    SelectionList,
    Static,
    Switch,
    Tab,
    TabbedContent,
    TabPane,
    Tabs,
    TextArea,
    Tree,
)

from rigi.widgets.action_menu import (
    ActionMenuItem,
    ActionMenuItemData,
    ActionMenuPanel,
)
from rigi.widgets.border_frame import BorderFrame
from rigi.widgets.bottom_panel import BottomPanel
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
from rigi.widgets.settings_overlay import SettingsOverlay
from rigi.widgets.settings_screen import SettingDef, SettingsScreen
from rigi.widgets.sidebar import Sidebar
from rigi.widgets.statusbar import StatusBar, StatusItem
from rigi.widgets.tab_group import TabGroup
from rigi.widgets.terminal_bar import TerminalBar

__all__ = [
    # Textual primitives
    "Widget",
    "ComposeResult",
    "Screen",
    "ModalScreen",
    "reactive",
    # Rigi widgets
    "StatusBar",
    "StatusItem",
    "Sidebar",
    "TerminalBar",
    "BottomPanel",
    "BorderFrame",
    "ContentArea",
    "MenuItem",
    "MenuPanel",
    "HamburgerPanel",
    "MenuItemData",
    "ActionMenuItem",
    "ActionMenuPanel",
    "ActionMenuItemData",
    "TabGroup",
    "SettingsScreen",
    "SettingsOverlay",
    "SettingDef",
    "HelpOverlay",
    "Image",
    "TerminalImageProtocol",
    "detect_image_protocol",
    "MouseMixin",
    "Clickable",
    "Draggable",
    "ShortcutsBar",
    "extract_help_annotation",
    "Gauge",
    "Sparkline",
    # Textual widgets
    "Label",
    "Static",
    "Button",
    "Input",
    "DataTable",
    "Markdown",
    "ProgressBar",
    "Switch",
    "Select",
    "TextArea",
    "ListView",
    "ListItem",
    "Tree",
    "Log",
    "RichLog",
    "TabbedContent",
    "TabPane",
    "Tabs",
    "Tab",
    "RadioButton",
    "RadioSet",
    "ContentSwitcher",
    "DirectoryTree",
    "Digits",
    "LoadingIndicator",
    "Collapsible",
    "Rule",
    "OptionList",
    "SelectionList",
]
