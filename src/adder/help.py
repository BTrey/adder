"""The help dialog and the text it shows.

The text is built from the operator and command registries, so an operator or
a command that is registered shows up here without any other change.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from adder import __version__
from adder.commands import COMMANDS, Command
from adder.operators import OPERATORS, Operator

USAGE_WIDTH = 14
"""Columns kept for the example, so the summaries line up."""

DIALOG_GUTTER = 8
"""The border, the padding, and the scrollbar columns around the help text."""

INTRODUCTION = (
    "Type a line and press Enter. The line joins the List on the left.",
    "A line that starts with an operator also changes the Value.",
    "A line with no operator is only text.",
)

HINT = "Press Escape to close."

KEYS = (
    ("Enter", "Evaluate the line."),
    ("Ctrl+Q", "Quit Adder."),
    ("Escape", "Close this help."),
)


def summarize(handler: Operator | Command) -> str:
    """Return the first line of the handler docstring."""
    documentation = handler.__doc__ or ""
    return documentation.strip().splitlines()[0].strip()


def build_help_text(colors: Mapping[str, str]) -> Text:
    """Build the help as one Text, colored from the palette."""
    text = Text()
    text.append(f"Adder {__version__}\n\n", style=f"bold {colors['value']}")
    for line in INTRODUCTION:
        text.append(f"{line}\n", style=colors["text"])

    _section(text, colors, "Operators")
    for operator in OPERATORS.values():
        _entry(text, colors, operator.usage, summarize(operator), colors[operator.color_key])

    _section(text, colors, "Commands")
    for name, command in COMMANDS.items():
        _entry(text, colors, f"@{name}", summarize(command), colors["command"])

    _section(text, colors, "Keys")
    for key, description in KEYS:
        _entry(text, colors, key, description, colors["value"])

    text.append(f"\n{HINT}", style=colors["border"])
    return text


def _section(text: Text, colors: Mapping[str, str], title: str) -> None:
    """Start a section of the help."""
    text.append(f"\n{title}\n", style=f"bold {colors['value']}")


def _entry(text: Text, colors: Mapping[str, str], usage: str, summary: str, color: str) -> None:
    """Add one example line and its summary."""
    text.append(f"  {usage.ljust(USAGE_WIDTH)}", style=color)
    text.append(f"{summary}\n", style=colors["text"])


class HelpScreen(ModalScreen[None]):
    """A dialog over the app that shows the help."""

    DEFAULT_CSS: ClassVar[str] = """
    HelpScreen {
        align: center middle;
        background: $adder-background 60%;
    }

    #help-dialog {
        width: auto;
        overflow-x: hidden;
        max-width: 90%;
        height: auto;
        max-height: 100%;
        padding: 1 2;
        border: round $adder-border;
        background: $adder-background;
    }

    #help-text {
        /* Fill the dialog, so a narrow terminal wraps the help instead of
           cutting it off. */
        width: 1fr;
    }

    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
        ("enter", "dismiss", "Close"),
    ]

    def __init__(self, colors: Mapping[str, str]) -> None:
        self.help_colors = colors
        self.help_text = build_help_text(colors)
        super().__init__()

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-dialog"):
            yield Static(self.help_text, id="help-text", markup=False)

    def on_mount(self) -> None:
        """Make the dialog as wide as the widest help line.

        An automatic width leaves out the scrollbar, which then cuts the text.
        The CSS max-width still keeps the dialog inside a narrow terminal.
        """
        longest = max(len(line) for line in self.help_text.plain.splitlines())
        self.query_one("#help-dialog", VerticalScroll).styles.width = longest + DIALOG_GUTTER

    def on_click(self) -> None:
        """Close the dialog when the user clicks anywhere."""
        self.dismiss(None)
