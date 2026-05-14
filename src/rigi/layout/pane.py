from __future__ import annotations

from typing import Any

from textual.widget import Widget


class Pane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class HPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class VPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class ScrollPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class Card(Widget):
    def __init__(self, *children: Widget, title: str = "", **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._title = title
        if title:
            self.border_title = title


class Split(Widget):
    def __init__(self, *children: Widget, sizes: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._sizes = sizes

    def on_mount(self) -> None:
        if self._sizes:
            children = list(self.children)
            for child, size in zip(children, self._sizes, strict=False):
                child.styles.width = size
