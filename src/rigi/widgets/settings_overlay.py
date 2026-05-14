"""SettingsOverlay — transparent overlay widget with settings content."""

from __future__ import annotations

import logging
from typing import Callable

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.events import Click, Key, MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label

from rigi.screens.settings import SettingDef

_ui_log = logging.getLogger("rigi.ui")


class _CategoryClicked(Message):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name


class _CategoryRow(Widget):
    can_focus = False

    def __init__(self, name: str) -> None:
        super().__init__()
        self._cat_name = name

    def compose(self) -> ComposeResult:
        yield Label(self._cat_name)

    def set_active(self, v: bool) -> None:
        self.set_class(v, "--active")

    def on_click(self) -> None:
        self.post_message(_CategoryClicked(self._cat_name))


class _ActionButton(Widget):
    can_focus = False

    def __init__(self, label: str, callback: Callable[[], None]) -> None:
        super().__init__()
        self._label = label
        self._callback = callback

    def compose(self) -> ComposeResult:
        yield Label(self._label)

    def on_click(self) -> None:
        self._callback()
        try:
            overlay = self.app.query_one("#rigi-settings-overlay")
            if isinstance(overlay, SettingsOverlay):
                overlay._refresh_content()
        except Exception as e:
            _ui_log.error(f"Error in action button click: {e}", exc_info=True)


class _ValueRow(Widget):
    def __init__(self, setting: SettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Label(self._setting.get_value(), classes="_val-lbl")
        if self._setting.action_fn:
            yield _ActionButton(self._setting.action_label, self._setting.action_fn)


class _SettingInput(Input):
    def __init__(self, setting: SettingDef) -> None:
        super().__init__(value=setting.get_value())
        self._setting = setting
        self.restrict = None

    def _commit(self) -> None:
        self._setting.set_value(self.value)

    def on_blur(self) -> None:
        self._commit()

    @on(Input.Submitted)
    def on_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._commit()
        self.app.set_focus(None)


class _Checkbox(Widget):
    can_focus = True

    class Changed(Message):
        def __init__(self, value: bool) -> None:
            super().__init__()
            self.value = value

    def __init__(self, setting: SettingDef) -> None:
        super().__init__()
        self._setting = setting
        self._checked = setting.get_checked()

    def render(self) -> str:
        return "☑" if self._checked else "☐"

    def on_click(self) -> None:
        self._toggle()

    def on_key(self, event: Key) -> None:
        if event.key in ("space", "enter"):
            self._toggle()
            event.stop()

    def _toggle(self) -> None:
        if self._setting.toggle_fn:
            try:
                self._setting.toggle_fn()
            except Exception as e:
                _ui_log.error(f"Toggle error: {e}", exc_info=True)
        self._checked = self._setting.get_checked()
        self.refresh()
        self.post_message(self.Changed(self._checked))


class _Slider(Widget):
    can_focus = True

    class Changed(Message):
        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value

    def __init__(self, value: int = 50, min_val: int = 0, max_val: int = 100) -> None:
        super().__init__()
        self._value = max(min_val, min(max_val, value))
        self._min = min_val
        self._max = max_val
        self._dragging = False

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int) -> None:
        new = max(self._min, min(self._max, int(v)))
        if new != self._value:
            self._value = new
            self.refresh()
            self.post_message(self.Changed(self._value))

    def render(self) -> Text:
        w = max(3, self.size.width)
        frac = (self._value - self._min) / max(1, self._max - self._min)
        thumb = max(0, min(w - 1, int(frac * (w - 1))))
        t = Text()
        t.append("─" * thumb, style="dim #6e7681")
        t.append("●", style="bold #58a6ff")
        t.append("─" * (w - 1 - thumb), style="dim #6e7681")
        return t

    def _set_from_x(self, x: int) -> None:
        w = max(3, self.size.width)
        frac = max(0.0, min(1.0, x / max(1, w - 1)))
        self.value = int(self._min + frac * (self._max - self._min))

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.capture_mouse()
        self._set_from_x(event.x)

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging:
            self._set_from_x(event.x)

    def on_mouse_up(self, _event: MouseUp) -> None:
        self._dragging = False
        self.release_mouse()

    def on_key(self, event: Key) -> None:
        if event.key == "left":
            self.value = self._value - 1
            event.stop()
        elif event.key == "right":
            self.value = self._value + 1
            event.stop()


class _SliderRow(Widget):
    def __init__(self, setting: SettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        try:
            initial = max(0, min(100, int(self._setting.get_value())))
        except (ValueError, TypeError):
            initial = 50
        yield _Slider(value=initial, min_val=0, max_val=100)
        yield Input(value=str(initial), restrict=r"\d*", max_length=3, id="sr-input")

    @on(_Slider.Changed)
    def on_slider_changed(self, event: _Slider.Changed) -> None:
        event.stop()
        try:
            self.query_one("#sr-input", Input).value = str(event.value)
        except Exception:
            pass
        self._setting.set_value(str(event.value))

    @on(Input.Changed, "#sr-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        raw = event.value.strip()
        if raw.isdigit():
            val = max(0, min(100, int(raw)))
            try:
                self.query_one(_Slider).value = val
            except Exception:
                pass

    @on(Input.Submitted, "#sr-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._commit_input()

    def _commit_input(self) -> None:
        try:
            inp = self.query_one("#sr-input", Input)
            raw = inp.value.strip()
            val = max(0, min(100, int(raw))) if raw.isdigit() else 50
            inp.value = str(val)
            self.query_one(_Slider).value = val
            self._setting.set_value(str(val))
        except Exception:
            pass


class _SettingItem(Widget):
    def __init__(self, setting: SettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Label(self._setting.label, classes="_s-label")
        if self._setting.description:
            yield Label(self._setting.description, classes="_s-desc")
        if self._setting.checkbox_fn is not None and self._setting.write_fn is not None:
            yield _Checkbox(self._setting)
            yield _SliderRow(self._setting)
        elif self._setting.checkbox_fn is not None:
            yield _Checkbox(self._setting)
        elif self._setting.write_fn is not None:
            yield _SettingInput(self._setting)
        if (
            (self._setting.value_fn is not None or self._setting.action_fn is not None)
            and self._setting.checkbox_fn is None
            and self._setting.write_fn is None
        ):
            yield _ValueRow(self._setting)


class _SettingsContent(Widget):
    def compose(self) -> ComposeResult:
        yield from []


class SettingsOverlay(Widget):
    can_focus = True

    def __init__(self, settings: list[SettingDef]) -> None:
        super().__init__()
        self._settings = settings
        self._active_category = ""
        self._pending_category = ""
        self._categories: list[str] = []
        seen: set[str] = set()
        for s in settings:
            if s.category not in seen:
                seen.add(s.category)
                self._categories.append(s.category)
        if self._categories:
            self._active_category = self._categories[0]

    def compose(self) -> ComposeResult:
        with Widget(id="s-outer"):
            with Widget(id="s-titlebar"):
                yield Label("Settings", id="s-title-lbl")
                yield Button("×", id="s-close-btn")
            with Widget(id="s-body"):
                with Widget(id="s-categories"):
                    for cat in self._categories:
                        row = _CategoryRow(cat)
                        if cat == self._active_category:
                            row.add_class("--active")
                        yield row
                yield _SettingsContent(id="s-content")

    def on_mount(self) -> None:
        self.query_one("#s-outer").border_title = "⚙  Settings"
        self._render_category(self._active_category)

    @on(Button.Pressed, "#s-close-btn")
    def on_close_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.remove()

    @on(_CategoryClicked)
    def on_category_clicked(self, event: _CategoryClicked) -> None:
        event.stop()
        if event.name == self._active_category:
            return
        self._active_category = event.name
        for row in self.query(_CategoryRow):
            row.set_active(row._cat_name == event.name)
        self._render_category(event.name)

    def _render_category(self, category: str) -> None:
        self._pending_category = category
        settings = [s for s in self._settings if s.category == category]

        async def _do() -> None:
            if self._pending_category != category:
                return
            try:
                content = self.query_one("#s-content", _SettingsContent)
                await content.query("*").remove()
                if self._pending_category != category:
                    return
                await content.mount(Label(category, classes="_cat-title"))
                for s in settings:
                    if self._pending_category != category:
                        return
                    await content.mount(_SettingItem(s))
            except Exception as e:
                _ui_log.error(f"Settings render error: {e}", exc_info=True)

        self.app.run_worker(_do(), name="rigi-settings-render", exclusive=True)

    def _refresh_content(self) -> None:
        self._render_category(self._active_category)

    def on_click(self, event: Click) -> None:
        container = self.query_one("#s-outer")
        if not container.region.contains(event.screen_x, event.screen_y):
            self.remove()
            event.stop()
