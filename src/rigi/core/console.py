"""Terminal / console detection and capability utilities.

Detect which terminal is running, what it supports (true color, hyperlinks,
mouse, unicode, sixel, kitty graphics), and emit escape sequences for
advanced features.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from typing import Literal

# ── Multiplexer detection ──────────────────────────────────────────────────────

IS_TMUX: bool = bool(os.environ.get("TMUX"))
IS_SCREEN: bool = os.environ.get("TERM", "") == "screen"
IS_MULTIPLEXED: bool = IS_TMUX or IS_SCREEN


# ── Terminal identity ──────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def detect_terminal() -> str:
    """Return a lowercase terminal identifier string.

    Possible values: ``kitty``, ``iterm2``, ``wezterm``, ``windows-terminal``,
    ``vte``, ``alacritty``, ``foot``, ``tmux``, ``screen``, ``xterm``,
    ``konsole``, ``gnome-terminal``, ``unknown``.
    """
    env = os.environ

    # Kitty sets TERM=xterm-kitty or KITTY_WINDOW_ID
    if env.get("KITTY_WINDOW_ID") or env.get("TERM") == "xterm-kitty":
        return "kitty"

    # WezTerm
    if env.get("TERM_PROGRAM") == "WezTerm" or env.get("WEZTERM_EXECUTABLE"):
        return "wezterm"

    # iTerm2 (macOS)
    if env.get("TERM_PROGRAM") == "iTerm.app" or env.get("ITERM_SESSION_ID"):
        return "iterm2"

    # Windows Terminal
    if env.get("WT_SESSION") or env.get("WT_PROFILE_ID"):
        return "windows-terminal"

    # Alacritty
    if env.get("ALACRITTY_WINDOW_ID") or env.get("TERM") == "alacritty":
        return "alacritty"

    # Foot (Wayland)
    if env.get("TERM") == "foot" or env.get("TERM_PROGRAM") == "foot":
        return "foot"

    # Konsole
    if env.get("KONSOLE_VERSION") or env.get("TERM_PROGRAM") == "konsole":
        return "konsole"

    # GNOME Terminal / VTE
    if env.get("VTE_VERSION"):
        return "gnome-terminal"

    # tmux / screen (multiplexers — report as such)
    if IS_TMUX:
        return "tmux"
    if IS_SCREEN:
        return "screen"

    # Xterm-compatible fallback
    term = env.get("TERM", "")
    if term.startswith("xterm"):
        return "xterm"

    return "unknown"


# ── Color support ──────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def supports_true_color() -> bool:
    """Return True if the terminal supports 24-bit (true) color."""
    env = os.environ
    colorterm = env.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return True
    term = detect_terminal()
    return term in (
        "kitty",
        "iterm2",
        "wezterm",
        "windows-terminal",
        "alacritty",
        "foot",
        "gnome-terminal",
        "konsole",
    )


@lru_cache(maxsize=1)
def supports_256_color() -> bool:
    """Return True if the terminal supports at least 256 colors."""
    if supports_true_color():
        return True
    term = os.environ.get("TERM", "")
    return "256color" in term or "256colour" in term


@lru_cache(maxsize=1)
def color_depth() -> Literal[1, 8, 256, 16777216]:
    """Return the approximate color depth (1, 8, 256, or 16777216)."""
    if supports_true_color():
        return 16777216
    if supports_256_color():
        return 256
    term = os.environ.get("TERM", "")
    if "color" in term or term in ("xterm", "vt100"):
        return 8
    return 1


# ── Feature support ────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def supports_hyperlinks() -> bool:
    """Return True if the terminal supports OSC 8 hyperlinks."""
    term = detect_terminal()
    return term in (
        "kitty",
        "iterm2",
        "wezterm",
        "windows-terminal",
        "foot",
        "gnome-terminal",
        "konsole",
        "alacritty",
        "xterm",
    )


@lru_cache(maxsize=1)
def supports_mouse() -> bool:
    """Return True if the terminal supports mouse tracking."""
    if IS_SCREEN:
        return False
    term = os.environ.get("TERM", "")
    if term in ("dumb", ""):
        return False
    return True


@lru_cache(maxsize=1)
def supports_unicode() -> bool:
    """Return True if stdout can handle unicode (UTF-8 locale or UTF-8 encoding)."""
    try:
        enc = (sys.stdout.encoding or "").lower()
        return "utf" in enc
    except Exception:
        pass
    lang = (
        os.environ.get("LANG", "") + os.environ.get("LC_ALL", "") + os.environ.get("LC_CTYPE", "")
    )
    return "utf" in lang.lower()


@lru_cache(maxsize=1)
def supports_kitty_graphics() -> bool:
    """Return True if the terminal supports the Kitty graphics protocol."""
    return detect_terminal() in ("kitty", "wezterm")


@lru_cache(maxsize=1)
def supports_sixel() -> bool:
    """Return True if the terminal likely supports sixel graphics."""
    return detect_terminal() in ("iterm2", "xterm")


# ── Escape sequence helpers ────────────────────────────────────────────────────


def hyperlink(url: str, text: str) -> str:
    """Return an OSC 8 hyperlink escape sequence (clickable link in terminal).

    Falls back to plain *text* if hyperlinks are not supported.
    """
    if not supports_hyperlinks():
        return text
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def set_title(title: str) -> str:
    """Return the escape sequence that sets the terminal tab/window title."""
    return f"\033]2;{title}\007"


def set_icon_name(name: str) -> str:
    """Return the escape sequence that sets the terminal icon name."""
    return f"\033]1;{name}\007"


def bell() -> str:
    """Return the terminal bell character."""
    return "\a"


def write_escape(seq: str) -> None:
    """Write *seq* directly to the terminal device, bypassing stdout buffering."""
    try:
        sys.stdout.write(seq)
        sys.stdout.flush()
    except Exception:
        try:
            with open("/dev/tty", "w") as tty:
                tty.write(seq)
        except Exception:
            pass


# ── Terminal info summary ──────────────────────────────────────────────────────


def info() -> dict[str, object]:
    """Return a dict summarising terminal capabilities."""
    return {
        "terminal": detect_terminal(),
        "true_color": supports_true_color(),
        "color_depth": color_depth(),
        "unicode": supports_unicode(),
        "hyperlinks": supports_hyperlinks(),
        "mouse": supports_mouse(),
        "kitty_graphics": supports_kitty_graphics(),
        "sixel": supports_sixel(),
        "tmux": IS_TMUX,
        "screen": IS_SCREEN,
        "multiplexed": IS_MULTIPLEXED,
        "columns": os.get_terminal_size().columns if sys.stdout.isatty() else 80,
        "lines": os.get_terminal_size().lines if sys.stdout.isatty() else 24,
    }
