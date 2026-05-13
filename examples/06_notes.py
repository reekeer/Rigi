"""Notes app — markdown viewer with search and multiple sections."""

from __future__ import annotations

from rigi import App, TabDef
from rigi.layout.pane import Pane
from rigi.widgets import Markdown

app = App(name="notes", version="1.0.0", description="Markdown notes viewer")

_notes: dict[str, str] = {
    "Getting Started": """# Getting Started

Welcome to **Notes** — a simple markdown viewer built on Rigi.

## Navigation

Use the sidebar to browse sections. Press **Ctrl+T** to focus the terminal
and type commands.

## Available Commands

| Command         | Description              |
|-----------------|--------------------------|
| `note <name>`   | Jump to a note by name   |
| `new <name>`    | Create a blank note      |
| `list`          | List all notes           |
| `search <text>` | Search note contents     |

---

> Tip: press **→** to enter a subsection, **←** to go back.
""",
    "Rigi Overview": """# Rigi Overview

Rigi is a high-level TUI framework built on top of [Textual](https://textual.textualize.io).

## Core concepts

### Tabs & Subtabs

```python
tab = TabDef(name="Dashboard", key="1", icon="")
sub = tab.add_subtab("Reports", make_reports)
app.add_tab(tab)
```

### Status Bar

```python
app.add_status("cpu", "CPU", lambda: f"{cpu_pct()}%", refresh_interval=2.0)
```

### Terminal Commands

```python
@app.command("greet", help="Say hello")
async def greet(app, name="world", **_):
    app.notify(f"Hello, {name}!")
```

### Settings Panel

```python
general = app.settings.add_page("General")
general.settings = [
    Setting("Theme", description="Active color theme", value_fn=lambda: app._theme.name),
]
```
""",
    "Keyboard Shortcuts": """# Keyboard Shortcuts

## Navigation

| Key         | Action                      |
|-------------|-----------------------------|
| `↑` / `↓`  | Move through sidebar items  |
| `→`         | Enter subtab group          |
| `←`         | Go back / up a level        |
| `⌂`        | Navigate to home tab        |

## App

| Key         | Action                      |
|-------------|-----------------------------|
| `Ctrl+H`   | Open help panel             |
| `Ctrl+T`   | Focus terminal input        |
| `Ctrl+C`   | Copy focused text           |
| `Ctrl+Q`   | Quit application            |

## Terminal

| Key         | Action                      |
|-------------|-----------------------------|
| `Tab`       | Cycle through completions   |
| `↑` / `↓`  | Navigate command history    |
| `Enter`     | Submit command              |
""",
    "API Reference": """# API Reference

## App

```python
App(
    name: str,
    version: str = "0.1.0",
    description: str = "",
    username: str | None = None,
    home_tab: str | None = None,
    theme: Theme | None = None,
)
```

### Methods

- `add_tab(tab: TabDef) → TabDef`
- `add_status(key, label, value_fn, style, refresh_interval)`
- `add_setting(category, label, description, value_fn, action_fn)`
- `add_menu_item(label, callback, section)`
- `navigate_to_tab(name: str) → bool`
- `invalidate_tab_cache(tab_name=None)`
- `set_theme(theme: Theme)`
- `register_css(path)`

## TabDef

```python
TabDef(name, key=None, icon="", widget_factory=None)
tab.add_subtab(name, widget_factory=None, icon="", key=None)
```

## Layout helpers

- `Pane(*children)` — vertical stack
- `HPane(*children)` — horizontal row
- `VPane(*children)` — vertical column
- `Card(*children, title="")` — bordered card
- `Split(*children, sizes=None)` — horizontal split
""",
}


def _make_note(name: str):
    def _factory():
        content = _notes.get(name, f"# {name}\n\n*Empty note.*")
        return Pane(Markdown(content))

    return _factory


notes_tab = TabDef(name="Notes", key="1", icon="")
for title in _notes:
    notes_tab.add_subtab(title, _make_note(title))
app.add_tab(notes_tab)

app.add_status("count", "Notes", lambda: str(len(_notes)), refresh_interval=5.0)


@app.command("list", help="List all notes", aliases=["ls"])
async def cmd_list(app: App, **_: object) -> None:
    names = "\n".join(f"  • {n}" for n in _notes)
    app.notify(f"Notes:\n{names}", title="All notes")


@app.command("new", help="Create a blank note")
async def cmd_new(app: App, **kwargs: object) -> None:
    name = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not name:
        app.notify("Usage: new <note name>", severity="warning")
        return
    _notes[name] = f"# {name}\n\n*Start writing...*"
    app.notify(f"Created: {name}", timeout=2)


@app.command("search", help="Search note contents")
async def cmd_search(app: App, **kwargs: object) -> None:
    query = " ".join(str(v) for v in kwargs.values() if v).lower()
    if not query:
        app.notify("Usage: search <text>", severity="warning")
        return
    matches = [n for n, c in _notes.items() if query in c.lower()]
    if matches:
        app.notify("Found in: " + ", ".join(matches), title=f"Search: {query}")
    else:
        app.notify(f"No results for '{query}'", severity="warning")


if __name__ == "__main__":
    App.run_cli(app)
