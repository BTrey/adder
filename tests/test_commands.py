"""Tests for the command registry and the `@` operator."""

import pytest

from src.commands import COMMANDS
from src.model import Row, Session
from src.operators import OPERATORS, EvaluationError


def run(text: str, session: Session) -> Row | None:
    """Run a `@command` line through the registered `@` operator."""
    return OPERATORS["@"].evaluate(session, text, text[1:])


def test_command_operator_is_registered() -> None:
    assert OPERATORS["@"].color_key == "command"
    assert "clear" in COMMANDS
    assert COMMANDS["clear"].name == "clear"


def test_clear_empties_the_list_and_resets_the_value() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    assert run("@clear", session) is None
    assert session.rows == []
    assert session.value == 0.0


def test_clear_is_case_insensitive_and_ignores_spaces() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    assert run("@ CLEAR ", session) is None
    assert session.rows == []


def test_unknown_command_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="unknown command: nope"):
        run("@nope", Session())


def test_missing_command_name_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="missing command name"):
        run("@", Session())


def test_clear_reports_a_rejected_argument() -> None:
    with pytest.raises(EvaluationError, match="takes no argument"):
        run("@clear now", Session())
