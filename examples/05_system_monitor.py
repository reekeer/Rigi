"""System monitor — live CPU, memory, processes (uses only stdlib)."""

from __future__ import annotations

import os
import platform
import subprocess
import time

from rigi import App, TabDef
from rigi.layout.pane import Card, HPane, Pane
from rigi.widgets import DataTable, Label

app = App(
    name="sysmon", version="1.0.0", description="System resource monitor", home_tab="System"
)

_start = time.time()


def _uptime() -> str:
    s = int(time.time() - _start)
    h, m = divmod(s // 60, 60)
    return f"{h}h {m}m {s % 60}s"


def _read_cpu() -> str:
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:8])
        return f"{max(0, 100 - idle * 100 // max(total, 1))}%"
    except Exception:
        return "n/a"


def _read_mem() -> tuple[str, str, str]:
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k.strip()] = int(v.split()[0])
        total = info.get("MemTotal", 0)
        free = info.get("MemAvailable", 0)
        used = total - free
        pct = used * 100 // max(total, 1)

        def mb(kb: int) -> str:
            return f"{kb // 1024} MB"

        return mb(used), mb(total), f"{pct}%"
    except Exception:
        return "n/a", "n/a", "n/a"


def _top_procs(n: int = 10) -> list[tuple[str, str, str]]:
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"], text=True, timeout=2
        ).splitlines()[1 : n + 1]
        return [tuple(line.split(None, 3)[:3]) for line in out]  # type: ignore[return-value]
    except Exception:
        return []


def make_system():
    cpu = _read_cpu()
    mem_used, mem_total, mem_pct = _read_mem()
    uptime = _uptime()
    load = "n/a"
    try:
        load = " / ".join(f"{x:.2f}" for x in os.getloadavg())
    except AttributeError:
        pass

    procs_data = _top_procs()
    procs_table = DataTable()
    procs_table.add_columns("PID", "Name", "CPU%")
    for row in procs_data:
        procs_table.add_row(*row)

    return Pane(
        HPane(
            Card(
                Label(f"[bold]OS:[/bold]      {platform.system()} {platform.release()}"),
                Label(f"[bold]Arch:[/bold]    {platform.machine()}"),
                Label(f"[bold]Python:[/bold]  {platform.python_version()}"),
                Label(f"[bold]PID:[/bold]     {os.getpid()}"),
                Label(f"[bold]Uptime:[/bold]  {uptime}"),
                title=" Host",
            ),
            Card(
                Label(
                    f"[bold]CPU:[/bold]     [{'green' if int(cpu.rstrip('%') or 0) < 70 else 'red'}]{cpu}[/{'green' if int(cpu.rstrip('%') or 0) < 70 else 'red'}]"
                ),
                Label(f"[bold]Load:[/bold]    [dim]{load}[/dim]"),
                Label(f"[bold]Mem used:[/bold]  {mem_used}"),
                Label(f"[bold]Mem total:[/bold] {mem_total}"),
                Label(f"[bold]Mem %:[/bold]     [cyan]{mem_pct}[/cyan]"),
                title=" Resources",
            ),
        ),
        Card(procs_table, title=" Top Processes (by CPU)"),
    )


def make_env():
    table = DataTable()
    table.add_columns("Variable", "Value")
    interesting = [
        "PATH",
        "HOME",
        "USER",
        "SHELL",
        "TERM",
        "LANG",
        "EDITOR",
        "VIRTUAL_ENV",
        "CONDA_DEFAULT_ENV",
        "NODE_ENV",
    ]
    for key in interesting:
        val = os.environ.get(key, "[dim]not set[/dim]")
        if len(val) > 60:
            val = val[:57] + "..."
        table.add_row(f"[bold]{key}[/bold]", val)
    return Pane(table)


system_tab = TabDef(name="System", key="1", icon="", widget_factory=make_system)
env_tab = TabDef(name="Env", key="2", icon="", widget_factory=make_env)
app.add_tab(system_tab)
app.add_tab(env_tab)

app.add_status("cpu", "CPU", _read_cpu, refresh_interval=2.0)
app.add_status("mem", "Mem", lambda: _read_mem()[2], refresh_interval=3.0)
app.add_status("time", "Up", _uptime, refresh_interval=1.0)


@app.command("refresh", help="Refresh all tabs", aliases=["r"])
async def cmd_refresh(app: App, **_: object) -> None:
    app.invalidate_tab_cache()
    app.notify("Refreshed", timeout=2)


if __name__ == "__main__":
    App.run_cli(app)
