"""Tests for value formatting and the two column renderables."""

import math

import pytest

from adder.formatting import build_list_text, build_value_text, format_value
from adder.model import Row, RowKind
from adder.stripes import Stripes

COLORS = {
    "text": "#839496",
    "value": "#268bd2",
    "arithmetic": "#2aa198",
    "error": "#dc322f",
}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100.0, "100"),
        (-100.0, "-100"),
        (0.0, "0"),
        (-0.0, "0"),
        (0.5, "0.5"),
        (1 / 3, "0.3333333333"),
        (0.1 + 0.2, "0.3"),
        (1e-12, "1e-12"),
        (1e300, "1e+300"),
        (1e20, "1e+20"),
    ],
)
def test_format_value(value: float, expected: str) -> None:
    assert format_value(value) == expected


def test_format_value_handles_infinity_and_nan() -> None:
    assert format_value(math.inf) == "inf"
    assert format_value(-math.inf) == "-inf"
    assert format_value(math.nan) == "nan"


def test_build_list_text_one_line_per_row() -> None:
    rows = [Row(text="hello"), Row(text="+ 100", kind=RowKind.OPERATION, value=100.0)]
    text = build_list_text(rows, COLORS)
    assert text.plain == " hello\n + 100"
    assert text.no_wrap is True


def test_build_list_text_appends_error_message() -> None:
    rows = [Row.error_row("/ 0", "division by zero")]
    text = build_list_text(rows, COLORS)
    assert text.plain == " / 0  division by zero"


def test_build_list_text_does_not_interpret_markup() -> None:
    text = build_list_text([Row(text="[bold]not markup[/]")], COLORS)
    assert text.plain == " [bold]not markup[/]"


def test_build_list_text_colors_rows_by_color_key() -> None:
    rows = [Row(text="+ 1", color_key="arithmetic")]
    text = build_list_text(rows, COLORS)
    assert str(text.spans[0].style) == "#2aa198"


def test_build_value_text_blank_when_value_unchanged() -> None:
    rows = [Row(text="hello"), Row(text="+ 100", value=100.0), Row(text="$a 1")]
    text = build_value_text(rows, COLORS)
    assert text.plain == " \n100 \n "
    assert text.justify == "right"


def test_build_value_text_is_empty_for_no_rows() -> None:
    assert build_value_text([], COLORS).plain == ""
    assert build_list_text([], COLORS).plain == ""


def test_build_value_text_uses_value_color() -> None:
    text = build_value_text([Row(text="+ 1", value=1.0)], COLORS)
    assert str(text.spans[0].style) == "#268bd2"


def test_unknown_color_key_falls_back_to_text_color() -> None:
    text = build_list_text([Row(text="x", color_key="nope")], COLORS)
    assert str(text.spans[0].style) == "#839496"


STRIPES = Stripes(shade="#073642", background="#002b36")


def test_a_row_is_padded_to_the_given_width() -> None:
    text = build_list_text([Row(text="hi")], COLORS, width=6)
    assert text.plain == " hi   "


def test_a_row_longer_than_the_width_is_not_cut() -> None:
    text = build_list_text([Row(text="hello world")], COLORS, width=4)
    assert text.plain == " hello world"


def test_a_shaded_row_carries_the_shade_as_its_background() -> None:
    rows = [Row(text="one"), Row(text="two")]
    text = build_list_text(rows, COLORS, stripes=STRIPES, width=5)
    assert str(text.spans[0].style) == "#839496"
    assert str(text.spans[1].style) == "#839496 on #073642"


def test_a_shaded_value_row_carries_the_shade_too() -> None:
    rows = [Row(text="+ 1", value=1.0), Row(text="+ 2", value=2.0)]
    text = build_value_text(rows, COLORS, stripes=STRIPES, width=6)
    assert text.plain == "    1 \n    2 "
    assert str(text.spans[1].style) == "#268bd2 on #073642"


def test_a_value_row_is_right_aligned_by_its_padding() -> None:
    text = build_value_text([Row(text="+ 1", value=100.0)], COLORS, width=6)
    assert text.plain == "  100 "


def test_a_blank_value_row_still_fills_the_width() -> None:
    text = build_value_text([Row(text="hi")], COLORS, stripes=STRIPES, width=4)
    assert text.plain == "    "


def test_plain_stripes_add_no_background() -> None:
    plain = Stripes(shade="#002b36", background="#002b36")
    text = build_list_text([Row(text="a"), Row(text="b")], COLORS, stripes=plain, width=3)
    assert {str(span.style) for span in text.spans} == {"#839496"}
