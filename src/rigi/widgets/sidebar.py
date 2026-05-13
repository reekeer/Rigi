from __future__ import annotations

from textual.app import ComposeResult
from textual.events import Click, MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label

from rigi.core.types import SubtabDef, TabDef


class _VerticalResizeHandle(Widget):
    ALLOW_SELECT = False

    def __init__(self, target_id: str) -> None:
        super().__init__()
        self._target_id = target_id
        self._drag_x: int | None = None
        self._drag_w: int | None = None

    def render(self) -> str:
        return "│" * self.size.height

    def on_mouse_down(self, event: MouseDown) -> None:
        self.capture_mouse()
        self._drag_x = event.screen_x
        try:
            self._drag_w = self.app.query_one(f"#{self._target_id}").size.width
        except Exception:
            pass

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._drag_x is None or self._drag_w is None:
            return
        delta = event.screen_x - self._drag_x
        new_w = max(10, self._drag_w + delta)
        try:
            self.app.query_one(f"#{self._target_id}").styles.width = new_w
        except Exception:
            pass

    def on_mouse_up(self, _: MouseUp) -> None:
        self.release_mouse()
        self._drag_x = None
        self._drag_w = None


class _MainTabClicked(Message):
    def __init__(self, tab_idx: int) -> None:
        super().__init__()
        self.tab_idx = tab_idx


class _SubItemClicked(Message):
    def __init__(self, path: list[int]) -> None:
        super().__init__()
        self.path = list(path)


class _SubItemToggle(Message):
    def __init__(self, path: list[int], expand_all: bool = False) -> None:
        super().__init__()
        self.path = list(path)
        self.expand_all = expand_all


class _MainNavItem(Widget):
    can_focus = False

    def __init__(self, tab: TabDef, idx: int) -> None:
        super().__init__()
        self._tab = tab
        self._idx = idx

    def compose(self) -> ComposeResult:
        icon = f"{self._tab.icon} " if self._tab.icon else ""
        key_hint = f"[dim]{self._tab.key}[/dim] " if self._tab.key else ""
        yield Label(f"{key_hint}{icon}{self._tab.name}")

    def set_active(self, active: bool) -> None:
        self.set_class(active, "--active")

    def on_click(self) -> None:
        self.post_message(_MainTabClicked(self._idx))
        self.app.set_focus(None)


class _MainNav(Widget):
    def __init__(self) -> None:
        super().__init__(id="main-nav")
        self._tabs: list[TabDef] = []
        self._active_idx: int = 0

    def set_tabs(self, tabs: list[TabDef]) -> None:
        self._tabs = tabs
        self._rebuild()

    def set_active(self, idx: int) -> None:
        self._active_idx = idx
        for item in self.query(_MainNavItem):
            item.set_active(item._idx == idx)

    def _rebuild(self) -> None:
        self.remove_children()
        for i, tab in enumerate(self._tabs):
            item = _MainNavItem(tab, i)
            item.set_active(i == self._active_idx)
            self.mount(item)


class _SubNavNamePart(Widget):
    can_focus = False

    def __init__(self, sub: SubtabDef, path: list[int], depth: int) -> None:
        super().__init__()
        self._sub = sub
        self._path = list(path)
        self._depth = depth

    def compose(self) -> ComposeResult:
        indent = "  " * self._depth
        yield Label(f"{indent}● {self._sub.name}")

    def on_click(self, event: Click) -> None:
        event.stop()
        self.app.set_focus(None)
        if self._sub.widget_factory or not self._sub.children:
            self.post_message(_SubItemClicked(self._path))
        else:
            self.post_message(_SubItemToggle(self._path, event.shift))


class _SubNavArrowPart(Widget):
    can_focus = False

    def __init__(self, path: list[int], expanded: bool) -> None:
        super().__init__()
        self._path = list(path)
        self._expanded = expanded

    def compose(self) -> ComposeResult:
        icon = "▼" if self._expanded else "▶"
        yield Label(f" {icon}")

    def on_click(self, event: Click) -> None:
        event.stop()
        self.app.set_focus(None)
        self.post_message(_SubItemToggle(self._path, event.shift))


class _SubNavItem(Widget):
    can_focus = False

    def __init__(self, sub: SubtabDef, path: list[int], depth: int, expanded: bool) -> None:
        super().__init__()
        self._sub = sub
        self._path = list(path)
        self._depth = depth
        self._expanded = expanded

    def compose(self) -> ComposeResult:
        yield _SubNavNamePart(self._sub, self._path, self._depth)
        if self._sub.children:
            yield _SubNavArrowPart(self._path, self._expanded)

    def set_active(self, active: bool) -> None:
        self.set_class(active, "--active")


class _SubNav(Widget):
    def __init__(self) -> None:
        super().__init__(id="sub-nav")
        self._tab: TabDef | None = None
        self._tab_idx: int = 0
        self._active_path: list[int] = []
        self._expanded: set[tuple[int, ...]] = set()
        self.display = False

    def set_tab(
        self,
        tab: TabDef | None,
        tab_idx: int = 0,
        active_path: list[int] | None = None,
    ) -> None:
        self._tab = tab
        self._tab_idx = tab_idx
        self._active_path = list(active_path or [])
        self._expanded = set()
        self.display = bool(tab and tab.subtabs)
        if self.is_mounted:
            self._rebuild()

    def set_active_path(self, path: list[int]) -> None:
        self._active_path = list(path)
        for item in self.query(_SubNavItem):
            item.set_active(item._path == path)

    def resolve(self, path: list[int]) -> SubtabDef | None:
        if not self._tab or not path:
            return None
        try:
            node = self._tab.subtabs[path[0]]
            for idx in path[1:]:
                node = node.children[idx]
            return node
        except (IndexError, AttributeError):
            return None

    def get_flat_visible(self) -> list[list[int]]:
        result: list[list[int]] = []
        if self._tab:
            for i, sub in enumerate(self._tab.subtabs):
                self._collect_visible(sub, [i], result)
        return result

    def _collect_visible(self, sub: SubtabDef, path: list[int], result: list[list[int]]) -> None:
        result.append(path)
        if tuple(path) in self._expanded:
            for j, child in enumerate(sub.children):
                self._collect_visible(child, path + [j], result)

    def _rebuild(self) -> None:
        self.remove_children()
        if self._tab is None:
            return
        for i, sub in enumerate(self._tab.subtabs):
            self._mount_subtree(sub, [i], 0)

    def _mount_subtree(self, sub: SubtabDef, path: list[int], depth: int) -> None:
        expanded = tuple(path) in self._expanded
        item = _SubNavItem(sub, path, depth, expanded)
        item.set_active(path == self._active_path)
        self.mount(item)
        if expanded:
            for j, child in enumerate(sub.children):
                self._mount_subtree(child, path + [j], depth + 1)

    def on__sub_item_toggle(self, event: _SubItemToggle) -> None:
        event.stop()
        key = tuple(event.path)
        if event.expand_all:
            sub = self.resolve(event.path)
            if sub:
                self._expand_recursive(key, sub)
        elif key in self._expanded:
            self._expanded.discard(key)
        else:
            self._expanded.add(key)
        self._rebuild()

    def _expand_recursive(self, key: tuple[int, ...], sub: SubtabDef) -> None:
        self._expanded.add(key)
        for j, child in enumerate(sub.children):
            child_key = key + (j,)
            self._expand_recursive(child_key, child)

    def on_mount(self) -> None:
        self._rebuild()


class Sidebar(Widget):
    class NavigationChanged(Message):
        def __init__(self, tab_idx: int, subtab_path: list[int]) -> None:
            super().__init__()
            self.tab_idx = tab_idx
            self.subtab_path = list(subtab_path)

    def __init__(self) -> None:
        super().__init__()
        self._tabs: list[TabDef] = []
        self._active_tab: int = 0
        self._active_path: list[int] = []
        self._nav_level: str = "tab"

    def compose(self) -> ComposeResult:
        yield _MainNav()
        yield _VerticalResizeHandle("main-nav")
        yield _SubNav()

    def on_mount(self) -> None:
        main = self.query_one(_MainNav)
        main.set_tabs(self._tabs)
        if self._tabs:
            self.query_one(_SubNav).set_tab(self._tabs[0], 0)

    def set_tabs(self, tabs: list[TabDef]) -> None:
        self._tabs = tabs
        if not self.is_mounted:
            return
        main = self.query_one(_MainNav)
        main.set_tabs(tabs)
        tab = tabs[0] if tabs else None
        self.query_one(_SubNav).set_tab(tab, 0)

    def on__main_tab_clicked(self, event: _MainTabClicked) -> None:
        event.stop()
        idx = event.tab_idx
        self._active_tab = idx
        self._active_path = []
        self._nav_level = "tab"
        self.query_one(_MainNav).set_active(idx)
        tab = self._tabs[idx] if idx < len(self._tabs) else None
        self.query_one(_SubNav).set_tab(tab, idx, [])
        self.post_message(Sidebar.NavigationChanged(idx, []))

    def on__sub_item_clicked(self, event: _SubItemClicked) -> None:
        event.stop()
        path = event.path
        sub_nav = self.query_one(_SubNav)
        sub_nav.set_active_path(path)
        self._active_path = list(path)
        self._nav_level = "subtab"
        self.post_message(Sidebar.NavigationChanged(self._active_tab, path))

    def navigate(self, direction: int) -> None:
        if not self._tabs:
            return
        sub_nav = self.query_one(_SubNav)

        if self._nav_level == "tab":
            new_tab = max(0, min(len(self._tabs) - 1, self._active_tab + direction))
            if new_tab == self._active_tab:
                return
            self._active_tab = new_tab
            self._active_path = []
            self.query_one(_MainNav).set_active(new_tab)
            tab_or_none: TabDef | None = self._tabs[new_tab] if new_tab < len(self._tabs) else None
            sub_nav.set_tab(tab_or_none, new_tab, [])
            self.post_message(Sidebar.NavigationChanged(new_tab, []))
        else:
            if not self._active_path:
                return
            tab = self._tabs[self._active_tab] if self._active_tab < len(self._tabs) else None
            if tab is None:
                return
            if len(self._active_path) == 1:
                siblings = tab.subtabs
            else:
                parent = sub_nav.resolve(self._active_path[:-1])
                siblings = parent.children if parent else []
            if not siblings:
                return
            current_idx = self._active_path[-1]
            new_idx = max(0, min(len(siblings) - 1, current_idx + direction))
            if new_idx == current_idx:
                return
            self._active_path = self._active_path[:-1] + [new_idx]
            sub_nav.set_active_path(self._active_path)
            self.post_message(Sidebar.NavigationChanged(self._active_tab, self._active_path))

    def navigate_right(self) -> None:
        if not self._tabs:
            return
        sub_nav = self.query_one(_SubNav)

        if self._nav_level == "tab":
            tab = self._tabs[self._active_tab] if self._active_tab < len(self._tabs) else None
            if tab and tab.subtabs:
                self._nav_level = "subtab"
                self._active_path = [0]
                sub_nav.set_tab(tab, self._active_tab, [0])
                self.post_message(Sidebar.NavigationChanged(self._active_tab, [0]))
        else:
            current = sub_nav.resolve(self._active_path)
            if current and current.children:
                child_path = self._active_path + [0]
                sub_nav._expanded.add(tuple(self._active_path))
                sub_nav._active_path = list(child_path)
                sub_nav._rebuild()
                self._active_path = child_path
                self.post_message(Sidebar.NavigationChanged(self._active_tab, child_path))

    def navigate_left(self) -> None:
        if self._nav_level != "subtab":
            return
        sub_nav = self.query_one(_SubNav)

        if len(self._active_path) > 1:
            parent = self._active_path[:-1]
            self._active_path = parent
            sub_nav.set_active_path(parent)
            self.post_message(Sidebar.NavigationChanged(self._active_tab, parent))
        else:
            self._nav_level = "tab"
            self._active_path = []
            sub_nav.set_active_path([])
            self.post_message(Sidebar.NavigationChanged(self._active_tab, []))

    def jump_to_tab_by_key(self, key: str) -> bool:
        for t_idx, tab in enumerate(self._tabs):
            if tab.key == key:
                self._active_tab = t_idx
                self._active_path = []
                self._nav_level = "tab"
                self.query_one(_MainNav).set_active(t_idx)
                self.query_one(_SubNav).set_tab(tab, t_idx, [])
                self.post_message(Sidebar.NavigationChanged(t_idx, []))
                return True
        return False
