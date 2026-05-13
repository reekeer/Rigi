"""Tests for Checkbox widget."""

import pytest
from textual.app import App

from rigi.widgets.checkbox import Checkbox


@pytest.mark.asyncio
async def test_checkbox_initial_value():
    class TestApp(App[None]):
        def compose(self):
            yield Checkbox("Test", value=True)

    app = TestApp()
    async with app.run_test() as _:
        cb = app.query_one(Checkbox)
        assert cb.value is True


@pytest.mark.asyncio
async def test_checkbox_toggle():
    class TestApp(App[None]):
        def compose(self):
            yield Checkbox("Test", value=False)

    app = TestApp()
    async with app.run_test() as _:
        cb = app.query_one(Checkbox)
        assert cb.value is False
        cb.toggle()
        assert cb.value is True
