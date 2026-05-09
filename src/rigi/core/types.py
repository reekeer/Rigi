from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from textual.widget import Widget


@dataclass
class StatusItem:
    key: str
    label: str
    value_fn: Callable[[], str]
    style: str = "bold white"
    refresh_interval: float = 1.0


@dataclass
class CommandArg:
    name: str
    help: str = ""
    required: bool = False
    default: Any = None
    arg_type: type[Any] = str
    choices: list[str] | None = None
    is_flag: bool = False
    short: str | None = None


@dataclass
class SubtabDef:
    name: str
    widget_factory: Callable[[], Widget] | None = None
    icon: str = ""
    key: str | None = None
    children: list[SubtabDef] = field(default_factory=list)

    def add_subtab(
        self,
        name: str,
        widget_factory: Callable[[], Widget] | None = None,
        icon: str = "",
        key: str | None = None,
    ) -> SubtabDef:
        sub = SubtabDef(name=name, widget_factory=widget_factory, icon=icon, key=key)
        self.children.append(sub)
        return sub


@dataclass
class TabDef:
    name: str
    key: str | None = None
    icon: str = ""
    subtabs: list[SubtabDef] = field(default_factory=list)
    widget_factory: Callable[[], Widget] | None = None

    def add_subtab(
        self,
        name: str,
        widget_factory: Callable[[], Widget] | None = None,
        icon: str = "",
        key: str | None = None,
    ) -> SubtabDef:
        sub = SubtabDef(name=name, widget_factory=widget_factory, icon=icon, key=key)
        self.subtabs.append(sub)
        return sub


@dataclass
class HelpEntry:
    key: str
    description: str
    category: str = "Commands"


HandlerFn = Callable[..., Awaitable[None] | None]
