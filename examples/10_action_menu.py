"""Action menu + editable table example."""

from __future__ import annotations

from typing import Any, cast

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import MouseDown
from textual.screen import ModalScreen
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


class _EditRowScreen(ModalScreen[list[str] | None]):
    DEFAULT_CSS = """
    _EditRowScreen {
        align: center middle;
    }
    _EditRowScreen > #er-box {
        width: 48;
        height: auto;
        border: round #30363d;
        background: #0d1117;
        padding: 1 2;
    }
    _EditRowScreen #er-title {
        color: #58a6ff;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    _EditRowScreen .er-label {
        color: #6e7681;
        height: 1;
        margin-top: 1;
    }
    _EditRowScreen .er-input {
        height: 1;
        border: solid #30363d;
        background: #161b22;
        color: #e6edf3;
        padding: 0 1;
    }
    _EditRowScreen .er-input:focus {
        border: solid #58a6ff;
    }
    _EditRowScreen #er-hint {
        color: #3d444d;
        height: 1;
        margin-top: 1;
        content-align: center middle;
        width: 100%;
    }
    """

    BINDINGS = [Binding("escape", "dismiss_none", show=False)]

    def __init__(self, columns: tuple[str, ...], values: list[str]) -> None:
        super().__init__()
        self._columns = columns
        self._values = values

    def compose(self) -> ComposeResult:
        with Widget(id="er-box"):
            yield Label("Edit Row", id="er-title")
            for col, val in zip(self._columns, self._values, strict=True):
                yield Label(col, classes="er-label")
                yield Input(value=val, classes="er-input")
            yield Label("Enter — save  ·  Esc — cancel", id="er-hint")

    def on_mount(self) -> None:
        inputs = list(self.query(Input))
        if inputs:
            inputs[0].focus()

    def action_dismiss_none(self) -> None:
        self.dismiss(None)

    @on(Input.Submitted)
    def _on_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        inputs = list(self.query(Input))
        try:
            idx = inputs.index(event.input)
        except ValueError:
            idx = -1
        if idx == len(inputs) - 1:
            self.dismiss([inp.value for inp in inputs])
        elif idx >= 0:
            inputs[idx + 1].focus()


class EditableTable(Widget):
    DEFAULT_CSS = """
    EditableTable {
        layout: vertical;
        height: 1fr;
        width: 100%;
    }
    EditableTable DataTable {
        height: 1fr;
        width: 100%;
    }
    """

    BINDINGS = [Binding("e", "row_menu", "Actions")]

    def __init__(self) -> None:
        super().__init__()
        self._data: list[list[str]] = [list(r) for r in _ROWS]
        self._col_keys: list[Any] = []
        self._row_keys: list[Any] = []

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        self._col_keys = list(table.add_columns(*_COLUMNS))
        for row in self._data:
            self._row_keys.append(table.add_row(*row))

    def action_row_menu(self) -> None:
        table = self.query_one(DataTable)
        row_idx = table.cursor_coordinate.row
        x = table.region.x + 2
        y = table.region.y + row_idx + 2
        self._show_row_menu(row_idx, x, y)

    def on_mouse_down(self, event: MouseDown) -> None:
        if event.button == 3:
            event.stop()
            table = self.query_one(DataTable)
            table_region = table.region
            row_in_view = event.screen_y - table_region.y - 1
            scroll_y = int(table.scroll_offset.y)
            row_idx = max(0, min(row_in_view + scroll_y, len(self._data) - 1))
            if row_in_view >= 0:
                self._show_row_menu(row_idx, event.screen_x, event.screen_y)

    def _show_row_menu(self, row_idx: int, x: int, y: int) -> None:
        if row_idx < 0 or row_idx >= len(self._data):
            return
        items = [
            ActionMenuItemData("Edit", callback=lambda: self._edit_row(row_idx)),
            ActionMenuItemData("Delete", color="red", callback=lambda: self._delete_row(row_idx)),
        ]
        cast(App, self.app).show_action_menu(items, x=x, y=y)

    def _edit_row(self, row_idx: int) -> None:
        def _apply(values: list[str] | None) -> None:
            if values is None:
                return
            self._data[row_idx] = values
            table = self.query_one(DataTable)
            for col_idx, val in enumerate(values):
                table.update_cell(self._row_keys[row_idx], self._col_keys[col_idx], val)

        cast(App, self.app).push_screen(
            _EditRowScreen(_COLUMNS, list(self._data[row_idx])),
            _apply,
        )

    def _delete_row(self, row_idx: int) -> None:
        table = self.query_one(DataTable)
        table.remove_row(self._row_keys[row_idx])
        self._data.pop(row_idx)
        self._row_keys.pop(row_idx)


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
            "[bold]Editable Table[/bold] — arrows to navigate, "
            "[cyan]E[/cyan] or [cyan]RMB[/cyan] for actions."
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
        ActionMenuItemData(
            "Paste", color="green", callback=lambda: app.notify("Pasted!", timeout=2)
        ),
        ActionMenuItemData(
            "Delete", color="red", callback=lambda: app.notify("Deleted!", timeout=2)
        ),
        ActionMenuItemData("Rename", callback=lambda: app.notify("Renamed!", timeout=2)),
        ActionMenuItemData("Cancel", disabled=True),
    ]
    app.show_action_menu(items, title="Actions")


if __name__ == "__main__":
    App.run_cli(app)
