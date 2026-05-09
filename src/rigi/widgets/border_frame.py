from __future__ import annotations

from textual.widget import Widget


class RigiBorderFrame(Widget):
    DEFAULT_CSS = """
    RigiBorderFrame {
        width: 100%;
        height: 100%;
        border: round #30363d;
        layout: vertical;
        padding: 0;
    }
    """

    def __init__(self, prog_name: str, version: str) -> None:
        super().__init__()
        self.border_title = f" {prog_name} v{version} "
        self.border_title_align = "left"
