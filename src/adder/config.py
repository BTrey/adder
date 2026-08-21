"""The color palette, its INI file, and the built-in defaults."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, fields
from pathlib import Path

from textual.color import Color, ColorParseError

CONFIG_DIRECTORY = "adder"
CONFIG_FILENAME = "adder.conf"

SECTIONS: dict[str, tuple[str, ...]] = {
    "colors": ("background", "border", "text", "value", "input"),
    "operators": ("arithmetic", "exponent", "variable", "command", "error"),
}


class ConfigError(Exception):
    """The config file cannot be read, or it holds a color that is not valid."""


@dataclass(frozen=True)
class Palette:  # pylint: disable=too-many-instance-attributes
    """Every color the app uses. The defaults are solarized dark."""

    background: str = "#002b36"
    border: str = "#586e75"
    text: str = "#839496"
    value: str = "#268bd2"
    input: str = "#93a1a1"
    arithmetic: str = "#2aa198"
    exponent: str = "#6c71c4"
    variable: str = "#b58900"
    command: str = "#859900"
    error: str = "#dc322f"

    @property
    def colors(self) -> dict[str, str]:
        """The palette as a plain mapping, for the row spans."""
        return {field.name: getattr(self, field.name) for field in fields(self)}


DEFAULT_CONFIG_TEXT = """\
# Adder colors.
#
# A value is any color Textual accepts: a hex string such as #268bd2, or a
# name such as red. A key that is not listed here is ignored. A key that is
# missing keeps its default. The defaults below are solarized dark.

[colors]
# base03 - the app background
background = #002b36
# base01 - the panel borders
border = #586e75
# base0 - a row with no operator
text = #839496
# blue - the right column
value = #268bd2
# base1 - the entry field
input = #93a1a1

[operators]
# cyan - the + - * / rows
arithmetic = #2aa198
# violet - the ^ rows
exponent = #6c71c4
# yellow - the $ rows
variable = #b58900
# green - the @ rows
command = #859900
# red - a row that failed
error = #dc322f
"""


def default_config_path() -> Path:
    """Return the config file path used when no path is given on the command line."""
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / CONFIG_DIRECTORY / CONFIG_FILENAME


def _read(path: Path) -> configparser.ConfigParser:
    """Read the INI file, or raise ConfigError."""
    parser = configparser.ConfigParser()
    try:
        with path.open(encoding="utf-8") as handle:
            parser.read_file(handle)
    except (OSError, configparser.Error, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    return parser


def load_palette(path: Path | None = None) -> Palette:
    """Load the palette.

    With a path, the file must exist. Without a path, the app reads the default
    config file if it is there, and uses the built-in defaults if it is not.
    """
    if path is None:
        path = default_config_path()
        if not path.is_file():
            return Palette()
    elif not path.is_file():
        raise ConfigError(f"config file not found: {path}")

    parser = _read(path)
    values: dict[str, str] = {}
    for section, keys in SECTIONS.items():
        for key in keys:
            raw = parser.get(section, key, fallback=None)
            if raw is None:
                continue
            raw = raw.strip()
            try:
                Color.parse(raw)
            except ColorParseError as exc:
                raise ConfigError(f"bad color for {key}: {raw}") from exc
            values[key] = raw
    return Palette(**values)
