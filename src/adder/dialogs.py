"""The format dialog and the decimal places dialog.

`@format` opens `FormatScreen`. If the user picks Specific, the app opens
`PlacesScreen` next to ask how many decimal places to use.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet

from adder.formats import CHOICES, Fixed, ValueFormat, read_places

DIALOG_CSS = """
DialogScreen {
    align: center middle;
    background: $adder-background 60%;
}

#dialog {
    /* An explicit width: the children below use 1fr, which would otherwise
       stretch an automatic width across the screen. */
    width: 44;
    max-width: 90%;
    height: auto;
    padding: 1 2;
    border: round $adder-border;
    background: $adder-background;
}

#title {
    width: 1fr;
    padding-bottom: 1;
    text-style: bold;
    color: $adder-value;
}

#message {
    width: 1fr;
    height: 1;
    color: $adder-error;
}

#buttons {
    width: 1fr;
    height: auto;
    padding-top: 1;
    align-horizontal: right;
}

#buttons Button {
    margin-left: 2;
}

/* The id beats the type selector of the widget's own default CSS. */
#choices {
    width: 1fr;
    height: auto;
    padding: 0;
    border: none;
    background: $adder-background;
}

#places {
    width: 12;
    border: round $adder-border;
    background: $adder-background;
    color: $adder-input;
}
"""


class DialogScreen[ResultT](ModalScreen[ResultT]):
    """What the two dialogs share: the look, the keys, and the buttons."""

    DEFAULT_CSS: ClassVar[str] = DIALOG_CSS

    BINDINGS: ClassVar[list[BindingType]] = [("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        """Close the dialog and change nothing."""
        self.dismiss(None)

    def accept(self) -> None:
        """Apply what the user chose. Subclasses implement this."""
        raise NotImplementedError

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Run OK or Cancel."""
        if event.button.id == "ok":
            self.accept()
        else:
            self.action_cancel()

    @staticmethod
    def buttons() -> ComposeResult:
        """The OK and Cancel buttons, at the bottom of the dialog."""
        with Horizontal(id="buttons"):
            yield Button("OK", id="ok", variant="primary")
            yield Button("Cancel", id="cancel")


class FormatScreen(DialogScreen[str | None]):
    """Ask which format the Value column should use."""

    def __init__(self, value_format: ValueFormat) -> None:
        self.value_format = value_format
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Value format", id="title")
            with RadioSet(id="choices"):
                for index, choice in enumerate(CHOICES):
                    yield RadioButton(
                        choice.label,
                        value=index == self._current_index(),
                        id=f"choice-{choice.key}",
                    )
            yield from self.buttons()

    def _current_index(self) -> int:
        """The choice that matches the format in use."""
        for index, choice in enumerate(CHOICES):
            if choice.key == self.value_format.name:
                if choice.key != "decimal":
                    return index
                if isinstance(self.value_format, Fixed) and self.value_format == Fixed():
                    return index
                break
        return len(CHOICES) - 1

    def accept(self) -> None:
        """Return the key of the chosen format."""
        index = self.query_one(RadioSet).pressed_index
        self.dismiss(CHOICES[max(0, index)].key)


class PlacesScreen(DialogScreen[int | None]):
    """Ask how many decimal places the specific format should use."""

    def __init__(self, places: int) -> None:
        self.places = places
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Decimal places", id="title")
            yield Input(str(self.places), id="places", type="integer")
            yield Label("", id="message")
            yield from self.buttons()

    def on_mount(self) -> None:
        """Put the cursor in the number field."""
        self.query_one("#places", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Let Enter in the number field do what OK does."""
        event.stop()
        self.accept()

    def accept(self) -> None:
        """Return the number of decimal places, or report why it is not usable."""
        try:
            places = read_places(self.query_one("#places", Input).value)
        except ValueError as error:
            self.query_one("#message", Label).update(str(error))
            return
        self.dismiss(places)
