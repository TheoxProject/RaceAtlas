"""Offline FFC observations. No HTTP client, scheduler or implicit persistence."""

from .parser import parse_calendar, parse_race
from .projection import IdentityAttestation, project_race
from .types import AdapterError, WindowRequest

__all__ = [
    "AdapterError",
    "IdentityAttestation",
    "WindowRequest",
    "parse_calendar",
    "parse_race",
    "project_race",
]
