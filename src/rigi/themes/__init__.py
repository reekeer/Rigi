"""Built-in themes for Rigi.

Usage::

    from rigi.themes import DARK, LIGHT, MONOKAI, NORD, RigiTheme
"""

from rigi.themes.base import RigiTheme
from rigi.themes.dark import DARK
from rigi.themes.light import LIGHT
from rigi.themes.monokai import MONOKAI
from rigi.themes.nord import NORD

__all__ = ["RigiTheme", "DARK", "LIGHT", "MONOKAI", "NORD"]
