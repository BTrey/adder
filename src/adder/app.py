"""The Textual application: two columns, an entry field, and the wiring."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal, VerticalScroll
from textual.theme import Theme
from textual.widgets import Input, Static

from adder.cli import MAX_WIDTH, MIN_WIDTH
from adder.commands import HELP_EFFECT
from adder.config import DEFAULT_BAND, Palette
from adder.evaluator import evaluate_line
from adder.formatting import build_list_text, build_value_text
from adder.help import HelpScreen
from adder.model import Session
from adder.stripes import Stripes

THEME_NAME = "adder"

STYLESHEET = """\
Screen {
    background: $adder-background;
}

#columns {
    height: 1fr;
}

#list {
    width: 75%;
    border: round $adder-border;
    background: $adder-background;
    overflow-x: scroll;
    overflow-y: auto;
    scrollbar-size-horizontal: 1;
}

#value {
    width: 1fr;
    border: round $adder-border;
    background: $adder-background;
    overflow-x: hidden;
    overflow-y: hidden;
}

#list-text {
    width: auto;
}

#value-text {
    width: 1fr;
    text-align: right;
    /* The bottom row matches the row the horizontal scrollbar takes from the
       left column, so both columns can scroll to the same last row. */
    padding-bottom: 1;
}

#entry {
    dock: bottom;
    height: 3;
    border: round $adder-border;
    background: $adder-background;
    color: $adder-input;
}
"""


class AdderApp(App[None]):
    """A running-tape calculator and notepad."""

    CSS: ClassVar[str] = STYLESHEET
    BINDINGS: ClassVar[list[BindingType]] = [("ctrl+q", "quit", "Quit")]

    def __init__(
        self,
        width: int = 75,
        palette: Palette | None = None,
        band: int = DEFAULT_BAND,
        session: Session | None = None,
    ) -> None:
        self.column_width = width
        self.palette = palette or Palette()
        self.stripes = Stripes.from_palette(self.palette, band)
        self.session = session or Session()
        super().__init__()

    def _apply_width(self) -> None:
        """Give the List column its share of the screen.

        A column that gets none of the screen is hidden, so the other column
        takes the whole width instead of leaving an empty border box behind.
        """
        self.list_column.styles.width = f"{self.column_width}%"
        if self.column_width == MIN_WIDTH:
            self.list_column.display = False
        elif self.column_width == MAX_WIDTH:
            self.value_column.display = False

    def get_theme_variable_defaults(self) -> dict[str, str]:
        """Publish the palette to the stylesheet.

        These are defaults, so they are in place before the theme is selected.
        """
        return {
            "adder-background": self.palette.background,
            "adder-border": self.palette.border,
            "adder-text": self.palette.text,
            "adder-value": self.palette.value,
            "adder-input": self.palette.input,
        }

    def compose(self) -> ComposeResult:
        with Horizontal(id="columns"):
            with VerticalScroll(id="list"):
                yield Static(id="list-text", markup=False)
            with VerticalScroll(id="value"):
                yield Static(id="value-text", markup=False)
        yield Input(id="entry")

    @property
    def list_column(self) -> VerticalScroll:
        """The left column."""
        return self.query_one("#list", VerticalScroll)

    @property
    def value_column(self) -> VerticalScroll:
        """The right column."""
        return self.query_one("#value", VerticalScroll)

    def on_mount(self) -> None:
        """Name the panels, select the theme, and tie the two columns together."""
        self._apply_width()
        self.register_theme(self._theme())
        self.theme = THEME_NAME
        self.list_column.border_title = "List"
        self.value_column.border_title = "Value"
        self.watch(self.list_column, "scroll_y", self._follow_scroll, init=False)
        self.query_one("#entry", Input).focus()
        self.refresh_columns()

    def _theme(self) -> Theme:
        """Build the Textual theme from the palette."""
        return Theme(
            name=THEME_NAME,
            primary=self.palette.value,
            accent=self.palette.variable,
            error=self.palette.error,
            success=self.palette.command,
            warning=self.palette.exponent,
            foreground=self.palette.text,
            background=self.palette.background,
            surface=self.palette.background,
            panel=self.palette.background,
            dark=True,
            variables=self.get_theme_variable_defaults(),
        )

    def _follow_scroll(self, scroll_y: float) -> None:
        """Keep the right column on the row the left column shows."""
        # force: the right column hides its scrollbar, which otherwise blocks the scroll.
        self.value_column.scroll_to(y=scroll_y, animate=False, force=True, immediate=True)

    def refresh_columns(self) -> None:
        """Redraw both columns from the session.

        Each row is padded to the width of its column, so the stripe of a row
        covers the column from edge to edge.
        """
        colors = self.palette.colors
        rows = self.session.rows
        self.query_one("#list-text", Static).update(
            build_list_text(rows, colors, self.stripes, self._column_width(self.list_column))
        )
        self.query_one("#value-text", Static).update(
            build_value_text(rows, colors, self.stripes, self._column_width(self.value_column))
        )

    @staticmethod
    def _column_width(column: VerticalScroll) -> int:
        """The columns the rows of one panel can use."""
        return column.container_size.width

    def on_resize(self) -> None:
        """Repad the rows for the new column widths."""
        self.refresh_columns()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Evaluate the typed line, then add it to the List."""
        evaluate_line(self.session, event.value)
        event.input.value = ""
        self.refresh_columns()
        self.list_column.scroll_end(animate=False)
        self.run_effects()

    def run_effects(self) -> None:
        """Do the work the line asked the UI for, such as showing the help."""
        for effect in self.session.take_effects():
            handler = self.EFFECTS.get(effect)
            if handler is not None:
                handler(self)

    def show_help(self) -> None:
        """Open the help dialog."""
        self.push_screen(HelpScreen(self.palette.colors))

    EFFECTS: ClassVar[dict[str, Callable[[AdderApp], None]]] = {HELP_EFFECT: show_help}
    """What each requested effect does. A new effect is one more entry here."""
