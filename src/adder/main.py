"""The entry point: read the command line, load the colors, run the app."""

from __future__ import annotations

import sys

from adder.app import AdderApp
from adder.cli import PRINT_CONFIG, parse_args
from adder.config import DEFAULT_CONFIG_TEXT, ConfigError, load_appearance


def main(argv: list[str] | None = None) -> int:
    """Run Adder. Return the exit status."""
    arguments = parse_args(argv)
    if arguments.config is PRINT_CONFIG:
        print(DEFAULT_CONFIG_TEXT, end="")
        return 0
    try:
        appearance = load_appearance(arguments.config)
    except ConfigError as error:
        print(f"adder: {error}", file=sys.stderr)
        return 2
    AdderApp(width=arguments.width, palette=appearance.palette, band=appearance.band).run()
    return 0
