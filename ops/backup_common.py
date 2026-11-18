"""Shared bounded errors for the CLI and its fixture, including ``python -m``."""

from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]


class ProofError(Exception):
    """Only fixed codes, never raw driver details, may cross the CLI boundary."""


def require(condition, code):
    if not condition:
        raise ProofError(code)


def guard_path(path, code="symlink_path"):
    """Inspect outer components before child access; not a TOCTOU/admin boundary."""
    absolute = Path(path).absolute()
    current = Path(absolute.anchor)
    for part in (None, *absolute.parts[1:]):
        if part is not None:
            current /= part
        try:
            require(not current.is_symlink() and not current.is_junction(), code)
        except OSError:
            raise ProofError(code) from None
