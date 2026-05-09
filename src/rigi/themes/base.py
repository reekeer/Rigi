"""RigiTheme data class — color palette for a Rigi application."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RigiTheme:
    """Color theme for a RigiApp.

    All color values are CSS color strings (hex, named, rgb(), etc.).
    Call ``to_css()`` to get the complete override stylesheet.
    """

    name: str

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
RigiBorderFrame {{
    border: round {self.border};
}}
RigiStatusBar {{
    border-bottom: solid {self.border_dim};
}}
_RigiMainNav {{
    border-right: solid {self.border_dim};
}}
_MainNavItem {{
    color: {self.text_dim};
}}
_MainNavItem:hover {{
    color: {self.text};
}}
_MainNavItem.--active {{
    color: {self.text_highlight};
    border-left: thick {self.text_highlight};
}}
_RigiSubNav {{
    border-right: solid {self.border_dim};
}}
_SubNavItem {{
    color: {self.text_dim};
}}
_SubNavItem:hover {{
    color: {self.text};
}}
_SubNavItem.--active {{
    color: {self.text_highlight2};
}}
RigiShortcutsBar {{
    border-top: solid {self.border_dim};
}}
RigiShortcutsBar Label {{
    color: {self.text_dim};
}}
RigiTerminalBar Label {{
    color: {self.terminal_color};
}}
RigiTerminalBar Input {{
    color: {self.text};
}}
RigiCard {{
    border: round {self.border_dim};
}}
RigiCompletionList {{
    border: solid {self.border};
    background: {self.completion_bg};
}}
RigiHelpScreen > #help-container {{
    border: round {self.border};
    background: {self.popup_bg};
}}
RigiHamburgerPanel {{
    border: round {self.border};
    background: {self.popup_bg};
}}
RigiPaletteScreen > #palette-container {{
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
"""
