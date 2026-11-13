"""Local exact whole-secret policy for setters only; existing login is unchanged."""

import gzip
import hashlib
from functools import lru_cache
from pathlib import Path

from .errors import InvalidPassword
from .passwords import password_bytes

CORPUS = Path(__file__).with_name("data") / "common-passwords-django-6.0.txt.gz"
DIGEST = "3c1baed62596de36860824eb3f436d5932d37ca8b06e59df78f5a44ec175afe4"


@lru_cache(maxsize=1)
def common_passwords():
    compressed = CORPUS.read_bytes()
    if len(compressed) != 80228 or hashlib.sha256(compressed).hexdigest() != DIGEST:
        raise RuntimeError("Password corpus unavailable.")
    with gzip.open(CORPUS, "rb") as stream:
        decoded = stream.read(1048577)
    if len(decoded) > 1048576:
        raise RuntimeError("Password corpus unavailable.")
    return frozenset(decoded.decode("utf-8").splitlines())


def validate_new_password(password):
    password_bytes(password)
    if password in common_passwords():
        raise InvalidPassword()
