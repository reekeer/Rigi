from __future__ import annotations

from rigi import (
    Command,
    CommandArg,
    RigiApp,
    RigiTheme,
    StatusItem,
    SubtabDef,
    TabDef,
    ThemeDark,
    ThemeLight,
    ThemeMonokai,
    ThemeNord,
)
from rigi.commands.registry import CommandRegistry
from rigi.widgets.hamburger_menu import RigiMenuItemData
from rigi.widgets.settings_screen import RigiSettingDef


def test_import() -> None:
    assert RigiApp is not None


def test_theme_to_css() -> None:
    css = ThemeDark.to_css()
    assert "RigiBorderFrame" in css
    assert ThemeDark.name == "dark"


def test_all_themes_have_css() -> None:
    for theme in [ThemeDark, ThemeLight, ThemeMonokai, ThemeNord]:
        css = theme.to_css()
        assert isinstance(css, str)
        assert len(css) > 0


def test_tab_def() -> None:
    tab = TabDef(name="Home", key="1", icon="")
    assert tab.name == "Home"
    sub = tab.add_subtab("Sub", icon="")
    assert sub.name == "Sub"
    assert len(tab.subtabs) == 1


def test_subtab_children() -> None:
    parent = SubtabDef(name="Parent")
    child = parent.add_subtab("Child")
    assert len(parent.children) == 1
    assert child.name == "Child"


def test_command_arg_default_type() -> None:
    arg = CommandArg(name="foo")
    assert arg.arg_type is str
    assert arg.required is False


def test_command_registry() -> None:
    reg = CommandRegistry()
    cmd = Command(name="test", help="Test command", aliases=["t"])
    reg.register(cmd)
    assert reg.get("test") is cmd
    assert reg.get("t") is cmd
    assert reg.get("missing") is None


def test_command_completions() -> None:
    reg = CommandRegistry()
    reg.register(Command(name="help"))
    reg.register(Command(name="quit"))
    reg.register(Command(name="clear"))

    hints = reg.completions("h")
    assert "help" in hints

    hints_all = reg.completions("")
    assert "help" in hints_all
    assert "quit" in hints_all


def test_setting_def_get_set() -> None:
    s = RigiSettingDef(
        category="Test",
        label="Key",
        value_fn=lambda: "default",
    )
    assert s.get_value() == "default"
    s.set_value("custom")
    assert s.get_value() == "custom"


def test_setting_def_write_fn() -> None:
    written: list[str] = []
    s = RigiSettingDef(
        category="Test",
        label="Key",
        write_fn=written.append,
    )
    s.set_value("hello")
    assert written == ["hello"]


def test_menu_item_data() -> None:
    item = RigiMenuItemData(label="Option", checked=True)
    assert item.label == "Option"
    assert item.checked is True
    assert item.submenu is None
    assert item.callback is None


def test_rigi_app_init() -> None:
    app = RigiApp(name="testapp", version="0.0.1", description="test")
    assert app._prog_name == "testapp"
    assert app._version == "0.0.1"


def test_rigi_app_add_tab() -> None:
    app = RigiApp(name="testapp")
    tab = app.add_tab(TabDef(name="Dashboard", key="1"))
    assert tab in app._rigi_tabs


def test_rigi_app_command_decorator() -> None:
    app = RigiApp(name="testapp")
    calls: list[str] = []

    @app.command("greet", help="Say hi")
    async def greet(_app: RigiApp, **_: object) -> None:  # pyright: ignore[reportUnusedFunction]
        calls.append("hi")

    assert app._cmd_registry.get("greet") is not None


def test_status_item() -> None:
    item = StatusItem(
        key="time",
        label="Time",
        value_fn=lambda: "12:00",
        refresh_interval=1.0,
    )
    assert item.value_fn() == "12:00"


def test_custom_theme() -> None:
    theme = RigiTheme(
        name="custom",
        border="#ff0000",
        text="#ffffff",
    )
    css = theme.to_css()
    assert "#ff0000" in css
    assert "custom" in css
