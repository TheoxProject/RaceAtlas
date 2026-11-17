"""Shared bounded errors for the CLI and its fixture, including ``python -m``."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProofError(Exception):
    """Only fixed codes, never raw driver details, may cross the CLI boundary."""


def require(condition, code):
    if not condition:
        raise ProofError(code)
