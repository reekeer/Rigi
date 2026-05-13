"""Action menu example — popup menu with numbered actions."""

from __future__ import annotations

from rigi import ActionMenuItemData, App, TabDef
from rigi.layout.pane import Card, Pane
from rigi.widgets import Label

app = App(
    name="action-menu",
    version="1.0.0",
    description="Demo of RigiActionMenu",
    home_tab="Demo",
)


def make_demo():
    return Pane(
        Label("[bold]RigiActionMenu[/bold] — press [cyan]Ctrl+M[/cyan] or use the button below."),
        Label(""),
        Card(
            Label("Action menus show numbered items with color support."),
            Label("Click an item or press its number key to activate."),
            title=" Info",
        ),
    )


demo_tab = TabDef(name="Demo", key="1", icon="", widget_factory=make_demo)
app.add_tab(demo_tab)


@app.command("menu", help="Show the action menu")
async def cmd_menu(app: App, **_: object) -> None:
    items = [
        ActionMenuItemData("Copy", color="cyan", callback=lambda: app.notify("Copied!", timeout=2)),
        ActionMenuItemData("Paste", color="green", callback=lambda: app.notify("Pasted!", timeout=2)),
        ActionMenuItemData("Delete", color="red", callback=lambda: app.notify("Deleted!", timeout=2)),
        ActionMenuItemData("Rename", callback=lambda: app.notify("Renamed!", timeout=2)),
        ActionMenuItemData("Cancel", disabled=True),
    ]
    app.show_action_menu(items, title="Actions")


if __name__ == "__main__":
    App.run_cli(app)
