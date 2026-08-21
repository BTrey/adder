"""Tests for line parsing and dispatch."""

import pytest

from src.evaluator import evaluate_line
from src.model import RowKind, Session


@pytest.mark.parametrize("line", ["", "   ", "\t"])
def test_an_empty_line_adds_nothing(line: str) -> None:
    session = Session()
    assert evaluate_line(session, line) is None
    assert session.rows == []


def test_plain_text_row_does_not_change_the_value() -> None:
    session = Session(value=7.0)
    row = evaluate_line(session, "hello")
    assert row is not None
    assert row.kind is RowKind.TEXT
    assert row.color_key == "text"
    assert row.value is None
    assert session.rows == [row]
    assert session.value == 7.0


def test_a_line_is_stripped_before_it_is_read() -> None:
    session = Session()
    row = evaluate_line(session, "   + 100   ")
    assert row is not None
    assert row.text == "+ 100"
    assert row.value == 100.0


@pytest.mark.parametrize("line", ["+100", "+ 100", "+   100"])
def test_a_space_after_the_operator_is_optional(line: str) -> None:
    session = Session()
    row = evaluate_line(session, line)
    assert row is not None
    assert row.value == 100.0


def test_rows_accumulate_and_the_value_runs() -> None:
    session = Session()
    for line in ["hello", "+ 100", "* 3"]:
        evaluate_line(session, line)
    assert [row.text for row in session.rows] == ["hello", "+ 100", "* 3"]
    assert [row.value for row in session.rows] == [None, 100.0, 300.0]
    assert session.value == 300.0


def test_a_variable_reference_is_an_operand() -> None:
    session = Session()
    evaluate_line(session, "$var1 5")
    row = evaluate_line(session, "+ $var1")
    assert row is not None
    assert row.value == 5.0


def test_an_assignment_row_leaves_the_right_column_blank() -> None:
    session = Session(value=2.0)
    row = evaluate_line(session, "$var1 = 5")
    assert row is not None
    assert row.value is None
    assert session.value == 2.0
    assert session.get_variable("var1") == 5.0


def test_clear_empties_the_list_and_adds_no_row() -> None:
    session = Session()
    evaluate_line(session, "+ 5")
    assert evaluate_line(session, "@clear") is None
    assert session.rows == []
    assert session.value == 0.0


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("/ 0", "division by zero"),
        ("+ twelve", "not a number: twelve"),
        ("+", "missing operand"),
        ("+ $nope", "unknown variable: nope"),
        ("@nope", "unknown command: nope"),
        ("^ -1", "zero cannot be raised to a negative power"),
        ("$1var 5", "not a valid variable name: 1var"),
    ],
)
def test_an_error_row_is_added_and_the_value_is_unchanged(line: str, message: str) -> None:
    session = Session()
    row = evaluate_line(session, line)
    assert row is not None
    assert row.kind is RowKind.ERROR
    assert row.color_key == "error"
    assert row.error == message
    assert row.text == line
    assert row.value is None
    assert session.rows == [row]
    assert session.value == 0.0


def test_no_line_can_raise() -> None:
    session = Session()
    for line in ["", "+", "^^^", "$", "@", "/0", "hello [red]", "$$$", "+ 1e999", "^ 1e999"]:
        evaluate_line(session, line)
