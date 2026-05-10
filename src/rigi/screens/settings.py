"""RigiSettingsScreen — modal settings panel."""

from __future__ import annotations

import logging
from typing import Callable

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Input, Label

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
    ) -> None:
        self.category = category
        self.label = label
        self.description = description
        self.value_fn = value_fn
        self.action_fn = action_fn
        self.action_label = action_label
        self.write_fn = write_fn
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


class _CategoryClicked(Message):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name


class _CategoryRow(Widget):
    DEFAULT_CSS = """
    _CategoryRow {
        height: 2; width: 100%; padding: 0 2;
        color: #6e7681; background: transparent; content-align: left middle;
    }
    _CategoryRow:hover { color: #c9d1d9; }
    _CategoryRow.--active { color: #58a6ff; border-left: thick #58a6ff; text-style: bold; }
    """
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
    DEFAULT_CSS = """
    _ActionButton {
        width: 10; height: 1; content-align: center middle;
        background: #21262d; color: #c9d1d9; padding: 0 1;
    }
    _ActionButton:hover { background: #30363d; color: white; }
    """
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
    DEFAULT_CSS = """
    _ValueRow { layout: horizontal; height: 1; width: 100%; background: transparent; }
    _ValueRow ._val-lbl { width: 1fr; color: #58a6ff; height: 1; }
    """

    def __init__(self, setting: RigiSettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Label(self._setting.get_value(), classes="_val-lbl")
        if self._setting.action_fn:
            yield _ActionButton(self._setting.action_label, self._setting.action_fn)


class _SettingInput(Input):
    DEFAULT_CSS = """
    _SettingInput {
        width: 28; height: 1; border: solid #30363d;
        background: #161b22; color: #e6edf3; padding: 0 1; margin-top: 1;
    }
    _SettingInput:focus { border: solid #58a6ff; }
    """

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


class _SettingItem(Widget):
    DEFAULT_CSS = """
    _SettingItem {
        height: auto; width: 100%; padding: 0 0 1 0;
        border-bottom: solid #21262d; margin-bottom: 1; background: transparent;
    }
    _SettingItem ._s-label { color: #c9d1d9; text-style: bold; height: 1; }
    _SettingItem ._s-desc { color: #6e7681; height: 1; }
    """

    def __init__(self, setting: RigiSettingDef) -> None:
        super().__init__()
        self._setting = setting

    def compose(self) -> ComposeResult:
        yield Label(self._setting.label, classes="_s-label")
        if self._setting.description:
            yield Label(self._setting.description, classes="_s-desc")
        if self._setting.write_fn is not None or (
            self._setting.value_fn is not None and self._setting.action_fn is None
        ):
            yield _SettingInput(self._setting)
        elif self._setting.value_fn or self._setting.action_fn:
            yield _ValueRow(self._setting)


class _SettingsContent(Widget):
    DEFAULT_CSS = """
    _SettingsContent { width: 1fr; height: 100%; padding: 1 2; overflow-y: auto; background: transparent; }
    _SettingsContent ._cat-title { color: #58a6ff; text-style: bold; height: 1; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield from []


class RigiSettingsScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    RigiSettingsScreen { align: center middle; background: transparent; }
    #s-outer {
        width: 90%; height: 85%;
        border: round #30363d; border-title-color: #c9d1d9;
        background: #0d1117; layout: vertical;
    }
    #s-titlebar {
        height: 2; padding: 0 2;
        border-bottom: solid #21262d; background: transparent; content-align: left middle;
    }
    #s-body { layout: horizontal; height: 1fr; background: transparent; }
    #s-categories {
        width: 22; height: 100%; border-right: solid #21262d;
        padding: 1 0; overflow-y: auto; background: transparent;
    }
    """

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
                yield Label("[dim]ESC to close[/dim]")
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
