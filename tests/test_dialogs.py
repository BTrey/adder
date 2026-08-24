"""Tests for the format dialog and the decimal places dialog."""

from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Label, RadioButton, RadioSet

from adder.config import Palette
from adder.dialogs import FormatScreen, PlacesScreen
from adder.formats import CHOICES, DEFAULT_PLACES, FORMATS, Fixed

SIZE = (60, 20)


class DialogApp(App[None]):
    """An app that opens one dialog and keeps its result."""

    def __init__(self, screen_to_show: FormatScreen | PlacesScreen) -> None:
        self.screen_to_show = screen_to_show
        self.result: Any = "not set"
        super().__init__()

    def get_theme_variable_defaults(self) -> dict[str, str]:
        """Publish the palette, as the real app does."""
        return {f"adder-{key}": color for key, color in Palette().colors.items()}

    def on_mount(self) -> None:
        self.push_screen(self.screen_to_show, self._done)

    def _done(self, result: Any) -> None:
        self.result = result


async def test_the_format_dialog_lists_every_choice() -> None:
    app = DialogApp(FormatScreen(FORMATS["general"]))
    async with app.run_test(size=SIZE):
        buttons = app.screen.query_one(RadioSet).query(RadioButton)
        labels = [str(button.label) for button in buttons]
        assert labels == [choice.label for choice in CHOICES]


async def test_the_dialog_starts_on_the_format_in_use() -> None:
    app = DialogApp(FormatScreen(FORMATS["currency"]))
    async with app.run_test(size=SIZE):
        assert app.screen.query_one(RadioSet).pressed_index == 1


async def test_a_specific_format_starts_on_the_specific_choice() -> None:
    app = DialogApp(FormatScreen(Fixed(5)))
    async with app.run_test(size=SIZE):
        assert app.screen.query_one(RadioSet).pressed_index == 3


async def test_the_decimal_format_starts_on_the_decimal_choice() -> None:
    app = DialogApp(FormatScreen(Fixed(DEFAULT_PLACES)))
    async with app.run_test(size=SIZE):
        assert app.screen.query_one(RadioSet).pressed_index == 2


async def test_ok_returns_the_chosen_key() -> None:
    app = DialogApp(FormatScreen(FORMATS["general"]))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click("#choice-currency")
        await pilot.click("#ok")
        await pilot.pause()
        assert app.result == "currency"


async def test_cancel_returns_nothing() -> None:
    app = DialogApp(FormatScreen(FORMATS["general"]))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click("#choice-currency")
        await pilot.click("#cancel")
        await pilot.pause()
        assert app.result is None


async def test_escape_cancels_the_format_dialog() -> None:
    app = DialogApp(FormatScreen(FORMATS["general"]))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("escape")
        await pilot.pause()
        assert app.result is None


async def test_the_places_dialog_starts_on_the_places_in_use() -> None:
    app = DialogApp(PlacesScreen(4))
    async with app.run_test(size=SIZE):
        assert app.screen.query_one(Input).value == "4"


async def test_the_places_dialog_returns_the_number() -> None:
    app = DialogApp(PlacesScreen(2))
    async with app.run_test(size=SIZE) as pilot:
        app.screen.query_one(Input).value = "5"
        await pilot.click("#ok")
        await pilot.pause()
        assert app.result == 5


async def test_the_places_dialog_reports_a_bad_number_and_stays_open() -> None:
    app = DialogApp(PlacesScreen(2))
    async with app.run_test(size=SIZE) as pilot:
        app.screen.query_one(Input).value = "twelve"
        await pilot.click("#ok")
        await pilot.pause()
        assert app.result == "not set"
        assert "whole number" in str(app.screen.query_one("#message", Label).content)


async def test_the_places_dialog_reports_a_number_out_of_range() -> None:
    app = DialogApp(PlacesScreen(2))
    async with app.run_test(size=SIZE) as pilot:
        app.screen.query_one(Input).value = "99"
        await pilot.click("#ok")
        await pilot.pause()
        assert app.result == "not set"
        assert "0 to 10" in str(app.screen.query_one("#message", Label).content)


async def test_cancel_closes_the_places_dialog() -> None:
    app = DialogApp(PlacesScreen(2))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click("#cancel")
        await pilot.pause()
        assert app.result is None


async def test_enter_accepts_the_places_dialog() -> None:
    app = DialogApp(PlacesScreen(2))
    async with app.run_test(size=SIZE) as pilot:
        app.screen.query_one(Input).value = "3"
        await pilot.press("enter")
        await pilot.pause()
        assert app.result == 3


async def test_the_dialog_has_an_ok_and_a_cancel_button() -> None:
    app = DialogApp(FormatScreen(FORMATS["general"]))
    async with app.run_test(size=SIZE):
        buttons = app.screen.query(Button)
        assert [str(button.label) for button in buttons] == ["OK", "Cancel"]
        assert isinstance(app.screen.query_one("#ok", Button), Button)


async def test_the_base_dialog_has_no_accept_of_its_own() -> None:
    """Every dialog must say what OK does."""
    import pytest

    from adder.dialogs import DialogScreen

    with pytest.raises(NotImplementedError):
        DialogScreen[None]().accept()


async def test_the_keyboard_can_choose_and_accept() -> None:
    """Arrow to a choice, press space to select it, tab to OK, press enter."""
    app = DialogApp(FormatScreen(FORMATS["general"]))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("down", "space", "tab", "enter")
        await pilot.pause()
        assert app.result == "currency"
