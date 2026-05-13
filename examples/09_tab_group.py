"""TabGroup example — horizontal in-page tabs with optional wrapping."""

from __future__ import annotations

from rigi import App, TabDef, TabGroup
from rigi.layout.pane import Card, Pane
from rigi.widgets import Label

app = App(
    name="tab-group",
    version="1.0.0",
    description="Demo of TabGroup",
    home_tab="Demo",
)


def make_overview():
    return Pane(
        Label("[bold]TabGroup[/bold] — switch between panels horizontally."),
        Label(""),
        TabGroup(
            tabs=[
                (
                    "Overview",
                    lambda: Card(
                        Label("This is the overview panel."),
                        Label("Tab groups are great for settings or multi-step forms."),
                        title=" Overview",
                    ),
                ),
                (
                    "Settings",
                    lambda: Card(
                        Label("[dim]Option 1:[/dim] enabled"),
                        Label("[dim]Option 2:[/dim] disabled"),
                        title=" Settings",
                    ),
                ),
                (
                    "About",
                    lambda: Card(
                        Label("Version: 1.0.0"),
                        Label("Built with Rigi + Textual"),
                        title=" About",
                    ),
                ),
            ]
        ),
    )


demo_tab = TabDef(name="Demo", key="1", icon="", widget_factory=make_overview)
app.add_tab(demo_tab)

if __name__ == "__main__":
    App.run_cli(app)
