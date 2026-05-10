"""Theme showcase — demonstrates all built-in themes and custom CSS."""

from __future__ import annotations

import datetime

from rigi import RigiApp, TabDef
from rigi.layout.pane import RigiCard, RigiHPane, RigiPane, RigiSplit
from rigi.themes import DARK, LIGHT, MONOKAI, NORD
from rigi.widgets import Label, Markdown

app = RigiApp(
    name="themes",
    version="1.0.0",
    description="Theme & styling showcase",
    theme=DARK,
    home_tab="Showcase",
)

app.add_status("theme", "Theme", lambda: app._theme.name.capitalize(), refresh_interval=1.0)
app.add_status(
    "time", "Time", lambda: datetime.datetime.now().strftime("%H:%M"), refresh_interval=1.0
)


def make_showcase():
    return RigiPane(
        RigiHPane(
            RigiCard(
                Label("[bold red]Error[/bold red]        critical failure"),
                Label("[bold yellow]Warning[/bold yellow]      disk space low"),
                Label("[bold green]Success[/bold green]      deployment complete"),
                Label("[bold cyan]Info[/bold cyan]         3 new messages"),
                Label("[bold blue]Debug[/bold blue]        cache miss x42"),
                Label("[bold magenta]Trace[/bold magenta]        entering fn foo"),
                title=" Log Levels",
            ),
            RigiCard(
                Label("[dim]Disabled / secondary text[/dim]"),
                Label("[bold]Bold / primary text[/bold]"),
                Label("[italic]Italic annotation[/italic]"),
                Label("[underline]Underlined label[/underline]"),
                Label("[strike]Struck-through item[/strike]"),
                Label("[reverse]Reversed (highlight)[/reverse]"),
                title=" Text Styles",
            ),
        ),
        RigiCard(
            Markdown("""
## Color swatches

**Red family:**  `[red]` `[dark_red]` `[bright_red]`

**Green family:** `[green]` `[dark_green]` `[bright_green]`

**Blue family:**  `[blue]` `[cyan]` `[bright_cyan]`

**Neutral:**  `[white]` `[bright_white]` `[dim]`

> Switch theme with `theme dark|light|monokai|nord` in the terminal
"""),
            title=" Rich Markup Reference",
        ),
    )


def make_widgets():
    return RigiPane(
        RigiSplit(
            RigiCard(
                Label("  ● Active item"),
                Label("  ○ Inactive item"),
                Label("  ▶ Collapsed group"),
                Label("  ▼ Expanded group"),
                Label("  ─ Separator"),
                title=" Sidebar Icons",
            ),
            RigiCard(
                Label("  ⌂  Home button (active: [cyan]blue[/cyan])"),
                Label("  ☰  Hamburger menu"),
                Label("  ●  Terminal focused"),
                Label("  ○  Terminal unfocused"),
                Label("  ─  Resize handle"),
                title=" UI Elements",
            ),
        ),
    )


showcase_tab = TabDef(name="Showcase", key="1", icon="", widget_factory=make_showcase)
widgets_tab = TabDef(name="Widgets", key="2", icon="", widget_factory=make_widgets)
app.add_tab(showcase_tab)
app.add_tab(widgets_tab)


@app.command("theme", help="Switch theme: dark | light | monokai | nord")
async def cmd_theme(app: RigiApp, **kwargs: object) -> None:
    name = str(next(iter(kwargs.values()), "")).lower()
    themes = {"dark": DARK, "light": LIGHT, "monokai": MONOKAI, "nord": NORD}
    t = themes.get(name)
    if t is None:
        app.notify(f"Unknown theme '{name}'. Choose: {', '.join(themes)}", severity="warning")
        return
    app.set_theme(t)
    app.notify(f"Theme: {name}", timeout=2)


if __name__ == "__main__":
    RigiApp.run_cli(app)
