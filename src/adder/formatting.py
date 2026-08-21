"""Format the Value and build the renderable for each column."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from rich.console import JustifyMethod
from rich.text import Text

from adder.model import Row

INTEGER_LIMIT = 1e15
"""Above this magnitude a float can no longer hold every integer, so use exponent form."""

SIGNIFICANT_DIGITS = 10
"""Digits kept for a value that is not a whole number. This hides float noise."""


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


def _color(colors: Mapping[str, str], key: str) -> str:
    """Look up a color, falling back to the plain text color."""
    return colors.get(key, colors["text"])


def _new_text(justify: JustifyMethod | None = None) -> Text:
    """Build an empty Text that never wraps a row onto a second line."""
    return Text(no_wrap=True, overflow="ignore", justify=justify)


def build_list_text(rows: Sequence[Row], colors: Mapping[str, str]) -> Text:
    """Build the left column: one line per row, colored by its color key."""
    text = _new_text()
    for index, row in enumerate(rows):
        if index:
            text.append("\n")
        line = row.text if row.error is None else f"{row.text}  {row.error}"
        text.append(line, style=_color(colors, row.color_key))
    return text


def build_value_text(rows: Sequence[Row], colors: Mapping[str, str]) -> Text:
    """Build the right column: the new Value, or a blank line if it did not change."""
    text = _new_text(justify="right")
    for index, row in enumerate(rows):
        if index:
            text.append("\n")
        if row.value is not None:
            text.append(format_value(row.value), style=_color(colors, "value"))
    return text
