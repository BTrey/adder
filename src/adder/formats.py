"""How the Value prints in the right column.

To add a format, subclass `ValueFormat`, decorate it with `@register("<name>")`,
and add a `Choice` for it. Nothing else changes.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar

INTEGER_LIMIT = 1e15
"""Above this magnitude a float can no longer hold every integer, so use exponent form."""

SIGNIFICANT_DIGITS = 10
"""Digits kept by the general format for a number that is not whole."""

DEFAULT_PLACES = 2
"""Decimal places of the decimal format."""

MAX_PLACES = 10
"""The most decimal places the specific format accepts."""

DEFAULT_FORMAT = "general"
"""The format a new session starts with."""

SPECIFIC = "specific"
"""The choice that asks the user for a number of decimal places."""


class ValueFormat(ABC):
    """Turns the Value into the text of the right column."""

    name: ClassVar[str] = ""

    @abstractmethod
    def format(self, value: float) -> str:
        """Return the text for a Value."""


FORMATS: dict[str, ValueFormat] = {}


def register(name: str) -> Callable[[type[ValueFormat]], type[ValueFormat]]:
    """Register a format class under its name."""

    def decorator(cls: type[ValueFormat]) -> type[ValueFormat]:
        cls.name = name
        FORMATS[name] = cls()
        return cls

    return decorator


@register("general")
@dataclass(frozen=True)
class General(ValueFormat):
    """Print a whole number without a decimal point, and any other number with
    up to 10 significant digits."""

    def format(self, value: float) -> str:
        if not math.isfinite(value):
            return str(value)
        if value == int(value) and abs(value) < INTEGER_LIMIT:
            return str(int(value))
        return f"{value:.{SIGNIFICANT_DIGITS}g}"


@register("currency")
@dataclass(frozen=True)
class Currency(ValueFormat):
    """Print US currency: a dollar sign, a leading zero, and two decimal places."""

    def format(self, value: float) -> str:
        if not math.isfinite(value):
            return str(value)
        amount = abs(value)
        sign = "-" if value < 0 and round(amount, DEFAULT_PLACES) else ""
        return f"{sign}${amount:.{DEFAULT_PLACES}f}"


@register("decimal")
@dataclass(frozen=True)
class Fixed(ValueFormat):
    """Print a fixed number of decimal places."""

    places: int = DEFAULT_PLACES

    def format(self, value: float) -> str:
        if not math.isfinite(value):
            return str(value)
        return f"{value + 0.0:.{self.places}f}"


@dataclass(frozen=True)
class Choice:
    """One option of the format dialog."""

    key: str
    label: str
    asks_places: bool = False


CHOICES = (
    Choice("general", "General"),
    Choice("currency", "Currency"),
    Choice("decimal", "Decimal"),
    Choice(SPECIFIC, "Specific", asks_places=True),
)


def build_format(key: str, places: int | None = None) -> ValueFormat:
    """Build the format for one choice of the dialog."""
    if key == SPECIFIC:
        return Fixed(DEFAULT_PLACES if places is None else places)
    return FORMATS[key]


def read_places(raw: str) -> int:
    """Read a number of decimal places the user typed.

    Raise ValueError with a message the dialog can show.
    """
    try:
        places = int(raw.strip())
    except ValueError as exc:
        raise ValueError("decimal places must be a whole number") from exc
    if not 0 <= places <= MAX_PLACES:
        raise ValueError(f"decimal places must be 0 to {MAX_PLACES}") from None
    return places
