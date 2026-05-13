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
    RigiActionMenuItem,
    RigiActionMenuItemData,
    RigiActionMenuPanel,
)
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
from rigi.widgets.settings_screen import RigiSettingDef, RigiSettingsScreen
from rigi.widgets.sidebar import RigiSidebar
from rigi.widgets.statusbar import RigiStatusBar, RigiStatusItem
from rigi.widgets.terminal_bar import RigiTerminalBar
from rigi.widgets.vertical_tabs import RigiVerticalTabs

__all__ = [
    # Textual primitives
    "Widget",
    "ComposeResult",
    "Screen",
    "ModalScreen",
    "reactive",
    # Rigi widgets
    "RigiStatusBar",
    "RigiStatusItem",
    "RigiSidebar",
    "RigiTerminalBar",
    "RigiBottomPanel",
    "RigiBorderFrame",
    "RigiContentArea",
    "RigiMenuItem",
    "RigiMenuPanel",
    "RigiHamburgerPanel",
    "RigiMenuItemData",
    "RigiActionMenuItem",
    "RigiActionMenuPanel",
    "RigiActionMenuItemData",
    "RigiVerticalTabs",
    "RigiSettingsScreen",
    "RigiSettingDef",
    "RigiImage",
    "TerminalImageProtocol",
    "detect_image_protocol",
    "RigiMouseMixin",
    "RigiClickable",
    "RigiDraggable",
    "RigiShortcutsBar",
    "extract_help_annotation",
    "RigiGauge",
    "RigiSparkline",
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
