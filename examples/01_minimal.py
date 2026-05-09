"""Minimal Rigi app — one tab, one card."""
from __future__ import annotations

from rigi import RigiApp, TabDef
from rigi.layout.pane import RigiPane, RigiCard
from rigi.widgets import Label

app = RigiApp(name="minimal", version="1.0.0", description="Simplest possible Rigi app")


def home():
    return RigiPane(
        RigiCard(
            Label("Welcome to [bold cyan]Rigi[/bold cyan]!"),
            Label(""),
            Label("  [dim]Ctrl+H[/dim]   Help"),
            Label("  [dim]Ctrl+T[/dim]   Focus terminal"),
            Label("  [dim]Ctrl+Q[/dim]   Quit"),
            title="Getting started",
        ),
    )


app.add_tab(TabDef(name="Home", key="1", icon="⌂", widget_factory=home))

if __name__ == "__main__":
    RigiApp.run_cli(app)
