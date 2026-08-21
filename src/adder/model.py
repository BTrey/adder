"""The data model: rows, row kinds, and the session that holds them."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RowKind(Enum):
    """What a row of the List represents."""

    TEXT = "text"
    OPERATION = "operation"
    ASSIGNMENT = "assignment"
    COMMAND = "command"
    ERROR = "error"


@dataclass
class Row:
    """One line of the List, and the Value it produced, if any.

    A row prints in the right column only if `value` is not None.
    """

    text: str
    kind: RowKind = RowKind.TEXT
    color_key: str = "text"
    value: float | None = None
    error: str | None = None

    @classmethod
    def error_row(cls, text: str, message: str) -> Row:
        """Build an error row that keeps the raw text and the message."""
        return cls(text=text, kind=RowKind.ERROR, color_key="error", error=message)


@dataclass
class Session:
    """The List, the running Value, and the variables."""

    rows: list[Row] = field(default_factory=list)
    value: float = 0.0
    variables: dict[str, float] = field(default_factory=dict)

    def add(self, row: Row) -> None:
        """Append a row and adopt its Value if it changed the Value."""
        self.rows.append(row)
        if row.value is not None:
            self.value = row.value

    def set_variable(self, name: str, value: float) -> None:
        """Store a variable."""
        self.variables[name] = value

    def get_variable(self, name: str) -> float | None:
        """Read a variable, or None if it is not set."""
        return self.variables.get(name)

    def clear(self) -> None:
        """Empty the List and reset the Value. Variables stay."""
        self.rows.clear()
        self.value = 0.0
