from __future__ import annotations

from textual.widget import Widget


class BorderFrame(Widget):
    def __init__(self, prog_name: str, version: str) -> None:
        super().__init__()
        self.border_title = f" {prog_name} v{version} "
        self.border_title_align = "left"
