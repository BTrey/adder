"""Tests for the operator registry and its handlers."""

import pytest

from src.model import RowKind, Session
from src.operators import OPERATORS, EvaluationError, resolve_operand


def run(symbol: str, operand: str, session: Session, text: str = "") -> object:
    """Run one operator against a session."""
    return OPERATORS[symbol].evaluate(session, text or f"{symbol} {operand}", operand)


def test_registry_holds_every_documented_symbol() -> None:
    assert set(OPERATORS) >= {"+", "-", "*", "/", "^", "$"}


def test_registry_records_the_symbol_on_the_handler() -> None:
    assert OPERATORS["+"].symbol == "+"
    assert OPERATORS["+"].name == "add"


@pytest.mark.parametrize(
    ("symbol", "start", "operand", "expected"),
    [
        ("+", 1.0, "4", 5.0),
        ("-", 10.0, "4", 6.0),
        ("*", 3.0, "4", 12.0),
        ("/", 12.0, "4", 3.0),
        ("^", 2.0, "10", 1024.0),
        ("+", 0.0, "-2.5", -2.5),
    ],
)
def test_arithmetic(symbol: str, start: float, operand: str, expected: float) -> None:
    session = Session(value=start)
    row = run(symbol, operand, session)
    assert row.value == expected  # type: ignore[attr-defined]
    assert row.kind is RowKind.OPERATION  # type: ignore[attr-defined]


def test_arithmetic_color_keys() -> None:
    assert OPERATORS["+"].color_key == "arithmetic"
    assert OPERATORS["^"].color_key == "exponent"
    assert OPERATORS["$"].color_key == "variable"


def test_operator_does_not_change_the_session_itself() -> None:
    session = Session(value=1.0)
    run("+", "4", session)
    assert session.value == 1.0


def test_divide_by_zero_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="division by zero"):
        run("/", "0", Session(value=1.0))


def test_zero_to_a_negative_power_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="negative power"):
        run("^", "-1", Session(value=0.0))


def test_negative_base_with_fractional_exponent_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="real number"):
        run("^", "0.5", Session(value=-8.0))


def test_overflow_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="too large"):
        run("^", "1000", Session(value=1e300))


def test_missing_operand_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="missing operand"):
        run("+", "", Session())


def test_bad_number_raises_evaluation_error() -> None:
    with pytest.raises(EvaluationError, match="not a number"):
        run("+", "twelve", Session())


def test_resolve_operand_reads_a_variable() -> None:
    session = Session()
    session.set_variable("var1", 5.0)
    assert resolve_operand(session, "$var1") == 5.0


def test_resolve_operand_reports_an_unknown_variable() -> None:
    with pytest.raises(EvaluationError, match="unknown variable: nope"):
        resolve_operand(Session(), "$nope")


def test_resolve_operand_reports_a_missing_variable_name() -> None:
    with pytest.raises(EvaluationError, match="missing variable name"):
        resolve_operand(Session(), "$")


def test_assignment_sets_a_variable_and_prints_no_value() -> None:
    session = Session(value=3.0)
    row = OPERATORS["$"].evaluate(session, "$var1 5", "var1 5")
    assert session.get_variable("var1") == 5.0
    assert row is not None
    assert row.value is None
    assert row.kind is RowKind.ASSIGNMENT
    assert row.color_key == "variable"


def test_assignment_accepts_an_equals_sign() -> None:
    session = Session()
    OPERATORS["$"].evaluate(session, "$var1 = 5", "var1 = 5")
    assert session.get_variable("var1") == 5.0


def test_assignment_accepts_another_variable() -> None:
    session = Session()
    session.set_variable("var1", 5.0)
    OPERATORS["$"].evaluate(session, "$var2 = $var1", "var2 = $var1")
    assert session.get_variable("var2") == 5.0


def test_assignment_without_a_value_is_an_error() -> None:
    with pytest.raises(EvaluationError, match="missing value"):
        OPERATORS["$"].evaluate(Session(), "$var1", "var1")


def test_assignment_with_a_bad_name_is_an_error() -> None:
    with pytest.raises(EvaluationError, match="not a valid variable name"):
        OPERATORS["$"].evaluate(Session(), "$1var 5", "1var 5")


def test_assignment_without_a_name_is_an_error() -> None:
    with pytest.raises(EvaluationError, match="missing variable name"):
        OPERATORS["$"].evaluate(Session(), "$", "")
