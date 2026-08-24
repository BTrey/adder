"""Tests for the help text."""

from rich.text import Text

from adder import __version__
from adder.commands import COMMANDS
from adder.config import Palette
from adder.help import build_help_text, summarize
from adder.operators import OPERATORS

COLORS = Palette().colors


def plain() -> str:
    return build_help_text(COLORS).plain


def test_the_help_names_the_program_and_its_version() -> None:
    assert f"Adder {__version__}" in plain()


def test_the_help_lists_every_operator_with_its_example() -> None:
    text = plain()
    for operator in OPERATORS.values():
        assert operator.usage in text
        assert summarize(operator) in text


def test_the_help_lists_every_command() -> None:
    text = plain()
    for name, command in COMMANDS.items():
        assert f"@{name}" in text
        assert summarize(command) in text


def test_the_help_lists_the_keys() -> None:
    text = plain()
    assert "Enter" in text
    assert "Ctrl+Q" in text
    assert "Escape" in text


def test_the_help_says_how_to_close_the_dialog() -> None:
    assert plain().rstrip().endswith("Press Escape to close.")


def test_the_help_explains_a_text_row() -> None:
    assert "no operator" in plain()


def test_summarize_reads_the_first_line_of_the_docstring() -> None:
    assert summarize(OPERATORS["+"]) == "Add the operand to the Value."
    assert summarize(COMMANDS["zeroize"]) == "Empty the List and the variables, and reset the Value."


def test_the_help_colors_each_operator_with_its_own_color() -> None:
    text = build_help_text(COLORS)
    styles = {str(span.style) for span in text.spans}
    assert COLORS["arithmetic"] in styles
    assert COLORS["exponent"] in styles
    assert COLORS["variable"] in styles
    assert COLORS["command"] in styles


def test_the_help_is_built_from_spans_not_markup() -> None:
    text = build_help_text(COLORS)
    assert isinstance(text, Text)
    assert "[" not in text.plain
