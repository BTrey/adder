"""Command line parsing."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Final

DEFAULT_WIDTH: Final = 75
MIN_WIDTH: Final = 0
MAX_WIDTH: Final = 100

PROGRAM = "adder.py"
DESCRIPTION = "A running-tape calculator and notepad for the terminal."
EPILOG = """\
operators: + - * / ^ (arithmetic), $name = 5 (variable), @clear (command)
"""


class ConfigAction(Enum):
    """What the -c flag asked for when it was given no path."""

    PRINT = auto()


PRINT_CONFIG: Final = ConfigAction.PRINT
"""The value of `config` when the user typed a bare -c: print the defaults and exit."""

ConfigOption = Path | ConfigAction | None


@dataclass(frozen=True)
class Arguments:
    """The parsed command line."""

    width: int
    config: ConfigOption


def width_percent(value: str) -> int:
    """Read the -w value as a percent between 0 and 100."""
    try:
        percent = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"width must be a whole number: {value}") from exc
    if not MIN_WIDTH <= percent <= MAX_WIDTH:
        raise argparse.ArgumentTypeError(f"width must be between 0 and 100: {value}")
    return percent


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-w",
        "--width",
        type=width_percent,
        default=DEFAULT_WIDTH,
        metavar="N",
        help="width of the List column, in percent of the screen (default: 75)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        nargs="?",
        const=PRINT_CONFIG,
        default=None,
        metavar="PATH",
        help="read colors from PATH, or print the default config and exit if PATH is left out",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> Arguments:
    """Parse the command line. A bad value exits with status 2."""
    namespace = build_parser().parse_args(argv)
    return Arguments(width=namespace.width, config=namespace.config)
