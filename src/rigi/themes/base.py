"""Theme data class — color palette for a Rigi application."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Theme:
    """Color theme for a App.

    All color values are CSS color strings (hex, named, rgb(), etc.).
    Call ``to_css()`` to get the complete override stylesheet.
    """

    name: str

    # ── backgrounds ────────────────────────────────────────────────────────
    bg_color: str = "#000000"
    fg_color: str = "#ffffff"

    # ── borders / separators ───────────────────────────────────────────────
    border: str = "#30363d"
    border_dim: str = "#21262d"

    # ── text colors ────────────────────────────────────────────────────────
    text: str = "#c9d1d9"
    text_dim: str = "#6e7681"
    text_highlight: str = "#58a6ff"
    text_highlight2: str = "#79c0ff"

    # ── widget-specific accents ────────────────────────────────────────────
    terminal_color: str = "#3fb950"
    key_color: str = "#e3b341"
    desc_color: str = "#8b949e"

    # ── popup / overlay backgrounds ────────────────────────────────────────
    popup_bg: str = "#0d1117"
    completion_bg: str = "#1c2128"

    def to_css(self) -> str:
        return f"""/* rigi-theme: {self.name} */
App, Screen {{
    background: {self.bg_color};
    color: {self.fg_color};
}}
BorderFrame {{
    border: round {self.border};
    background: {self.bg_color};
    color: {self.fg_color};
}}
StatusBar {{
    border-bottom: solid {self.border_dim};
    background: {self.bg_color};
}}
_MainNav {{
    background: {self.bg_color};
}}
_MainNavItem {{
    color: {self.text_dim};
    background: {self.bg_color};
}}
_MainNavItem:hover {{
    color: {self.text};
}}
_MainNavItem.--active {{
    color: {self.text_highlight};
    border-left: thick {self.text_highlight};
}}
_SubNav {{
    background: {self.bg_color};
    border-right: solid {self.border_dim};
}}
_SubNavItem {{
    color: {self.text_dim};
    background: {self.bg_color};
}}
_SubNavItem:hover {{
    color: {self.text};
}}
_SubNavItem.--active {{
    color: {self.text_highlight2};
}}
ShortcutsBar {{
    border-top: solid {self.border_dim};
    background: {self.bg_color};
}}
ShortcutsBar Label {{
    color: {self.text_dim};
}}
TerminalBar {{
    background: {self.bg_color};
}}
TerminalBar Label {{
    color: {self.terminal_color};
}}
TerminalBar Input {{
    color: {self.text};
}}
Card {{
    border: round {self.border_dim};
    background: {self.bg_color};
}}
CompletionList {{
    border: solid {self.border};
    background: {self.completion_bg};
}}
HelpOverlay {{
    background: transparent;
}}
HelpOverlay > #help-container {{
    border: round {self.border};
    background: {self.popup_bg};
}}
ActionMenuScreen {{
    background: transparent;
}}
SettingsOverlay {{
    background: transparent;
}}
HamburgerPanel {{
    border: round {self.border};
    background: {self.popup_bg};
}}
PaletteScreen > #palette-container {{
    border: round {self.border};
    background: {self.popup_bg};
}}
#help-title {{
    color: {self.text_highlight};
}}
.help-category {{
    color: {self.border};
}}
.help-key {{
    color: {self.key_color};
}}
.help-desc {{
    color: {self.desc_color};
}}
#help-dismiss {{
    color: {self.text_dim};
}}
_Body {{
    background: {self.bg_color};
}}
Sidebar {{
    background: {self.bg_color};
}}
ContentArea {{
    background: {self.bg_color};
}}
BottomPanel {{
    background: {self.bg_color};
}}
#content-main {{
    background: {self.bg_color};
}}
_VerticalResizeHandle {{
    background: {self.bg_color};
}}
_ContentResizeHandle {{
    background: {self.bg_color};
}}
"""
