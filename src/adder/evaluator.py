"""Turn one typed line into a row, and add it to the session."""

from __future__ import annotations

from adder import commands  # pylint: disable=unused-import  # registers the @ operator
from adder.model import Row, Session
from adder.operators import OPERATORS, EvaluationError

__all__ = ["evaluate_line", "commands"]


def evaluate_line(session: Session, line: str) -> Row | None:
    """Evaluate a line and add the resulting row to the session.

    Return the row that was added, or None if the line added nothing. This
    never raises: a line the user got wrong becomes an error row.
    """
    text = line.strip()
    if not text:
        return None
    operator = OPERATORS.get(text[0])
    if operator is None:
        row: Row | None = Row(text=text)
    else:
        try:
            row = operator.evaluate(session, text, text[1:].strip())
        except EvaluationError as exc:
            row = Row.error_row(text, str(exc))
    if row is not None:
        session.add(row)
    return row
