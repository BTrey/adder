"""End-to-end tests driven through the Textual Pilot."""

from __future__ import annotations

import pytest
from rich.text import Text
from textual.containers import VerticalScroll
from textual.widgets import Input, Static

from adder.app import AdderApp
from adder.config import Palette
from adder.dialogs import FormatScreen, PlacesScreen
from adder.formats import FORMATS, Fixed
from adder.help import HelpScreen

SIZE = (80, 24)


def column_text(app: AdderApp, identifier: str) -> str:
    """Read the plain text of one column, without the padding that carries the stripes."""
    renderable = app.query_one(identifier, Static).content
    assert isinstance(renderable, Text)
    return "\n".join(line.strip() for line in renderable.plain.split("\n"))


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


async def test_zeroize_resets_the_app_to_a_fresh_state() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "$var1 5", "+ $var1", "note", "@zeroize")
        assert column_text(app, "#list-text") == ""
        assert column_text(app, "#value-text") == ""
        assert app.session.value == 0.0
        assert app.session.variables == {}
        await type_lines(app, pilot, "+ $var1")
        assert column_text(app, "#list-text") == "+ $var1  unknown variable: var1"
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


async def test_the_help_command_opens_the_dialog() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@help")
        assert isinstance(app.screen, HelpScreen)
        help_text = app.screen.query_one("#help-text", Static).content
        assert isinstance(help_text, Text)
        assert "Operators" in help_text.plain
        assert "@zeroize" in help_text.plain
        assert app.session.rows == []
        assert app.session.effects == []


async def test_the_help_dialog_closes_and_returns_the_focus() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@help")
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)
        assert app.focused is app.query_one("#entry", Input)
        await type_lines(app, pilot, "+ 7")
        assert app.session.value == 7.0


async def test_a_click_closes_the_help_dialog() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@help")
        await pilot.click("#help-dialog")
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)


async def test_an_effect_with_no_handler_is_ignored() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        app.session.request_effect("not-a-real-effect")
        app.run_effects()
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)
        assert app.session.effects == []


async def test_the_help_dialog_fits_a_wide_terminal() -> None:
    app = AdderApp()
    async with app.run_test(size=(88, 34)) as pilot:
        await type_lines(app, pilot, "@help")
        dialog = app.screen.query_one("#help-dialog", VerticalScroll)
        assert dialog.show_vertical_scrollbar is False
        assert dialog.show_horizontal_scrollbar is False


async def test_a_narrow_terminal_wraps_and_scrolls_the_help() -> None:
    app = AdderApp()
    async with app.run_test(size=(58, 20)) as pilot:
        await type_lines(app, pilot, "@help")
        dialog = app.screen.query_one("#help-dialog", VerticalScroll)
        assert dialog.show_horizontal_scrollbar is False
        assert dialog.show_vertical_scrollbar is True
        await pilot.press("pagedown")
        await pilot.pause()
        assert dialog.scroll_y > 0


async def test_the_help_dialog_uses_the_palette() -> None:
    app = AdderApp(palette=Palette(border="#202020"))
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@help")
        dialog = app.screen.query_one("#help-dialog")
        assert dialog.styles.border_top[1].hex.lower() == "#202020"


STRIPED = Palette(background="#002b36", stripe="#073642")


def background_at(app: AdderApp, x: int, y: int) -> str:
    """The composited background color of one cell of the screen."""
    color = app.screen.get_style_at(x, y).bgcolor
    assert color is not None and color.triplet is not None
    return color.triplet.hex


def row_backgrounds(app: AdderApp, x: int, count: int) -> list[str]:
    """The background color of the first rows of a column, at one column of cells."""
    return [background_at(app, x, y) for y in range(1, count + 1)]


async def test_the_rows_are_striped() -> None:
    app = AdderApp(palette=STRIPED)
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1", "+ 2", "+ 3", "+ 4")
        assert row_backgrounds(app, 2, 4) == ["#002b36", "#073642", "#002b36", "#073642"]


async def test_a_stripe_covers_the_whole_column() -> None:
    app = AdderApp(palette=STRIPED, width=50)
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1", "+ 2")
        list_edge = app.list_column.content_size.width
        value_edge = SIZE[0] - 3
        for x in (2, list_edge, value_edge):
            assert background_at(app, x, 1) == "#002b36"
            assert background_at(app, x, 2) == "#073642"


async def test_a_wider_band_makes_wider_stripes() -> None:
    app = AdderApp(palette=STRIPED, band=2)
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1", "+ 2", "+ 3", "+ 4")
        assert row_backgrounds(app, 2, 4) == ["#002b36", "#002b36", "#073642", "#073642"]


async def test_one_stripe_color_gives_a_plain_background() -> None:
    app = AdderApp(palette=Palette(background="#002b36", stripe="#002b36"))
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1", "+ 2", "+ 3")
        assert set(row_backgrounds(app, 2, 3)) == {"#002b36"}


async def test_a_resize_repads_the_rows() -> None:
    app = AdderApp(palette=STRIPED, width=50)
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1", "+ 2")
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert background_at(app, app.list_column.content_size.width, 2) == "#073642"


async def test_the_format_command_opens_the_dialog() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1.5", "@format")
        assert isinstance(app.screen, FormatScreen)
        assert app.session.rows[-1].text == "+ 1.5"


async def test_choosing_currency_reprints_the_value_column() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1.5", "@format")
        await pilot.click("#choice-currency")
        await pilot.click("#ok")
        await pilot.pause()
        assert column_text(app, "#value-text") == "$1.50"
        assert app.session.value_format is FORMATS["currency"]


async def test_cancel_leaves_the_format_alone() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1.5", "@format")
        await pilot.click("#choice-currency")
        await pilot.click("#cancel")
        await pilot.pause()
        assert column_text(app, "#value-text") == "1.5"
        assert app.session.value_format == FORMATS["general"]


async def test_the_specific_choice_opens_the_places_dialog() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1.5", "@format")
        await pilot.click("#choice-specific")
        await pilot.click("#ok")
        await pilot.pause()
        assert isinstance(app.screen, PlacesScreen)
        app.screen.query_one("#places", Input).value = "4"
        await pilot.click("#ok")
        await pilot.pause()
        assert column_text(app, "#value-text") == "1.5000"
        assert app.session.value_format == Fixed(4)


async def test_cancelling_the_places_dialog_leaves_the_format_alone() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "+ 1.5", "@format")
        await pilot.click("#choice-specific")
        await pilot.click("#ok")
        await pilot.pause()
        await pilot.click("#cancel")
        await pilot.pause()
        assert column_text(app, "#value-text") == "1.5"
        assert app.session.value_format == FORMATS["general"]


async def test_the_format_dialog_uses_the_palette() -> None:
    app = AdderApp(palette=Palette(border="#202020"))
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@format")
        dialog = app.screen.query_one("#dialog")
        assert dialog.styles.border_top[1].hex.lower() == "#202020"


async def test_a_new_format_stays_for_later_rows() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@format")
        await pilot.click("#choice-currency")
        await pilot.click("#ok")
        await pilot.pause()
        await type_lines(app, pilot, "+ 2", "+ 0.5")
        assert column_text(app, "#value-text") == "$2.00\n$2.50"


async def test_zeroize_puts_the_format_back_to_general() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE) as pilot:
        await type_lines(app, pilot, "@format")
        await pilot.click("#choice-currency")
        await pilot.click("#ok")
        await pilot.pause()
        await type_lines(app, pilot, "@zeroize", "+ 1.5")
        assert column_text(app, "#value-text") == "1.5"


async def test_the_panels_are_named() -> None:
    app = AdderApp()
    async with app.run_test(size=SIZE):
        assert app.list_column.border_title == "List"
        assert app.value_column.border_title == "Value"
