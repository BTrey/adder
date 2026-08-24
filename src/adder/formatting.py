"""Format the Value and build the renderable for each column."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from rich.console import JustifyMethod
from rich.text import Text

from adder.model import Row
from adder.stripes import Stripes

INTEGER_LIMIT = 1e15
"""Above this magnitude a float can no longer hold every integer, so use exponent form."""

SIGNIFICANT_DIGITS = 10
"""Digits kept for a value that is not a whole number. This hides float noise."""

GUTTER = " "
"""One column of space at the outer edge of a row. The stripe covers it too, so
the gutter belongs to the text and not to the CSS padding."""


def format_value(value: float) -> str:
    """Format the Value for the right column.

    A whole number prints without a decimal point. Any other number prints with
    up to 10 significant digits.
    """
    if math.isnan(value) or math.isinf(value):
        return str(value)
    if value == int(value) and abs(value) < INTEGER_LIMIT:
        return str(int(value))
    return f"{value:.{SIGNIFICANT_DIGITS}g}"


def build_list_text(
    rows: Sequence[Row],
    colors: Mapping[str, str],
    stripes: Stripes | None = None,
    width: int = 0,
) -> Text:
    """Build the left column: one line per row, colored by its color key."""
    text = _new_text()
    for index, row in enumerate(rows):
        line = row.text if row.error is None else f"{row.text}  {row.error}"
        _line(text, index, f"{GUTTER}{line}".ljust(width), _color(colors, row.color_key), stripes)
    return text


def build_value_text(
    rows: Sequence[Row],
    colors: Mapping[str, str],
    stripes: Stripes | None = None,
    width: int = 0,
) -> Text:
    """Build the right column: the new Value, or a blank line if it did not change.

    The padding puts the Value at the right of the column, so the stripe of a
    row covers the whole column.
    """
    text = _new_text(justify="right")
    for index, row in enumerate(rows):
        line = "" if row.value is None else format_value(row.value)
        _line(text, index, f"{line}{GUTTER}".rjust(width), _color(colors, "value"), stripes)
    return text


def _new_text(justify: JustifyMethod | None = None) -> Text:
    """Build an empty Text that never wraps a row onto a second line."""
    return Text(no_wrap=True, overflow="ignore", justify=justify)


def _color(colors: Mapping[str, str], key: str) -> str:
    """Look up a color, falling back to the plain text color."""
    return colors.get(key, colors["text"])


def _line(text: Text, index: int, line: str, color: str, stripes: Stripes | None) -> None:
    """Add one row, shaded if it falls in a shaded band."""
    if index:
        text.append("\n")
    shade = None if stripes is None else stripes.shade_for(index)
    text.append(line, style=color if shade is None else f"{color} on {shade}")
