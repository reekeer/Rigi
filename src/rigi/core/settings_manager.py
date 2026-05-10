from __future__ import annotations

from collections.abc import Iterable
from typing import Callable

from rigi.screens.settings import RigiSettingDef


class Setting:
    """Single setting entry. Category is supplied by the SettingsPage it belongs to."""

    def __init__(
        self,
        label: str,
        description: str = "",
        value_fn: Callable[[], str] | None = None,
        action_fn: Callable[[], None] | None = None,
        action_label: str = "Change",
        write_fn: Callable[[str], None] | None = None,
        checkbox_fn: Callable[[], bool] | None = None,
        toggle_fn: Callable[[], None] | None = None,
    ) -> None:
        self.label = label
        self.description = description
        self.value_fn = value_fn
        self.action_fn = action_fn
        self.action_label = action_label
        self.write_fn = write_fn
        self.checkbox_fn = checkbox_fn
        self.toggle_fn = toggle_fn

    def _to_def(self, category: str) -> RigiSettingDef:
        return RigiSettingDef(
            category=category,
            label=self.label,
            description=self.description,
            value_fn=self.value_fn,
            action_fn=self.action_fn,
            action_label=self.action_label,
            write_fn=self.write_fn,
            checkbox_fn=self.checkbox_fn,
            toggle_fn=self.toggle_fn,
        )


class SettingsPage:
    """A named page in the settings screen."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._defs: list[RigiSettingDef] = []

    @property
    def settings(self) -> list[RigiSettingDef]:
        return self._defs

    @settings.setter
    def settings(self, value: Iterable[Setting]) -> None:
        self._defs = [s._to_def(self.name) for s in value]


class SettingsManager:
    """Manages user-defined settings pages.

    Usage::

        general = app.settings.add_page("General")
        general.settings = [
            Setting("Theme", description="Color theme", value_fn=lambda: app._theme.name),
            Setting("Verbose", checkbox_fn=lambda: verbose, toggle_fn=toggle_verbose),
        ]
    """

    def __init__(self) -> None:
        self._pages: list[SettingsPage] = []

    def add_page(self, name: str) -> SettingsPage:
        page = SettingsPage(name)
        self._pages.append(page)
        return page

    def all_defs(self) -> list[RigiSettingDef]:
        defs: list[RigiSettingDef] = []
        for page in self._pages:
            defs.extend(page._defs)
        return defs
