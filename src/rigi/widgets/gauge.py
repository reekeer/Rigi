"""Gauge and sparkline widgets for Rigi apps."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widget import Widget


class RigiGauge(Widget):
    """Horizontal progress bar — set .value to update."""

    def __init__(
        self,
        label: str = "",
        value: float = 0.0,
        total: float = 100.0,
        color: str = "green",
        show_pct: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._value = float(value)
        self._total = float(total)
        self._color = color
        self._show_pct = show_pct

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._value = max(0.0, min(self._total, float(v)))
        self.refresh()

    @property
    def percentage(self) -> float:
        return self._value / max(self._total, 1e-9)

    def render(self) -> Text:
        pct = self.percentage
        width = self.size.width
        label_part = f"{self._label} " if self._label else ""
        pct_str = f" {pct * 100:.0f}%" if self._show_pct else ""
        bar_width = max(1, width - len(label_part) - len(pct_str))
        filled = int(bar_width * pct)
        empty = bar_width - filled
        t = Text(no_wrap=True, overflow="crop")
        if label_part:
            t.append(label_part, style="bold")
        t.append("█" * filled, style=self._color)
        t.append("░" * empty, style="dim")
        if pct_str:
            t.append(pct_str, style="dim")
        return t


class RigiSparkline(Widget):
    """Inline sparkline chart. Call .push(value) to add data points."""

    _BARS = " ▁▂▃▄▅▆▇█"

    def __init__(
        self,
        data: list[float] | None = None,
        color: str = "cyan",
        max_points: int = 300,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._data: list[float] = list(data) if data else []
        self._color = color
        self._max_points = max_points

    def push(self, value: float) -> None:
        self._data.append(value)
        if len(self._data) > self._max_points:
            self._data = self._data[-self._max_points :]
        self.refresh()

    def clear(self) -> None:
        self._data.clear()
        self.refresh()

    def render(self) -> Text:
        width = self.size.width
        if not self._data:
            return Text("─" * width, style="dim")
        data = self._data[-width:]
        lo, hi = min(data), max(data)
        span = float(hi - lo) or 1.0
        n = len(self._BARS) - 1
        chars = "".join(self._BARS[int((v - lo) / span * n)] for v in data)
        return Text(chars.ljust(width, " "), style=self._color)
