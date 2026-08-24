"""The stripe pattern.

Textual CSS has no `linear-gradient`, and a background painted on the screen
never shows through the widgets above it. The stripes are therefore part of
each row: a row in a shaded band carries the shade as its background color.
That also keeps a stripe with its row while the List scrolls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adder.config import Palette


@dataclass(frozen=True)
class Stripes:
    """Bands of shaded rows, like a repeating linear gradient with hard stops.

    Args:
        shade: The background color of a shaded row.
        background: The background color of a plain row.
        band: The height of one band, in rows.
    """

    shade: str
    background: str
    band: int = 1

    @classmethod
    def from_palette(cls, palette: Palette, band: int) -> Stripes:
        """Build the pattern from the palette."""
        return cls(shade=palette.stripe, background=palette.background, band=band)

    @property
    def is_plain(self) -> bool:
        """True if the two colors are the same, which shows no stripes."""
        return self.shade == self.background

    def shade_for(self, row: int) -> str | None:
        """Return the background color of a row, or None if the row is plain."""
        if self.is_plain:
            return None
        band = max(1, self.band)
        return self.shade if (row // band) % 2 else None
