"""Built-in themes for Rigi.

Usage::

    from rigi.themes import DARK, LIGHT, MONOKAI, NORD, Theme
"""

from rigi.themes.base import Theme
from rigi.themes.dark import DARK
from rigi.themes.light import LIGHT
from rigi.themes.monokai import MONOKAI
from rigi.themes.nord import NORD

__all__ = ["Theme", "DARK", "LIGHT", "MONOKAI", "NORD"]
