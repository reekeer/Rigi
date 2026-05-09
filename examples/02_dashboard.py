"""Dashboard with live stats, a table, and nested subtabs."""
from __future__ import annotations

import datetime
import os
import random

from rigi import RigiApp, TabDef
from rigi.layout.pane import RigiCard, RigiHPane, RigiPane, RigiSplit
from rigi.widgets import DataTable, Label, Markdown

app = RigiApp(
    name="dashboard",
    version="2.0.0",
    description="Live metrics dashboard",
    home_tab="Overview",
)

app.add_status("time",  "Time",   lambda: datetime.datetime.now().strftime("%H:%M:%S"), refresh_interval=1.0)
app.add_status("cpu",   "CPU",    lambda: f"{random.randint(10, 85)}%",                refresh_interval=2.0)
app.add_status("mem",   "Mem",    lambda: f"{random.randint(40, 70)}%",                refresh_interval=3.0)


def make_overview():
    return RigiPane(
        RigiHPane(
            RigiCard(
                Label(f"[bold green]{random.randint(100, 999)}[/bold green]  requests/s"),
                Label(f"[bold yellow]{random.randint(1, 30)}ms[/bold yellow]  avg latency"),
                Label(f"[bold cyan]{random.randint(5, 50)}[/bold cyan]  active users"),
                title=" Overview",
            ),
            RigiCard(
                Label("[green]●[/green]  API          [dim]healthy[/dim]"),
                Label("[green]●[/green]  Database     [dim]healthy[/dim]"),
                Label("[yellow]●[/yellow]  Cache        [dim]degraded[/dim]"),
                Label("[green]●[/green]  Queue        [dim]healthy[/dim]"),
                Label("[red]●[/red]  Analytics    [dim]down[/dim]"),
                title=" Services",
            ),
        ),
        RigiCard(
            Label(f"Uptime:   [cyan]{random.randint(1, 99)}d {random.randint(0,23)}h[/cyan]"),
            Label(f"Version:  [dim]v{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}[/dim]"),
            Label(f"Region:   [dim]eu-west-1[/dim]"),
            Label(f"PID:      [dim]{os.getpid()}[/dim]"),
            title=" System",
        ),
    )


def make_metrics_table():
    table = DataTable()
    table.add_columns("Metric", "Value", "Min", "Max", "Trend")
    metrics = [
        ("CPU Usage",     f"{random.randint(10, 85)}%",  "2%",   "98%",  "↗"),
        ("Memory",        f"{random.randint(40, 70)}%",  "12%",  "95%",  "→"),
        ("Disk I/O",      f"{random.randint(5, 40)} MB/s","0",   "200",  "↘"),
        ("Network In",    f"{random.randint(1, 50)} MB/s","0",   "1000", "↗"),
        ("Network Out",   f"{random.randint(1, 30)} MB/s","0",   "500",  "→"),
        ("DB Connections",f"{random.randint(5, 50)}",    "0",    "100",  "↗"),
        ("Queue Depth",   f"{random.randint(0, 200)}",   "0",    "1000", "↘"),
        ("Cache Hit Rate",f"{random.randint(60, 95)}%",  "0%",   "100%", "→"),
    ]
    for row in metrics:
        table.add_row(*row)
    return RigiPane(table)


def make_logs():
    levels = ["INFO", "DEBUG", "WARN", "ERROR"]
    services = ["api", "db", "cache", "worker", "scheduler"]
    lines = []
    for i in range(20):
        t = datetime.datetime.now() - datetime.timedelta(seconds=i * 30)
        lvl = random.choice(levels)
        color = {"INFO": "cyan", "DEBUG": "dim", "WARN": "yellow", "ERROR": "red"}[lvl]
        svc = random.choice(services)
        lines.append(f"[{color}]{lvl:5}[/{color}]  [dim]{t.strftime('%H:%M:%S')}[/dim]  [bold]{svc}[/bold]  request handled")

    return RigiPane(
        RigiCard(*[Label(l) for l in lines], title=" Recent Logs"),
    )


overview_tab = TabDef(name="Overview", key="1", icon="", widget_factory=make_overview)
app.add_tab(overview_tab)

metrics_tab = TabDef(name="Metrics", key="2", icon="")
metrics_tab.add_subtab("Live Table", make_metrics_table, icon="")
metrics_tab.add_subtab("Logs",       make_logs,          icon="")
app.add_tab(metrics_tab)

app.add_menu_item("Refresh all", lambda: app.invalidate_tab_cache(), section="Data")


@app.command("refresh", help="Refresh widget cache", aliases=["r"])
async def cmd_refresh(app: RigiApp, **_: object) -> None:
    app.invalidate_tab_cache()
    app.notify("Refreshed", timeout=2)


if __name__ == "__main__":
    RigiApp.run_cli(app)
