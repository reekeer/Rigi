"""Action menu + editable table example."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.widget import Widget
from textual.widgets import DataTable, Input, Label

from rigi import ActionMenuItemData, App, TabDef
from rigi.layout.pane import Card, Pane


_COLUMNS = ("Name", "Age", "City", "Role")
_ROWS = [
    ("Alice", "30", "New York", "Engineer"),
    ("Bob", "25", "London", "Designer"),
    ("Carol", "35", "Tokyo", "Manager"),
    ("Dave", "28", "Berlin", "Developer"),
    ("Eve", "32", "Paris", "Analyst"),
]

app = App(
    name="action-menu",
    version="1.0.0",
    description="Demo of ActionMenu and EditableTable",
    home_tab="Demo",
)


class EditableTable(Widget):
    DEFAULT_CSS = """
    EditableTable {
        layout: vertical;
        height: 1fr;
        width: 100%;
    }
    EditableTable #cell-input {
        margin-bottom: 1;
    }
    EditableTable DataTable {
        height: 1fr;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("e", "edit_cell", "Edit"),
        Binding("enter", "edit_cell", "Edit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._data: list[list[str]] = [list(r) for r in _ROWS]
        self._col_keys: list[object] = []
        self._row_keys: list[object] = []
        self._editing: tuple[int, int] | None = None

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Edit — Enter to save, Esc to cancel", id="cell-input")
        yield DataTable()

    def on_mount(self) -> None:
        self.query_one(Input).display = False
        table = self.query_one(DataTable)
        table.cursor_type = "cell"
        self._col_keys = list(table.add_columns(*_COLUMNS))
        for row in self._data:
            self._row_keys.append(table.add_row(*row))

    def action_edit_cell(self) -> None:
        inp = self.query_one(Input)
        if inp.display:
            return
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate
        row_idx, col_idx = coord.row, coord.column
        inp.value = self._data[row_idx][col_idx]
        inp.display = True
        inp.focus()
        self._editing = (row_idx, col_idx)

    @on(Input.Submitted, "#cell-input")
    def _on_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._save(event.value)

    def on_key(self, event: Key) -> None:
        if event.key == "escape" and self.query_one(Input).display:
            event.stop()
            self._cancel()

    def _save(self, value: str) -> None:
        if self._editing is None:
            return
        row_idx, col_idx = self._editing
        self._data[row_idx][col_idx] = value
        table = self.query_one(DataTable)
        table.update_cell(self._row_keys[row_idx], self._col_keys[col_idx], value)
        self._editing = None
        self.query_one(Input).display = False
        table.focus()

    def _cancel(self) -> None:
        self._editing = None
        self.query_one(Input).display = False
        self.query_one(DataTable).focus()


def make_demo() -> Widget:
    return Pane(
        Label("[bold]ActionMenu[/bold] — press [cyan]Ctrl+M[/cyan] or use the button below."),
        Label(""),
        Card(
            Label("Action menus show numbered items with color support."),
            Label("Click an item or press its number key to activate."),
            title=" Info",
        ),
    )


def make_table() -> Widget:
    return Pane(
        Label(
            "[bold]Editable Table[/bold] — arrow keys to navigate, "
            "[cyan]E[/cyan] or [cyan]Enter[/cyan] to edit a cell, [cyan]Esc[/cyan] to cancel."
        ),
        Label(""),
        EditableTable(),
    )


app.add_tab(TabDef(name="Demo", key="1", icon="", widget_factory=make_demo))
app.add_tab(TabDef(name="Table", key="2", icon="", widget_factory=make_table))


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
