"""Tests for the palette, the default config text, and the INI loader."""

from configparser import ParsingError
from pathlib import Path

import pytest

from adder.config import (
    DEFAULT_CONFIG_TEXT,
    Appearance,
    ConfigError,
    Palette,
    default_config_path,
    load_appearance,
)


def load_palette(path: Path | None) -> Palette:
    """Read only the colors, which most of these tests care about."""
    return load_appearance(path).palette


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "adder.conf"
    path.write_text(body, encoding="utf-8")
    return path


def test_default_palette_is_solarized_dark() -> None:
    palette = Palette()
    assert palette.background == "#002b36"
    assert palette.stripe == "#073642"
    assert palette.text == "#839496"
    assert palette.error == "#dc322f"


def test_palette_colors_maps_every_color_key() -> None:
    colors = Palette().colors
    assert colors["text"] == "#839496"
    assert colors["value"] == "#268bd2"
    assert set(colors) >= {"arithmetic", "exponent", "variable", "command", "error"}


def test_default_config_text_parses_back_to_the_default_palette(tmp_path: Path) -> None:
    assert load_palette(write(tmp_path, DEFAULT_CONFIG_TEXT)) == Palette()


def test_a_partial_config_keeps_the_defaults(tmp_path: Path) -> None:
    path = write(tmp_path, "[colors]\nbackground = #ffffff\n")
    palette = load_palette(path)
    assert palette.background == "#ffffff"
    assert palette.text == Palette().text


def test_an_unknown_key_or_section_is_ignored(tmp_path: Path) -> None:
    path = write(tmp_path, "[colors]\nnope = red\n[nonsense]\nalso = red\n")
    assert load_palette(path) == Palette()


def test_the_stripe_color_is_read(tmp_path: Path) -> None:
    path = write(tmp_path, "[colors]\nstripe = #111111\n")
    assert load_palette(path).stripe == "#111111"


def test_the_stripe_band_is_read(tmp_path: Path) -> None:
    assert load_appearance(write(tmp_path, "[stripes]\nband = 3\n")).band == 3


def test_the_band_defaults_to_one_row(tmp_path: Path) -> None:
    assert load_appearance(write(tmp_path, "[colors]\ntext = red\n")) == Appearance(
        palette=Palette(text="red")
    )


def test_the_default_config_text_parses_back_to_the_default_appearance(tmp_path: Path) -> None:
    assert load_appearance(write(tmp_path, DEFAULT_CONFIG_TEXT)) == Appearance()


def test_a_band_that_is_not_a_number_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="band must be a whole number: two"):
        load_appearance(write(tmp_path, "[stripes]\nband = two\n"))


def test_a_band_below_one_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="band must be 1 or more: 0"):
        load_appearance(write(tmp_path, "[stripes]\nband = 0\n"))


def test_a_named_color_is_accepted(tmp_path: Path) -> None:
    assert load_palette(write(tmp_path, "[colors]\ntext = red\n")).text == "red"


def test_a_missing_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config file not found"):
        load_palette(tmp_path / "absent.conf")


def test_a_bad_color_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="bad color for text: nope"):
        load_palette(write(tmp_path, "[colors]\ntext = nope\n"))


def test_a_malformed_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="cannot read"):
        load_palette(write(tmp_path, "this is not ini\n"))


def test_an_unreadable_file_is_an_error(tmp_path: Path) -> None:
    path = write(tmp_path, DEFAULT_CONFIG_TEXT)
    path.chmod(0o000)
    try:
        with pytest.raises(ConfigError, match="cannot read"):
            load_palette(path)
    finally:
        path.chmod(0o644)


def test_no_path_reads_the_xdg_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    (tmp_path / "adder").mkdir()
    (tmp_path / "adder" / "adder.conf").write_text("[colors]\ntext = red\n", encoding="utf-8")
    assert default_config_path() == tmp_path / "adder" / "adder.conf"
    assert load_palette(None).text == "red"


def test_no_path_and_no_file_uses_the_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert load_palette(None) == Palette()


def test_the_home_config_is_used_without_xdg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert default_config_path() == tmp_path / ".config" / "adder" / "adder.conf"


def test_parsing_error_type_is_wrapped(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as info:
        load_palette(write(tmp_path, "[colors\ntext = red\n"))
    assert isinstance(info.value.__cause__, (ParsingError, OSError))
