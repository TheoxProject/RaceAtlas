"""Public catalogue API selection, independent of frontend views."""

from .selection import select_page
from .validation import CatalogError, parse_query

__all__ = ["CatalogError", "parse_query", "select_page"]
