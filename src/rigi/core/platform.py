from __future__ import annotations

import base64
import os
import platform as _platform
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path

IS_WINDOWS: bool = sys.platform == "win32"
IS_MACOS: bool = sys.platform == "darwin"
IS_LINUX: bool = sys.platform.startswith("linux")
IS_WAYLAND: bool = IS_LINUX and bool(os.environ.get("WAYLAND_DISPLAY"))
IS_WSL: bool = IS_LINUX and "microsoft" in _platform.release().lower()
IS_SSH: bool = bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))
IS_ISH: bool = IS_LINUX and _platform.release().lower().startswith("ish")
IS_TMUX: bool = bool(os.environ.get("TMUX"))
IS_SCREEN: bool = bool(os.environ.get("STY"))

PLATFORM_NAME: str = _platform.system()
PLATFORM_VERSION: str = _platform.release()
ARCH: str = _platform.machine()


def _detect_terminal() -> str:
    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    if os.environ.get("ITERM_SESSION_ID") or os.environ.get("TERM_PROGRAM") == "iTerm.app":
        return "iterm2"
    if os.environ.get("WT_SESSION"):
        return "windows-terminal"
    if os.environ.get("WEZTERM_EXECUTABLE") or os.environ.get("TERM_PROGRAM") == "WezTerm":
        return "wezterm"
    if os.environ.get("GHOSTTY_RESOURCES_DIR") or os.environ.get("TERM") == "xterm-ghostty":
        return "ghostty"
    if os.environ.get("ALACRITTY_SOCKET") or os.environ.get("ALACRITTY_WINDOW_ID"):
        return "alacritty"
    if os.environ.get("KONSOLE_VERSION") or os.environ.get("KONSOLE_DBUS_SESSION"):
        return "konsole"
    if os.environ.get("TERM_PROGRAM") == "Apple_Terminal":
        return "apple-terminal"
    if os.environ.get("TERM_PROGRAM") == "Hyper":
        return "hyper"
    if os.environ.get("TERM_PROGRAM") == "vscode" or os.environ.get("VSCODE_INJECTION"):
        return "vscode"
    if os.environ.get("TERM_PROGRAM") == "tmux" or IS_TMUX:
        return "tmux"
    if IS_SCREEN:
        return "screen"
    if os.environ.get("TERM_PROGRAM") == "MacTerm":
        return "macterm"
    if os.environ.get("CONEMUDIR") or os.environ.get("CMDER_ROOT"):
        return "conemu"
    if IS_ISH:
        return "ish"
    if IS_WINDOWS:
        return "cmd"
    term = os.environ.get("TERM", "")
    if "xterm" in term:
        return "xterm"
    return "unknown"


TERMINAL: str = _detect_terminal()


def _tmux_version() -> tuple[int, int]:
    try:
        out = subprocess.run(
            ["tmux", "-V"], capture_output=True, text=True, timeout=2
        ).stdout.strip()
        parts = out.split()
        if len(parts) >= 2:
            nums = parts[1].split(".")
            return int(nums[0]), int(nums[1]) if len(nums) > 1 else 0
    except Exception:
        pass
    return (0, 0)


def _has_true_color() -> bool:
    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return True
    if TERMINAL in (
        "kitty",
        "iterm2",
        "windows-terminal",
        "alacritty",
        "konsole",
        "wezterm",
        "ghostty",
        "vscode",
    ):
        return True
    term = os.environ.get("TERM", "")
    return "256color" in term or "truecolor" in term


def _has_osc_clipboard() -> bool:
    if TERMINAL in ("kitty", "alacritty", "iterm2", "wezterm", "ghostty", "windows-terminal"):
        return True
    if IS_TMUX and _tmux_version() >= (3, 2):
        return True
    term = os.environ.get("TERM", "")
    return "xterm" in term


def _has_hyperlinks() -> bool:
    return TERMINAL in (
        "kitty",
        "iterm2",
        "alacritty",
        "konsole",
        "wezterm",
        "ghostty",
        "vscode",
        "windows-terminal",
        "xterm",
    )


def _has_notifications() -> bool:
    if TERMINAL in ("iterm2", "windows-terminal", "wezterm", "kitty", "ghostty"):
        return True
    if IS_MACOS:
        return True
    if IS_WINDOWS:
        return True
    return bool(shutil.which("notify-send"))


def _has_progress() -> bool:
    return TERMINAL in ("windows-terminal", "iterm2", "wezterm")


def _has_window_title() -> bool:
    return TERMINAL not in ("ish", "cmd", "apple-terminal")


def _has_kitty_graphics() -> bool:
    return TERMINAL == "kitty"


def _has_iterm2_graphics() -> bool:
    return TERMINAL in ("iterm2", "wezterm")


def _has_sixel() -> bool:
    if TERMINAL in ("iterm2", "macterm"):
        return True
    term = os.environ.get("TERM", "")
    return "mlterm" in term


@dataclass
class TerminalCaps:
    true_color: bool
    osc_clipboard: bool
    hyperlinks: bool
    notifications: bool
    progress: bool
    window_title: bool
    kitty_graphics: bool
    iterm2_graphics: bool
    sixel: bool


CAPS: TerminalCaps = TerminalCaps(
    true_color=_has_true_color(),
    osc_clipboard=_has_osc_clipboard(),
    hyperlinks=_has_hyperlinks(),
    notifications=_has_notifications(),
    progress=_has_progress(),
    window_title=_has_window_title(),
    kitty_graphics=_has_kitty_graphics(),
    iterm2_graphics=_has_iterm2_graphics(),
    sixel=_has_sixel(),
)


def tmux_passthrough(seq: str) -> str:
    if not IS_TMUX:
        return seq
    escaped = seq.replace("\x1b", "\x1b\x1b")
    return f"\x1bPtmux;{escaped}\x1b\\"


def _write(seq: str) -> None:
    if IS_TMUX:
        seq = tmux_passthrough(seq)
    try:
        sys.stdout.write(seq)
        sys.stdout.flush()
    except Exception:
        pass


def set_window_title(title: str) -> None:
    if CAPS.window_title:
        _write(f"\x1b]0;{title}\x07")


def bell() -> None:
    try:
        sys.stdout.write("\x07")
        sys.stdout.flush()
    except Exception:
        pass


def hyperlink(text: str, url: str) -> str:
    if not CAPS.hyperlinks:
        return text
    return f"\x1b]8;;{url}\x07{text}\x1b]8;;\x07"


def set_progress(value: int | None) -> None:
    if not CAPS.progress:
        return
    if value is None:
        if TERMINAL == "windows-terminal":
            _write("\x1b]9;4;0;0\x07")
        elif TERMINAL in ("iterm2", "wezterm"):
            _write("\x1b]1337;SetProgress=\x07")
        return
    v = max(0, min(100, value))
    if TERMINAL == "windows-terminal":
        _write(f"\x1b]9;4;1;{v}\x07")
    elif TERMINAL in ("iterm2", "wezterm"):
        _write(f"\x1b]1337;SetProgress={v}\x07")


def osc_clipboard_copy(text: str) -> bool:
    if not CAPS.osc_clipboard:
        return False
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    seq = f"\x1b]52;c;{encoded}\x07"
    if IS_TMUX:
        seq = f"\x1bPtmux;\x1b{seq}\x1b\\"
    try:
        sys.stdout.write(seq)
        sys.stdout.flush()
        return True
    except Exception:
        return False


def notify_terminal(title: str, body: str = "") -> bool:
    try:
        if TERMINAL == "iterm2":
            _write(f"\x1b]9;{body or title}\x07")
            return True
        if TERMINAL == "windows-terminal":
            msg = f"{title}: {body}" if body else title
            _write(f"\x1b]9;{msg}\x07")
            return True
        if TERMINAL in ("kitty", "wezterm", "ghostty"):
            _write(f"\x1b]777;notify;{title};{body}\x07")
            return True
    except Exception:
        pass
    return False


def open_url(url: str) -> bool:
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_path(path: str | Path) -> bool:
    try:
        p = str(path)
        if IS_WINDOWS:
            os.startfile(p)  # type: ignore[attr-defined]
        elif IS_MACOS:
            subprocess.run(["open", p], check=True, capture_output=True)
        else:
            xdg = shutil.which("xdg-open")
            if xdg:
                subprocess.run([xdg, p], check=True, capture_output=True)
            else:
                return False
        return True
    except Exception:
        return False


def copy_to_clipboard(text: str) -> bool:
    if osc_clipboard_copy(text):
        return True
    encoded = text.encode("utf-8")
    try:
        if IS_WINDOWS:
            subprocess.run(["clip"], input=encoded, check=True, capture_output=True)
            return True
        if IS_MACOS:
            subprocess.run(["pbcopy"], input=encoded, check=True, capture_output=True)
            return True
        if IS_WAYLAND and shutil.which("wl-copy"):
            subprocess.run(["wl-copy"], input=encoded, check=True, capture_output=True)
            return True
        if shutil.which("xclip"):
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=encoded,
                check=True,
                capture_output=True,
            )
            return True
        if shutil.which("xsel"):
            subprocess.run(
                ["xsel", "--clipboard", "--input"],
                input=encoded,
                check=True,
                capture_output=True,
            )
            return True
        try:
            import pyperclip  # type: ignore[import-untyped]

            pyperclip.copy(text)
            return True
        except ImportError:
            pass
    except Exception:
        pass
    return False


def notify_desktop(title: str, body: str = "", urgency: str = "normal") -> bool:
    if notify_terminal(title, body):
        return True
    title = title.replace('"', "'")
    body = body.replace('"', "'")
    try:
        if IS_WINDOWS:
            script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$n = New-Object System.Windows.Forms.NotifyIcon; "
                "$n.Icon = [System.Drawing.SystemIcons]::Information; "
                "$n.Visible = $true; "
                f'$n.ShowBalloonTip(3000, "{title}", "{body}", '
                "[System.Windows.Forms.ToolTipIcon]::Info)"
            )
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        if IS_MACOS:
            subprocess.Popen(
                ["osascript", "-e", f'display notification "{body}" with title "{title}"'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        if shutil.which("notify-send"):
            subprocess.Popen(
                ["notify-send", f"--urgency={urgency}", title, body],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
    except Exception:
        pass
    return False


def config_dir(app_name: str) -> Path:
    if IS_WINDOWS:
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    elif IS_MACOS:
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    d = base / app_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_dir(app_name: str) -> Path:
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    elif IS_MACOS:
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    d = base / app_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_dir(app_name: str) -> Path:
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    elif IS_MACOS:
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    d = base / app_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def app_dirs(app_name: str) -> dict[str, Path]:
    return {
        "config": config_dir(app_name),
        "data": data_dir(app_name),
        "cache": cache_dir(app_name),
    }


def terminal_size() -> tuple[int, int]:
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        return 80, 24


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
