"""Tests for the command registry and the `@` operator."""

import pytest

from adder.commands import COMMANDS, HELP_EFFECT
from adder.model import Row, Session
from adder.operators import OPERATORS, EvaluationError


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


def test_zeroize_is_registered() -> None:
    assert COMMANDS["zeroize"].name == "zeroize"


def test_zeroize_clears_the_list_the_value_and_the_variables() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    session.set_variable("var1", 2.0)
    assert run("@zeroize", session) is None
    assert session == Session()


def test_zeroize_reports_a_rejected_argument() -> None:
    with pytest.raises(EvaluationError, match="zeroize takes no argument"):
        run("@zeroize now", Session())


def test_clear_keeps_the_variables() -> None:
    session = Session()
    session.set_variable("var1", 2.0)
    run("@clear", session)
    assert session.variables == {"var1": 2.0}


def test_help_is_registered() -> None:
    assert COMMANDS["help"].name == "help"


def test_help_asks_the_ui_to_show_the_help_and_adds_no_row() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    assert run("@help", session) is None
    assert session.take_effects() == [HELP_EFFECT]
    assert len(session.rows) == 1
    assert session.value == 5.0


def test_help_reports_a_rejected_argument() -> None:
    with pytest.raises(EvaluationError, match="help takes no argument"):
        run("@help me", Session())
