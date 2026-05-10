from __future__ import annotations

import base64
import io
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any

from rich.color import Color as RichColor
from rich.segment import Segment
from rich.style import Style
from textual.geometry import Size
from textual.strip import Strip
from textual.widget import Widget

try:
    from PIL import Image as PILImage

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


class TerminalImageProtocol(Enum):
    KITTY = auto()
    ITERM2 = auto()
    SIXEL = auto()
    BLOCKS = auto()


def detect_image_protocol() -> TerminalImageProtocol:
    term = os.environ.get("TERM", "")
    term_program = os.environ.get("TERM_PROGRAM", "")

    if "KITTY_WINDOW_ID" in os.environ or term == "xterm-kitty":
        return TerminalImageProtocol.KITTY
    if term_program == "iTerm.app":
        return TerminalImageProtocol.ITERM2
    if "sixel" in term or "sixel" in os.environ.get("TERM_FEATURES", "").lower():
        return TerminalImageProtocol.SIXEL
    return TerminalImageProtocol.BLOCKS


def _encode_kitty(img_bytes: bytes, cols: int = 0, rows: int = 0) -> str:
    data = base64.standard_b64encode(img_bytes).decode()
    chunks = [data[i : i + 4096] for i in range(0, len(data), 4096)]
    parts: list[str] = []
    for idx, chunk in enumerate(chunks):
        m = 1 if idx < len(chunks) - 1 else 0
        if idx == 0:
            payload = f"a=T,f=100,m={m}"
            if cols:
                payload += f",c={cols}"
            if rows:
                payload += f",r={rows}"
        else:
            payload = f"m={m}"
        parts.append(f"\x1b_G{payload};{chunk}\x1b\\")
    return "".join(parts)


def _encode_iterm2(img_bytes: bytes, width: int, height: int) -> str:
    b64 = base64.standard_b64encode(img_bytes).decode()
    size = len(img_bytes)
    return f"\x1b]1337;File=inline=1;size={size};width={width}px;height={height}px:{b64}\x07"


def _encode_sixel(img: PILImage.Image) -> str:
    img = img.convert(
        "P", dither=PILImage.Dither.FLOYDSTEINBERG, palette=PILImage.Palette.ADAPTIVE, colors=256
    )
    palette_raw = img.getpalette() or []
    palette = [
        (palette_raw[i * 3], palette_raw[i * 3 + 1], palette_raw[i * 3 + 2])
        for i in range(len(palette_raw) // 3)
    ]
    width, height = img.size
    pixels = list(img.getdata())  # type: ignore[arg-type]

    pal_def = "".join(
        f"#{i};2;{round(r/255*100)};{round(g/255*100)};{round(b/255*100)}"
        for i, (r, g, b) in enumerate(palette[:256])
    )

    body_lines: list[str] = []
    for band_y in range(0, height, 6):
        bands: dict[int, list[tuple[int, int]]] = {}
        for row in range(6):
            y = band_y + row
            if y >= height:
                break
            for x in range(width):
                c = pixels[y * width + x]
                bands.setdefault(c, []).append((row, x))

        row_parts: list[str] = []
        for color_idx, cells in sorted(bands.items()):
            row_parts.append(f"#{color_idx}")
            last_x = -1
            for row, x in sorted(cells, key=lambda p: p[1] * 10 + p[0]):
                if x > last_x + 1:
                    gap = x - last_x - 1
                    row_parts.append(f"!{gap}?" if gap > 1 else "?")
                row_parts.append(chr(63 + (1 << row)))
                last_x = x
            row_parts.append("$")
        body_lines.append("".join(row_parts) + "-")

    return "\x1bPq" + pal_def + "".join(body_lines) + "\x1b\\"


def _render_blocks(
    img: PILImage.Image,
) -> list[list[tuple[tuple[int, int, int], tuple[int, int, int]]]]:
    rgb = img.convert("RGB")
    width, height = rgb.size
    if height % 2 != 0:
        padded = PILImage.new("RGB", (width, height + 1), (0, 0, 0))
        padded.paste(rgb, (0, 0))
        rgb = padded
        height += 1
    pixels = list(rgb.getdata())  # type: ignore[arg-type]
    rows: list[list[tuple[tuple[int, int, int], tuple[int, int, int]]]] = []
    for y in range(0, height, 2):
        row: list[tuple[tuple[int, int, int], tuple[int, int, int]]] = []
        for x in range(width):
            top = pixels[y * width + x]
            bot = pixels[(y + 1) * width + x]
            row.append((top, bot))
        rows.append(row)
    return rows


def _make_fallback_strips(
    message: str, width: int, height: int, is_error: bool = False
) -> list[Strip]:
    border_color = "#ff5555" if is_error else "#30363d"
    icon_color = "#ff5555" if is_error else "#58a6ff"
    icon = "" if is_error else ""
    msg_color = "#ff8080" if is_error else "#8b949e"

    top_segs = [
        Segment("╭", Style.parse(border_color)),
        Segment("─" * (width - 2), Style.parse(border_color)),
        Segment("╮", Style.parse(border_color)),
    ]
    bot_segs = [
        Segment("╰", Style.parse(border_color)),
        Segment("─" * (width - 2), Style.parse(border_color)),
        Segment("╯", Style.parse(border_color)),
    ]
    empty_segs = [
        Segment("│", Style.parse(border_color)),
        Segment(" " * (width - 2)),
        Segment("│", Style.parse(border_color)),
    ]

    def center_line(text: str, style: str) -> list[Segment]:
        pad = max(0, (width - 2 - len(text)) // 2)
        left = pad
        right = width - 2 - len(text) - left
        return [
            Segment("│", Style.parse(border_color)),
            Segment(" " * left),
            Segment(text, Style.parse(style)),
            Segment(" " * right),
            Segment("│", Style.parse(border_color)),
        ]

    strips: list[Strip] = []
    if height < 3:
        truncated = message[:width]
        strips.append(Strip([Segment(truncated, Style.parse(msg_color))]))
        return strips

    mid = height // 2
    for row in range(height):
        if row == 0:
            strips.append(Strip(top_segs))
        elif row == height - 1:
            strips.append(Strip(bot_segs))
        elif row == mid - 1:
            strips.append(Strip(center_line(icon, icon_color)))
        elif row == mid:
            strips.append(Strip(center_line(message, msg_color)))
        else:
            strips.append(Strip(empty_segs))
    return strips


class RigiImage(Widget):
    def __init__(
        self,
        source: str | Path | bytes | None = None,
        *,
        protocol: TerminalImageProtocol | None = None,
        width: int | None = None,
        height: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._source = source
        self._protocol = protocol or detect_image_protocol()
        self._target_width = width
        self._target_height = height
        self._pil_img: PILImage.Image | None = None
        self._rendered_lines: list[Strip] | None = None
        self._raw_escape: str | None = None
        self._error: str | None = None
        self._prepared_size: tuple[int, int] | None = None

    def on_mount(self) -> None:
        if self._source is not None:
            self.load(self._source)

    def load(self, source: str | Path | bytes) -> None:
        self._rendered_lines = None
        self._raw_escape = None
        self._prepared_size = None
        if not _PIL_AVAILABLE:
            self._error = "no_pillow"
            self.refresh()
            return
        try:
            if isinstance(source, bytes):
                self._pil_img = PILImage.open(io.BytesIO(source))
            else:
                self._pil_img = PILImage.open(Path(source))
            self._pil_img.load()
            self._error = None
        except Exception as exc:
            self._pil_img = None
            self._error = str(exc)
        self.refresh()

    def _prepare(self, cell_width: int, cell_height: int) -> None:
        if self._pil_img is None:
            return
        if self._prepared_size == (cell_width, cell_height):
            return
        self._prepared_size = (cell_width, cell_height)
        self._rendered_lines = None
        self._raw_escape = None

        img = self._pil_img.copy()
        target_w = self._target_width or cell_width
        target_h = (self._target_height or cell_height) * 2
        img.thumbnail((target_w, target_h), PILImage.Resampling.LANCZOS)

        if self._protocol == TerminalImageProtocol.BLOCKS:
            self._rendered_lines = self._to_block_strips(img)
        elif self._protocol == TerminalImageProtocol.KITTY:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self._raw_escape = _encode_kitty(
                buf.getvalue(), cols=img.width, rows=(img.height + 1) // 2
            )
        elif self._protocol == TerminalImageProtocol.ITERM2:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self._raw_escape = _encode_iterm2(buf.getvalue(), img.width, img.height)
        elif self._protocol == TerminalImageProtocol.SIXEL:
            self._raw_escape = _encode_sixel(img)

    def _to_block_strips(self, img: PILImage.Image) -> list[Strip]:
        rows = _render_blocks(img)
        return [
            Strip(
                [
                    Segment(
                        "▀",
                        Style.from_color(
                            color=RichColor.from_rgb(top[0], top[1], top[2]),
                            bgcolor=RichColor.from_rgb(bot[0], bot[1], bot[2]),
                        ),
                    )
                    for top, bot in row
                ]
            )
            for row in rows
        ]

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return self._target_width or min(container.width, 80)

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        if self._target_height:
            return self._target_height
        if self._pil_img:
            ratio = self._pil_img.height / max(self._pil_img.width, 1)
            return max(1, int(width * ratio / 2))
        return 5

    def render_line(self, y: int) -> Strip:
        w, h = self.size.width, self.size.height

        if self._error == "no_pillow":
            fallback = _make_fallback_strips("pip install Pillow", w, h)
            return fallback[y] if y < len(fallback) else Strip([])

        if self._error:
            msg = self._error[: w - 4] if len(self._error) > w - 4 else self._error
            fallback = _make_fallback_strips(msg, w, h, is_error=True)
            return fallback[y] if y < len(fallback) else Strip([])

        if not _PIL_AVAILABLE or self._pil_img is None:
            fallback = _make_fallback_strips("No image loaded", w, h)
            return fallback[y] if y < len(fallback) else Strip([])

        self._prepare(w, h)

        if self._raw_escape is not None:
            if y == 0:
                return Strip([Segment(self._raw_escape, Style.null())])
            return Strip([])

        if self._rendered_lines is not None and y < len(self._rendered_lines):
            return self._rendered_lines[y]

        return Strip([])
