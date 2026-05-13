from __future__ import annotations

import logging
from typing import Callable

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Switch

_ui_log = logging.getLogger("rigi.ui")


class RigiSettingDef:
    def __init__(
        self,
        category: str,
        label: str,
        description: str = "",
        value_fn: Callable[[], str] | None = None,
        action_fn: Callable[[], None] | None = None,
        action_label: str = "Change",
        write_fn: Callable[[str], None] | None = None,
        checkbox_fn: Callable[[], bool] | None = None,
        toggle_fn: Callable[[], None] | None = None,
    ) -> None:
        self.category = category
        self.label = label
        self.description = description
        self.value_fn = value_fn
        self.action_fn = action_fn
        self.action_label = action_label
        self.write_fn = write_fn
        self.checkbox_fn = checkbox_fn
        self.toggle_fn = toggle_fn
        self._current_value: str | None = None

    def get_value(self) -> str:
        if self._current_value is not None:
            return self._current_value
        if self.value_fn is None:
            return ""
        try:
            return str(self.value_fn())
        except Exception as e:
            _ui_log.error(f"Error getting setting value for {self.label}: {e}", exc_info=True)
            return ""

    def set_value(self, v: str) -> None:
        self._current_value = v
        if self.write_fn:
            try:
                self.write_fn(v)
            except Exception as e:
                _ui_log.error(f"Error setting value for {self.label}: {e}", exc_info=True)

    def get_checked(self) -> bool:
        if self.checkbox_fn is None:
            return False
        try:
            return self.checkbox_fn()
        except Exception as e:
            _ui_log.error(f"Error getting checkbox value for {self.label}: {e}", exc_info=True)
            return False


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
            screen = self.app.screen
            if isinstance(screen, RigiSettingsScreen):
                screen._refresh_content()
        except Exception as e:
            _ui_log.error(f"Error in action button click: {e}", exc_info=True)


class _ValueRow(Widget):
    def __init__(self, setting: RigiSettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Label(self._setting.get_value(), classes="_val-lbl")
        if self._setting.action_fn:
            yield _ActionButton(self._setting.action_label, self._setting.action_fn)


class _SettingInput(Input):
    def __init__(self, setting: RigiSettingDef) -> None:
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


class _SettingSwitch(Widget):
    def __init__(self, setting: RigiSettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Switch(value=self._setting.get_checked(), classes="_s-switch")

    @on(Switch.Changed)
    def on_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if self._setting.toggle_fn:
            try:
                self._setting.toggle_fn()
            except Exception as e:
                _ui_log.error(f"Error toggling setting {self._setting.label}: {e}", exc_info=True)
        # Show/hide sibling input when present
        for sibling in self.siblings:
            if isinstance(sibling, _SettingInput):
                sibling.display = event.value
                if event.value:
                    sibling.focus()


class _SettingItem(Widget):
    def __init__(self, setting: RigiSettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Label(self._setting.label, classes="_s-label")
        if self._setting.description:
            yield Label(self._setting.description, classes="_s-desc")
        if self._setting.checkbox_fn is not None:
            yield _SettingSwitch(self._setting)
        if self._setting.write_fn is not None:
            inp = _SettingInput(self._setting)
            if self._setting.checkbox_fn is not None:
                inp.display = self._setting.get_checked()
            yield inp
        elif self._setting.value_fn is not None or self._setting.action_fn is not None:
            if self._setting.checkbox_fn is None:
                yield _ValueRow(self._setting)


class _SettingsContent(Widget):
    def compose(self) -> ComposeResult:
        yield from []


class RigiSettingsScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(self, settings: list[RigiSettingDef]) -> None:
        super().__init__()
        self._settings = settings
        self._active_category = ""
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
        self.dismiss(None)

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
        content = self.query_one("#s-content", _SettingsContent)
        content.remove_children()
        content.mount(Label(category, classes="_cat-title"))
        for s in self._settings:
            if s.category == category:
                content.mount(_SettingItem(s))

    def _refresh_content(self) -> None:
        self._render_category(self._active_category)
