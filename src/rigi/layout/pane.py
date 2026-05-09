from __future__ import annotations

from typing import Any

from textual.widget import Widget


class RigiPane(Widget):
    DEFAULT_CSS = "RigiPane { height: 100%; width: 100%; padding: 1 2; }"

    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiHPane(Widget):
    DEFAULT_CSS = "RigiHPane { layout: horizontal; height: 100%; width: 100%; }"

    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiVPane(Widget):
    DEFAULT_CSS = "RigiVPane { layout: vertical; height: 100%; width: 100%; }"

    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiScrollPane(Widget):
    DEFAULT_CSS = (
        "RigiScrollPane { height: 100%; width: 100%; overflow-y: auto; overflow-x: hidden; }"
    )

    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)


class RigiCard(Widget):
    DEFAULT_CSS = """
    RigiCard {
        border: round #30363d;
        border-title-color: #c9d1d9;
        border-title-align: left;
        padding: 1 2;
        margin: 0 0 1 0;
        height: auto;
    }
    """

    def __init__(self, *children: Widget, title: str = "", **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._title = title
        if title:
            self.border_title = title


class RigiSplit(Widget):
    DEFAULT_CSS = """
    RigiSplit {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }
    RigiSplit > Widget {
        width: 1fr;
        height: 100%;
    }
    """

    def __init__(self, *children: Widget, sizes: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._sizes = sizes

    def on_mount(self) -> None:
        if self._sizes:
            children = list(self.children)
            for child, size in zip(children, self._sizes, strict=False):
                child.styles.width = size
