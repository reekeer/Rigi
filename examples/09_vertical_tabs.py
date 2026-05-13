"""Vertical tabs example — in-page tab switcher."""

from __future__ import annotations

from rigi import RigiApp, RigiVerticalTabs, TabDef
from rigi.layout.pane import RigiCard, RigiPane
from rigi.widgets import Label

app = RigiApp(
    name="vertical-tabs",
    version="1.0.0",
    description="Demo of RigiVerticalTabs",
    home_tab="Demo",
)


def make_overview():
    return RigiPane(
        Label("[bold]RigiVerticalTabs[/bold] — switch between panels vertically."),
        Label(""),
        RigiVerticalTabs(
            tabs=[
                (
                    "Overview",
                    lambda: RigiCard(
                        Label("This is the overview panel."),
                        Label("Vertical tabs are great for settings or multi-step forms."),
                        title=" Overview",
                    ),
                ),
                (
                    "Settings",
                    lambda: RigiCard(
                        Label("[dim]Option 1:[/dim] enabled"),
                        Label("[dim]Option 2:[/dim] disabled"),
                        title=" Settings",
                    ),
                ),
                (
                    "About",
                    lambda: RigiCard(
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
    RigiApp.run_cli(app)
