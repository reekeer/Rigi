"""Todo app — add/complete/delete tasks via terminal commands."""

from __future__ import annotations

from rigi import App, TabDef
from rigi.layout.pane import Card, Pane
from rigi.widgets import DataTable, Label

app = App(name="todo", version="1.0.0", description="Terminal todo manager", home_tab="Tasks")

_tasks: list[dict[str, object]] = [
    {"id": 1, "text": "Set up project structure", "done": True, "priority": "high"},
    {"id": 2, "text": "Write unit tests", "done": False, "priority": "high"},
    {"id": 3, "text": "Add CI pipeline", "done": False, "priority": "medium"},
    {"id": 4, "text": "Update documentation", "done": False, "priority": "low"},
    {"id": 5, "text": "Code review pass", "done": False, "priority": "medium"},
]
_next_id = 6


def make_tasks():
    table = DataTable()
    table.add_columns("ID", "✓", "Priority", "Task", "Added")
    priority_color = {"high": "red", "medium": "yellow", "low": "cyan"}
    for t in _tasks:
        done_mark = "[green]✓[/green]" if t["done"] else "[dim]○[/dim]"
        pri = str(t["priority"])
        col = priority_color.get(pri, "white")
        task_text = f"[dim]{t['text']}[/dim]" if t["done"] else str(t["text"])
        table.add_row(str(t["id"]), done_mark, f"[{col}]{pri}[/{col}]", task_text, "today")
    return Pane(
        table,
        Card(
            Label("[dim]add <text>        [/dim] Add new task"),
            Label("[dim]done <id>         [/dim] Mark complete"),
            Label("[dim]delete <id>       [/dim] Delete task"),
            Label("[dim]priority <id> <p> [/dim] Set priority (high/medium/low)"),
            Label("[dim]clear             [/dim] Remove all done tasks"),
            title=" Commands",
        ),
    )


def make_done():
    done = [t for t in _tasks if t["done"]]
    return Pane(
        Card(
            *[Label(f"[green]✓[/green]  {t['text']}") for t in done]
            or [Label("[dim]No completed tasks yet[/dim]")],
            title=f" Completed ({len(done)})",
        ),
    )


tasks_tab = TabDef(name="Tasks", key="1", icon="", widget_factory=make_tasks)
done_tab = TabDef(name="Done", key="2", icon="", widget_factory=make_done)
app.add_tab(tasks_tab)
app.add_tab(done_tab)

app.add_status("total", "Total", lambda: str(len(_tasks)), refresh_interval=1.0)
app.add_status(
    "open", "Open", lambda: str(sum(1 for t in _tasks if not t["done"])), refresh_interval=1.0
)
app.add_status(
    "done", "Done", lambda: str(sum(1 for t in _tasks if t["done"])), refresh_interval=1.0
)


@app.command("add", help="Add a new task")
async def cmd_add(app: App, **kwargs: object) -> None:
    global _next_id
    text = " ".join(str(v) for v in kwargs.values() if v)
    if not text:
        app.notify("Usage: add <task text>", severity="warning")
        return
    _tasks.append({"id": _next_id, "text": text, "done": False, "priority": "medium"})
    _next_id += 1
    app.invalidate_tab_cache()
    app.notify(f"Added: {text}", timeout=2)


@app.command("done", help="Mark task as complete")
async def cmd_done(app: App, **kwargs: object) -> None:
    try:
        tid = int(next(iter(kwargs.values())))  # type: ignore[arg-type]
        task = next(t for t in _tasks if t["id"] == tid)
        task["done"] = True
        app.invalidate_tab_cache()
        app.notify(f"Completed: {task['text']}", timeout=2)
    except (StopIteration, ValueError, TypeError):
        app.notify("Usage: done <id>", severity="warning")


@app.command("delete", help="Delete a task", aliases=["del", "rm"])
async def cmd_delete(app: App, **kwargs: object) -> None:
    try:
        tid = int(next(iter(kwargs.values())))  # type: ignore[arg-type]
        task = next(t for t in _tasks if t["id"] == tid)
        _tasks.remove(task)
        app.invalidate_tab_cache()
        app.notify(f"Deleted: {task['text']}", timeout=2)
    except (StopIteration, ValueError, TypeError):
        app.notify("Usage: delete <id>", severity="warning")


@app.command("clear", help="Remove all completed tasks")
async def cmd_clear(app: App, **_: object) -> None:
    removed = sum(1 for t in _tasks if t["done"])
    _tasks[:] = [t for t in _tasks if not t["done"]]
    app.invalidate_tab_cache()
    app.notify(f"Removed {removed} completed tasks", timeout=2)


if __name__ == "__main__":
    App.run_cli(app)
