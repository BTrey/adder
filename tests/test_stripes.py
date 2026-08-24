"""Tests for the stripe pattern."""

from adder.stripes import Stripes


def test_the_first_band_is_plain_and_the_second_is_shaded() -> None:
    stripes = Stripes(shade="#073642", background="#002b36")
    assert [stripes.shade_for(row) for row in range(4)] == [
        None,
        "#073642",
        None,
        "#073642",
    ]


def test_a_band_covers_more_than_one_row() -> None:
    stripes = Stripes(shade="#073642", background="#002b36", band=2)
    assert [stripes.shade_for(row) for row in range(6)] == [
        None,
        None,
        "#073642",
        "#073642",
        None,
        None,
    ]


def test_a_shade_equal_to_the_background_shades_nothing() -> None:
    stripes = Stripes(shade="#002b36", background="#002b36")
    assert stripes.is_plain is True
    assert [stripes.shade_for(row) for row in range(4)] == [None, None, None, None]


def test_a_band_below_one_is_read_as_one_row() -> None:
    stripes = Stripes(shade="#073642", background="#002b36", band=0)
    assert stripes.shade_for(1) == "#073642"


def test_stripes_are_built_from_a_palette() -> None:
    from adder.config import Palette

    stripes = Stripes.from_palette(Palette(), band=3)
    assert stripes.shade == Palette().stripe
    assert stripes.background == Palette().background
    assert stripes.band == 3
