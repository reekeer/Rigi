from __future__ import annotations

from typing import Any

from textual.widget import Widget


class RigiPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiHPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiVPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiScrollPane(Widget):
    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiCard(Widget):
    def __init__(self, *children: Widget, title: str = "", **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._title = title
        if title:
            self.border_title = title


class RigiSplit(Widget):
    def __init__(self, *children: Widget, sizes: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._sizes = sizes

    def on_mount(self) -> None:
        if self._sizes:
            children = list(self.children)
            for child, size in zip(children, self._sizes, strict=False):
                child.styles.width = size
