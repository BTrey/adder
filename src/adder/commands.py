"""The command registry and the `@` operator that dispatches to it.

To add a command, subclass `Command` and decorate it with `@register("<name>")`.
No other file changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from adder.model import Row, Session
from adder.operators import EvaluationError, Operator
from adder.operators import register as register_operator


class Command(ABC):
    """A handler for one `@name` line."""

    name: str = ""

    @abstractmethod
    def execute(self, session: Session, text: str, argument: str) -> Row | None:
        """Run the command. Return the row to add, or None to add nothing.

        Raise EvaluationError for anything the user got wrong.
        """

    def reject_argument(self, argument: str) -> None:
        """Raise EvaluationError if the user typed an argument."""
        if argument:
            raise EvaluationError(f"{self.name} takes no argument")


COMMANDS: dict[str, Command] = {}

HELP_EFFECT = "help"
"""The effect the UI runs to show the help dialog."""


def register(name: str) -> Callable[[type[Command]], type[Command]]:
    """Register a command class under its name."""

    def decorator(cls: type[Command]) -> type[Command]:
        cls.name = name
        COMMANDS[name] = cls()
        return cls

    return decorator


@register("clear")
class Clear(Command):
    """Empty the List and reset the Value. The variables stay.

    The `@clear` line itself does not remain in the List.
    """

    def execute(self, session: Session, text: str, argument: str) -> Row | None:
        """Clear the session. This adds no row, so the command leaves no trace."""
        self.reject_argument(argument)
        session.clear()
        return None


@register("zeroize")
class Zeroize(Command):
    """Empty the List and the variables, and reset the Value.

    Adder is then in the same state as a program that has just started.
    """

    def execute(self, session: Session, text: str, argument: str) -> Row | None:
        """Reset the session. This adds no row, so the command leaves no trace."""
        self.reject_argument(argument)
        session.reset()
        return None


@register("help")
class Help(Command):
    """Show the help dialog."""

    def execute(self, session: Session, text: str, argument: str) -> Row | None:
        """Ask the UI for the help dialog. The List and the Value do not change."""
        self.reject_argument(argument)
        session.request_effect(HELP_EFFECT)
        return None


@register_operator("@")
class RunCommand(Operator):
    """Look up a command by name and run it."""

    name = "command"
    color_key = "command"
    usage = "@name"

    def evaluate(self, session: Session, text: str, operand: str) -> Row | None:
        name, _, argument = operand.strip().partition(" ")
        name = name.lower()
        if not name:
            raise EvaluationError("missing command name")
        command = COMMANDS.get(name)
        if command is None:
            raise EvaluationError(f"unknown command: {name}")
        return command.execute(session, text, argument.strip())
