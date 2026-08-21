"""End-to-end tests driven through the Textual Pilot."""

from __future__ import annotations

import pytest
from rich.text import Text
from textual.widgets import Input, Static

from adder.app import AdderApp
from adder.config import Palette

SIZE = (80, 24)


def column_text(app: AdderApp, identifier: str) -> str:
    """Read the plain text of one column."""
    renderable = app.query_one(identifier, Static).content
    assert isinstance(renderable, Text)
    return renderable.plain


async def type_lines(app: AdderApp, pilot: object, *lines: str) -> None:
    """Type each line into the entry field and press Enter."""
    entry = app.query_one("#entry", Input)
    for line in lines:
        entry.value = line
        await app.workers.wait_for_complete()
        entry.post_message(Input.Submitted(entry, line))
        await pilot.pause()  # type: ignore[attr-defined]


async def test_an_operator_line_adds_a_row_and_moves_the_value() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+100")
        assert column_text(app, "#list-text") == "+100"
        assert column_text(app, "#value-text") == "100"
        assert app.session.value == 100.0
        assert app.query_one("#entry", Input).value == ""


async def test_a_running_tape() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "hello", "+ 100", "* 3")
        assert column_text(app, "#list-text") == "hello\n+ 100\n* 3"
        assert column_text(app, "#value-text") == "\n100\n300"
        assert app.session.value == 300.0


async def test_a_variable_is_assigned_then_used() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "$var1 5", "+ $var1")
        assert column_text(app, "#list-text") == "$var1 5\n+ $var1"
        assert column_text(app, "#value-text") == "\n5"
        assert app.session.value == 5.0


async def test_clear_empties_both_columns() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 100", "@clear")
        assert column_text(app, "#list-text") == ""
        assert column_text(app, "#value-text") == ""
        assert app.session.value == 0.0


async def test_an_error_row_keeps_the_value() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 10", "/ 0")
        assert column_text(app, "#list-text") == "+ 10\n/ 0  division by zero"
        assert column_text(app, "#value-text") == "10\n"
        assert app.session.value == 10.0


async def test_an_empty_line_adds_nothing() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "   ")
        assert app.session.rows == []
        assert column_text(app, "#list-text") == ""


async def test_typing_at_the_keyboard_works() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("plus", "1", "0", "0", "enter")
        assert app.session.value == 100.0
        assert column_text(app, "#value-text") == "100"


@pytest.mark.parametrize(("percent", "expected"), [(25, 20), (50, 40), (75, 60)])
async def test_the_list_column_width_follows_the_flag(percent: int, expected: int) -> None:
    app = AdderApp(width=percent)
    async with app.run_test(size=SIZE):
        assert app.list_column.outer_size.width == expected
        assert app.value_column.outer_size.width == SIZE[0] - expected


async def test_a_width_of_zero_hides_the_list_column() -> None:
    app = AdderApp(width=0)
    async with app.run_test(size=SIZE):
        assert app.list_column.display is False
        assert app.value_column.outer_size.width == SIZE[0]


async def test_a_width_of_one_hundred_hides_the_value_column() -> None:
    app = AdderApp(width=100)
    async with app.run_test(size=SIZE):
        assert app.value_column.display is False
        assert app.list_column.outer_size.width == SIZE[0]


async def test_the_palette_reaches_the_widgets() -> None:
    palette = Palette(background="#101010", border="#202020", input="#303030")
    app = AdderApp(palette=palette)
    async with app.run_test(size=SIZE):
        assert app.screen.styles.background.hex.lower() == "#101010"
        assert app.list_column.styles.border_top[1].hex.lower() == "#202020"
        assert app.query_one("#entry", Input).styles.color.hex.lower() == "#303030"
        assert app.theme == "adder"


async def test_the_right_column_follows_the_left_column_scroll() -> None:
    app = AdderApp()
    async with app.run_test(size=(80, 12)) as pilot:
        await type_lines(app, pilot, *[f"+ {number}" for number in range(40)])
        assert app.list_column.scroll_y > 0
        assert app.value_column.scroll_y == app.list_column.scroll_y
        app.list_column.scroll_to(y=0, animate=False)
        await pilot.pause()
        assert app.value_column.scroll_y == 0


async def test_the_panels_are_named() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE):
        assert app.list_column.border_title == "List"
        assert app.value_column.border_title == "Value"
