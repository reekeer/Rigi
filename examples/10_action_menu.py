"""Action menu example — popup menu with numbered actions."""

from __future__ import annotations

from rigi import RigiActionMenuItemData, RigiApp, TabDef
from rigi.layout.pane import RigiCard, RigiPane
from rigi.widgets import Label

app = RigiApp(
    name="action-menu",
    version="1.0.0",
    description="Demo of RigiActionMenu",
    home_tab="Demo",
)


def make_demo():
    return RigiPane(
        Label("[bold]RigiActionMenu[/bold] — press [cyan]Ctrl+M[/cyan] or use the button below."),
        Label(""),
        RigiCard(
            Label("Action menus show numbered items with color support."),
            Label("Click an item or press its number key to activate."),
            title=" Info",
        ),
    )


demo_tab = TabDef(name="Demo", key="1", icon="", widget_factory=make_demo)
app.add_tab(demo_tab)


@app.command("menu", help="Show the action menu")
async def cmd_menu(app: RigiApp, **_: object) -> None:
    items = [
        RigiActionMenuItemData("Copy", color="cyan", callback=lambda: app.notify("Copied!", timeout=2)),
        RigiActionMenuItemData("Paste", color="green", callback=lambda: app.notify("Pasted!", timeout=2)),
        RigiActionMenuItemData("Delete", color="red", callback=lambda: app.notify("Deleted!", timeout=2)),
        RigiActionMenuItemData("Rename", callback=lambda: app.notify("Renamed!", timeout=2)),
        RigiActionMenuItemData("Cancel", disabled=True),
    ]
    app.show_action_menu(items, title="Actions")


if __name__ == "__main__":
    RigiApp.run_cli(app)
