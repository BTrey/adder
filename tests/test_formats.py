"""Tests for the Value formats."""

import math

import pytest

from adder.formats import (
    CHOICES,
    DEFAULT_FORMAT,
    DEFAULT_PLACES,
    FORMATS,
    MAX_PLACES,
    Fixed,
    build_format,
    read_places,
)


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
    ],
)
def test_the_general_format(value: float, expected: str) -> None:
    assert FORMATS["general"].format(value) == expected


def test_the_general_format_handles_infinity_and_nan() -> None:
    assert FORMATS["general"].format(math.inf) == "inf"
    assert FORMATS["general"].format(math.nan) == "nan"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100.0, "$100.00"),
        (0.5, "$0.50"),
        (0.0, "$0.00"),
        (-0.0, "$0.00"),
        (1.005, "$1.00"),
        (1234.5, "$1234.50"),
        (-5.0, "-$5.00"),
        (-0.004, "$0.00"),
    ],
)
def test_the_currency_format(value: float, expected: str) -> None:
    assert FORMATS["currency"].format(value) == expected


def test_the_currency_format_handles_infinity_and_nan() -> None:
    assert FORMATS["currency"].format(math.inf) == "inf"
    assert FORMATS["currency"].format(math.nan) == "nan"


@pytest.mark.parametrize(
    ("places", "value", "expected"),
    [
        (2, 100.0, "100.00"),
        (2, 1 / 3, "0.33"),
        (2, -0.0, "0.00"),
        (0, 100.0, "100"),
        (4, 1 / 3, "0.3333"),
        (4, -1.5, "-1.5000"),
    ],
)
def test_the_fixed_format(places: int, value: float, expected: str) -> None:
    assert Fixed(places).format(value) == expected


def test_the_fixed_format_handles_infinity_and_nan() -> None:
    assert Fixed(2).format(-math.inf) == "-inf"
    assert Fixed(2).format(math.nan) == "nan"


def test_the_decimal_format_is_two_places() -> None:
    assert FORMATS["decimal"] == Fixed(DEFAULT_PLACES)
    assert DEFAULT_PLACES == 2


def test_the_registry_holds_every_format() -> None:
    assert set(FORMATS) == {"general", "currency", "decimal"}
    assert DEFAULT_FORMAT == "general"


def test_two_formats_of_the_same_kind_are_equal() -> None:
    assert FORMATS["general"] == FORMATS["general"]
    assert Fixed(3) == Fixed(3)
    assert Fixed(3) != Fixed(4)
    assert Fixed(2) != FORMATS["currency"]


def test_the_choices_the_dialog_offers() -> None:
    assert [choice.key for choice in CHOICES] == ["general", "currency", "decimal", "specific"]
    assert [choice.label for choice in CHOICES] == ["General", "Currency", "Decimal", "Specific"]
    assert [choice.asks_places for choice in CHOICES] == [False, False, False, True]


def test_build_format_reads_a_registered_name() -> None:
    assert build_format("currency") == FORMATS["currency"]


def test_build_format_makes_a_specific_format() -> None:
    assert build_format("specific", 5) == Fixed(5)


def test_build_format_without_places_falls_back_to_the_default() -> None:
    assert build_format("specific") == Fixed(DEFAULT_PLACES)


@pytest.mark.parametrize("raw", ["0", "3", "10", " 4 "])
def test_read_places_accepts_the_whole_range(raw: str) -> None:
    assert read_places(raw) == int(raw)


@pytest.mark.parametrize("raw", ["-1", "11", "100"])
def test_read_places_rejects_a_value_out_of_range(raw: str) -> None:
    with pytest.raises(ValueError, match=f"decimal places must be 0 to {MAX_PLACES}"):
        read_places(raw)


@pytest.mark.parametrize("raw", ["", "two", "2.5"])
def test_read_places_rejects_a_value_that_is_not_a_whole_number(raw: str) -> None:
    with pytest.raises(ValueError, match="decimal places must be a whole number"):
        read_places(raw)
