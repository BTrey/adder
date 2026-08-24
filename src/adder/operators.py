"""The operator registry and the operators that ship with Adder.

To add an operator, subclass `ArithmeticOperator` (or `Operator` for something
that acts on the session) and decorate it with `@register("<symbol>")`. No other
file changes.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable

from adder.model import Row, RowKind, Session

VARIABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ASSIGNMENT = re.compile(r"^(?P<name>[^\s=]+)\s*(?:=\s*)?(?P<value>.*)$")


class EvaluationError(Exception):
    """A line the user can type that cannot produce a Value.

    The evaluator turns this into an error row. Nothing reaches the UI as an
    exception.
    """


class Operator(ABC):
    """A handler for one leading character of a line."""

    symbol: str = ""
    name: str = ""
    color_key: str = "text"
    usage: str = ""
    """An example line, shown in the help dialog."""

    @abstractmethod
    def evaluate(self, session: Session, text: str, operand: str) -> Row | None:
        """Evaluate one line. Return the row to add, or None to add nothing.

        Raise EvaluationError for anything the user got wrong.
        """


OPERATORS: dict[str, Operator] = {}


def register(symbol: str) -> Callable[[type[Operator]], type[Operator]]:
    """Register an operator class under its leading character."""

    def decorator(cls: type[Operator]) -> type[Operator]:
        cls.symbol = symbol
        OPERATORS[symbol] = cls()
        return cls

    return decorator


def resolve_operand(session: Session, operand: str) -> float:
    """Read an operand that is either a number literal or a `$name` reference."""
    operand = operand.strip()
    if not operand:
        raise EvaluationError("missing operand")
    if operand.startswith("$"):
        name = operand[1:].strip()
        if not name:
            raise EvaluationError("missing variable name")
        value = session.get_variable(name)
        if value is None:
            raise EvaluationError(f"unknown variable: {name}")
        return value
    try:
        return float(operand)
    except ValueError as exc:
        raise EvaluationError(f"not a number: {operand}") from exc


class ArithmeticOperator(Operator):
    """An operator that turns the Value and one operand into a new Value."""

    color_key = "arithmetic"

    @abstractmethod
    def apply(self, value: float, operand: float) -> float:
        """Return the new Value."""

    def evaluate(self, session: Session, text: str, operand: str) -> Row | None:
        number = resolve_operand(session, operand)
        return Row(
            text=text,
            kind=RowKind.OPERATION,
            color_key=self.color_key,
            value=self.apply(session.value, number),
        )


@register("+")
class Add(ArithmeticOperator):
    """Add the operand to the Value."""

    name = "add"
    usage = "+ 100"

    def apply(self, value: float, operand: float) -> float:
        return value + operand


@register("-")
class Subtract(ArithmeticOperator):
    """Subtract the operand from the Value."""

    name = "subtract"
    usage = "- 100"

    def apply(self, value: float, operand: float) -> float:
        return value - operand


@register("*")
class Multiply(ArithmeticOperator):
    """Multiply the Value by the operand."""

    name = "multiply"
    usage = "* 3"

    def apply(self, value: float, operand: float) -> float:
        return value * operand


@register("/")
class Divide(ArithmeticOperator):
    """Divide the Value by the operand."""

    name = "divide"
    usage = "/ 3"

    def apply(self, value: float, operand: float) -> float:
        if operand == 0:
            raise EvaluationError("division by zero")
        return value / operand


@register("^")
class Power(ArithmeticOperator):
    """Raise the Value to the power of the operand."""

    name = "power"
    usage = "^ 2"
    color_key = "exponent"

    def apply(self, value: float, operand: float) -> float:
        try:
            result = value**operand
        except ZeroDivisionError as exc:
            raise EvaluationError("zero cannot be raised to a negative power") from exc
        except OverflowError as exc:
            raise EvaluationError("result is too large") from exc
        if isinstance(result, complex):
            raise EvaluationError("result is not a real number")
        return float(result)


@register("$")
class Assign(Operator):
    """Set a variable. The equals sign is optional.

    `$name 5` and `$name = 5` are the same. An assignment does not change the
    Value, so the right column stays blank.
    """

    name = "assign"
    usage = "$rate = 0.07"
    color_key = "variable"

    def evaluate(self, session: Session, text: str, operand: str) -> Row | None:
        match = ASSIGNMENT.match(operand.strip())
        if match is None:
            raise EvaluationError("missing variable name")
        name = match["name"]
        if VARIABLE_NAME.fullmatch(name) is None:
            raise EvaluationError(f"not a valid variable name: {name}")
        if not match["value"].strip():
            raise EvaluationError(f"missing value for variable: {name}")
        session.set_variable(name, resolve_operand(session, match["value"]))
        return Row(text=text, kind=RowKind.ASSIGNMENT, color_key=self.color_key)
