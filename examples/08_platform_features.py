"""Platform & features showcase — gauges, sparklines, clipboard, desktop notify."""

from __future__ import annotations

import asyncio
import random

from rigi import App, TabDef, platform
from rigi.layout.pane import Card, Pane
from rigi.widgets import Gauge, Label, Markdown, Sparkline

app = App(
    name="platform-demo",
    version="1.0.0",
    description="Platform features & new widgets showcase",
    home_tab="Overview",
)

# ── Live metric state ──────────────────────────────────────────────────────────
_cpu_history: list[float] = []
_mem_history: list[float] = []
_net_history: list[float] = []

_gauge_cpu: Gauge | None = None
_gauge_mem: Gauge | None = None
_spark_cpu: Sparkline | None = None
_spark_mem: Sparkline | None = None
_spark_net: Sparkline | None = None


def _read_cpu_pct() -> float:
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:8])
        return max(0.0, 100.0 - idle * 100.0 / max(total, 1))
    except Exception:
        return random.uniform(5, 60)


def _read_mem_pct() -> float:
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k.strip()] = int(v.split()[0])
        total = info.get("MemTotal", 1)
        free = info.get("MemAvailable", 1)
        return (total - free) * 100.0 / max(total, 1)
    except Exception:
        return random.uniform(30, 70)


def make_overview() -> Pane:
    global _gauge_cpu, _gauge_mem, _spark_cpu, _spark_mem, _spark_net

    _gauge_cpu = Gauge(label="CPU", value=_read_cpu_pct(), color="green")
    _gauge_mem = Gauge(label="MEM", value=_read_mem_pct(), color="cyan")
    _spark_cpu = Sparkline(color="green")
    _spark_mem = Sparkline(color="cyan")
    _spark_net = Sparkline(color="yellow")

    cols, lines = platform.terminal_size()

    return Pane(
        Card(
            Label(f"[bold]Platform:[/bold]  {platform.PLATFORM_NAME}"),
            Label(f"[bold]Arch:[/bold]      {platform.ARCH}"),
            Label(f"[bold]Wayland:[/bold]   {'yes' if platform.IS_WAYLAND else 'no'}"),
            Label(f"[bold]Terminal:[/bold]  {cols}×{lines}"),
            title=" System",
        ),
        Card(
            Label("CPU usage"),
            _gauge_cpu,
            _spark_cpu,
            Label(""),
            Label("Memory usage"),
            _gauge_mem,
            _spark_mem,
            Label(""),
            Label("Network (simulated)"),
            _spark_net,
            title=" Live Metrics",
        ),
    )


def make_platform() -> Pane:
    import sys

    return Pane(
        Card(
            Markdown(f"""
## Platform Details

| Property | Value |
|----------|-------|
| OS | {platform.PLATFORM_NAME} {platform.PLATFORM_VERSION} |
| Arch | {platform.ARCH} |
| Python | {sys.version.split()[0]} |
| Wayland | {'✓' if platform.IS_WAYLAND else '✗'} |
| Windows | {'✓' if platform.IS_WINDOWS else '✗'} |
| macOS | {'✓' if platform.IS_MACOS else '✗'} |
| Linux | {'✓' if platform.IS_LINUX else '✗'} |
"""),
            title=" Platform",
        ),
        Card(
            Markdown(f"""
## Config Directories

| Purpose | Path |
|---------|------|
| Config | `{platform.config_dir('platform-demo')}` |
| Data   | `{platform.data_dir('platform-demo')}` |
| Cache  | `{platform.cache_dir('platform-demo')}` |

> These follow XDG on Linux, `~/Library/...` on macOS, `AppData` on Windows.
"""),
            title=" Directories",
        ),
    )


def make_features() -> Pane:
    return Pane(
        Card(
            Markdown("""
## New Features in this Build

### Widgets
- **Gauge** — horizontal progress bar with label and %
- **Sparkline** — rolling mini-chart, push values with `.push(v)`

### App Methods
- `app.open_url(url)` — open browser cross-platform
- `app.open_path(path)` — open file/dir with OS app
- `app.notify_desktop(title, body)` — OS desktop notification
- `app.schedule_task(coro)` — background async task (Textual 8 Worker API)

### Platform Module
- `rigi.platform.IS_WINDOWS / IS_MACOS / IS_LINUX / IS_WAYLAND`
- `rigi.platform.config_dir(name)` — XDG / AppData / Library
- `rigi.platform.copy_to_clipboard(text)` — wl-copy / pbcopy / clip
- `rigi.platform.terminal_size()` — (columns, lines)

### Terminal
- **History persisted** to `config_dir/<app>/terminal_history`
- **Fuzzy completion** — tab matches even non-prefix substrings
- **Ctrl+P** — command palette with fuzzy search

### Config
- `RIGI_THEME=dark|light|monokai|nord` env var
- `RIGI_SIDEBAR_WIDTH=<n>` env var
"""),
            title=" What's New",
        ),
    )


overview_tab = TabDef(name="Overview", key="1", icon="", widget_factory=make_overview)
platform_tab = TabDef(name="Platform", key="2", icon="", widget_factory=make_platform)
features_tab = TabDef(name="Features", key="3", icon="", widget_factory=make_features)
app.add_tab(overview_tab)
app.add_tab(platform_tab)
app.add_tab(features_tab)

app.add_status("cpu", "CPU", lambda: f"{_read_cpu_pct():.0f}%", refresh_interval=2.0)
app.add_status("mem", "Mem", lambda: f"{_read_mem_pct():.0f}%", refresh_interval=3.0)
app.add_status("os", "OS", lambda: platform.PLATFORM_NAME, refresh_interval=60.0)


@app.on_startup
async def _start_metrics(a: App) -> None:  # pyright: ignore[reportUnusedFunction]
    async def _loop() -> None:
        while True:
            cpu = _read_cpu_pct()
            mem = _read_mem_pct()
            net = random.uniform(0, 100)

            if _gauge_cpu is not None:
                _gauge_cpu.value = cpu
            if _gauge_mem is not None:
                _gauge_mem.value = mem
            if _spark_cpu is not None:
                _spark_cpu.push(cpu)
            if _spark_mem is not None:
                _spark_mem.push(mem)
            if _spark_net is not None:
                _spark_net.push(net)

            await asyncio.sleep(1.0)

    a.schedule_task(_loop())


@app.command("open", help="Open a URL or path  (e.g. open https://example.com)")
async def cmd_open(app: App, **kwargs: object) -> None:
    target = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not target:
        app.notify("Usage: open <url|path>", severity="warning")
        return
    if target.startswith("http://") or target.startswith("https://"):
        app.open_url(target)
        app.notify(f"Opened: {target}", severity="information")
    else:
        ok = app.open_path(target)
        app.notify(
            f"Opened: {target}" if ok else f"Failed to open: {target}",
            severity="information" if ok else "error",
        )


@app.command("copy", help="Copy text to clipboard")
async def cmd_copy(app: App, **kwargs: object) -> None:
    text = " ".join(str(v) for v in kwargs.values() if v).strip()
    if not text:
        app.notify("Usage: copy <text>", severity="warning")
        return
    from rigi.core.platform import copy_to_clipboard

    ok = copy_to_clipboard(text)
    app.notify(
        "Copied!" if ok else "Clipboard unavailable", severity="information" if ok else "warning"
    )


@app.command("desktop-notify", help="Send OS desktop notification", aliases=["dn"])
async def cmd_dn(app: App, **kwargs: object) -> None:
    text = " ".join(str(v) for v in kwargs.values() if v).strip() or "Hello from Rigi!"
    ok = app.notify_desktop("Rigi", text)
    app.notify(
        "Notification sent" if ok else "Desktop notifications unavailable",
        severity="information" if ok else "warning",
    )


@app.command("gauge", help="Demo: set CPU gauge value  (e.g. gauge 75)")
async def cmd_gauge(app: App, **kwargs: object) -> None:
    try:
        val = float(str(next(iter(kwargs.values()))))
        if _gauge_cpu is not None:
            _gauge_cpu.value = val
        app.notify(f"CPU gauge → {val:.0f}%", timeout=2)
    except (TypeError, ValueError, StopIteration):
        app.notify("Usage: gauge <0-100>", severity="warning")


if __name__ == "__main__":
    App.run_cli(app)
