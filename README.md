<h1 align="center">RIGI</h1>

<h4 align="center"><b>R</b>igi <b>I</b>sn't a <b>G</b>raphics <b>I</b>nterface - it's terminal.</h4>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensourceinitiative&logoColor=FFFFFF" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Textual-8.2.5%2B-8A2BE2?style=for-the-badge" alt="Textual">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey?style=for-the-badge&logo=linux&logoColor=FCC624" alt="Platform">
  <img src="https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge" alt="black">
  <img src="https://img.shields.io/badge/linting-ruff-orange?style=for-the-badge" alt="ruff">
  <img src="https://img.shields.io/badge/type%20checked-pyright-4B8BBE?style=for-the-badge" alt="pyright">
  <img src="https://img.shields.io/github/stars/reekeer/Rigi?style=for-the-badge&logo=github&logoColor=white" alt="Stars">
  <img src="https://img.shields.io/github/last-commit/reekeer/Rigi?style=for-the-badge&logo=github&logoColor=white" alt="Last Commit">
</p>

---

A high-level TUI framework built on top of [Textual](https://github.com/Textualize/textual). Rigi is an **internal library** - used across all CLI tools to maintain a consistent, polished terminal interface.

---

## 📦 Installation

```bash
pip install rigi-reekeer
```

---

## ✨ Overview

Rigi gives you a complete, opinionated TUI shell in a few lines of code:

- 🗂 **Sidebar navigation** - multi-level tab/subtab navigation with keyboard and mouse support
- 🖥 **Bottom panel** - resizable terminal with command history, tab completion, and a live log viewer
- 📊 **Status bar** - customizable status items, home button, hamburger menu
- 🎨 **Themes** - built-in Dark, Light, Monokai, Nord; fully customizable via `RigiTheme`
- ⌨️ **Command system** - register commands with arguments, aliases, fuzzy completion, and inline help
- 🔍 **Command palette** - `Ctrl+P` fuzzy-search overlay
- 🌍 **Cross-platform** - Linux (Arch, Debian, WSL), macOS, Windows 10/11, iSH; terminal detection for kitty, alacritty, iTerm2, WezTerm, Ghostty, Konsole, Windows Terminal, tmux, and more
- 🧩 **Widgets** - gauges, sparklines, image rendering (kitty/iTerm2/sixel), draggable/clickable mixins, settings screen

---

## 🚀 Quick start

```python
import rigi

app = rigi.RigiApp(
    name="mytool",
    version="1.0.0",
    description="My internal tool",
)

app.add_tab(rigi.TabDef(name="Dashboard", icon="󰕮"))
app.run()
```

See the [`examples/`](examples/) directory for complete working apps.

---

## 🖥 Platform support

| OS | Supported | Notes |
|---|:---:|---|
| Linux (Arch) | ✓ | full support |
| Linux (Debian / Ubuntu) | ✓ | full support |
| Linux (WSL 1/2) | ✓ | clipboard via OSC 52 |
| macOS | ✓ | AppleScript notifications |
| Windows 10/11 | ✓ | Windows Terminal recommended |
| iSH (iOS) | ✓ | limited - no true color |

## 🔌 Terminal support

| Terminal | True color | OSC clipboard | Hyperlinks | Graphics | Notifications | Progress |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| kitty | ✓ | ✓ | ✓ | kitty | OSC 777 | - |
| Alacritty | ✓ | ✓ | ✓ | - | - | - |
| iTerm2 | ✓ | ✓ | ✓ | iTerm2 | OSC 9 | ✓ |
| WezTerm | ✓ | ✓ | ✓ | iTerm2 | OSC 777 | ✓ |
| Ghostty | ✓ | ✓ | ✓ | - | OSC 777 | - |
| Konsole | ✓ | ✓ | ✓ | - | - | - |
| Windows Terminal | ✓ | ✓ | ✓ | - | OSC 9 | ✓ |
| tmux | passthrough | ✓ (>=3.2) | passthrough | passthrough | passthrough | - |
| Apple Terminal | ✓ | - | - | - | AppleScript | - |
| iSH | - | - | - | - | - | - |
| VSCode | ✓ | - | ✓ | - | - | - |

---

## 🗂 Structure

```
Rigi/
├── src/
│   └── rigi/
│       ├── __init__.py              ← public API
│       ├── commands/
│       │   ├── command.py           ← Command dataclass
│       │   ├── registry.py          ← CommandRegistry (fuzzy completions)
│       │   └── parser.py            ← CLI arg parser + inline command parser
│       ├── core/
│       │   ├── app.py               ← RigiApp (main application class)
│       │   ├── platform.py          ← OS + terminal detection, cross-platform utils
│       │   ├── console.py           ← terminal capability queries
│       │   ├── log_store.py         ← global log interceptor (logging + loguru)
│       │   ├── dev_commands.py      ← built-in dev commands
│       │   └── types.py             ← TabDef, SubtabDef, StatusItem, HelpEntry, …
│       ├── css/
│       │   └── default.tcss         ← default Textual stylesheet
│       ├── layout/
│       │   └── pane.py              ← RigiPane, RigiCard, RigiSplit, …
│       ├── themes/
│       │   ├── base.py              ← RigiTheme dataclass
│       │   ├── dark.py              ← DARK
│       │   ├── light.py             ← LIGHT
│       │   ├── monokai.py           ← MONOKAI
│       │   └── nord.py              ← NORD
│       └── widgets/
│           ├── bottom_panel.py      ← RigiBottomPanel (terminal + logs)
│           ├── sidebar.py           ← RigiSidebar
│           ├── statusbar.py         ← RigiStatusBar
│           ├── content_area.py      ← RigiContentArea
│           ├── border_frame.py      ← RigiBorderFrame
│           ├── palette.py           ← RigiPaletteScreen (Ctrl+P)
│           ├── help_panel.py        ← RigiHelpScreen, RigiShortcutsBar
│           ├── hamburger_menu.py    ← RigiHamburgerScreen
│           ├── settings_screen.py   ← RigiSettingsScreen
│           ├── gauge.py             ← RigiGauge, RigiSparkline
│           ├── image.py             ← RigiImage (kitty / iTerm2 / sixel)
│           ├── terminal_bar.py      ← RigiTerminalBar
│           └── mouse.py             ← RigiClickable, RigiDraggable
├── .github/
│   ├── workflows/
│   │   └── pr.yml                   ← PR quality checks
│   └── dependabot.yml
├── examples/
│   ├── 01_minimal.py
│   ├── 02_dashboard.py
│   ├── 03_todo.py
│   ├── 04_file_browser.py
│   ├── 05_system_monitor.py
│   ├── 06_notes.py
│   ├── 07_multi_theme.py
│   └── 08_platform_features.py
├── tests/
│   ├── test_basic.py
│   ├── test_commands.py
│   ├── test_help_system.py
│   ├── test_loggers.py
│   ├── test_log_store.py
│   ├── test_resize.py
│   ├── test_terminal.py
│   └── test_widgets.py
├── pyproject.toml
├── CONTRIBUTING.md
└── LICENSE
```

---

## 📖 Philosophy

This is a **personal library**, not a general-purpose open-source project.

- **No documentation.** Learn from the source code and the [`examples/`](examples/) directory.
- **No issues or discussions.** GitHub Issues and Discussions are disabled. Questions, feature requests, and support will not be answered.
- **Pull requests are welcome** - but only for: bug fixes, code optimization, cross-platform improvements, and features that expose missing Textual capabilities. Everything else will be closed without review.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact requirements.

---

<p align="center"><sub><a href="LICENSE">MIT</a> © reekeer</sub></p>
