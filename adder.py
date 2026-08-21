"""Adder: a running-tape calculator and notepad for the terminal."""

from __future__ import annotations

import sys

from src.app import AdderApp
from src.cli import PRINT_CONFIG, parse_args
from src.config import DEFAULT_CONFIG_TEXT, ConfigError, load_palette


def main(argv: list[str] | None = None) -> int:
    """Run Adder. Return the exit status."""
    arguments = parse_args(argv)
    if arguments.config is PRINT_CONFIG:
        print(DEFAULT_CONFIG_TEXT, end="")
        return 0
    try:
        palette = load_palette(arguments.config)
    except ConfigError as error:
        print(f"adder: {error}", file=sys.stderr)
        return 2
    AdderApp(width=arguments.width, palette=palette).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
