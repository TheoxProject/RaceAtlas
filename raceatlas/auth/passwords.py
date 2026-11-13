"""Fixed Argon2id policy, exact UTF-8 passwords and bounded per-process KDF work."""

from contextlib import contextmanager
from secrets import token_urlsafe
from threading import BoundedSemaphore

from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import HashingError, InvalidHashError, VerificationError
from argon2.low_level import Type

from .errors import AuthenticationUnavailable, InvalidPassword

MAX_KDF_CONCURRENCY = 2
_slots = BoundedSemaphore(MAX_KDF_CONCURRENCY)
_hasher = PasswordHasher(
    memory_cost=19456,
    time_cost=2,
    parallelism=1,
    salt_len=16,
    hash_len=32,
    type=Type.ID,
    encoding="utf-8",
)


def password_bytes(value):
    if not isinstance(value, str) or not 15 <= len(value) <= 128:
        raise InvalidPassword()
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        raise InvalidPassword() from None
    if len(encoded) > 512:
        raise InvalidPassword()
    return encoded


@contextmanager
def _kdf_slot():
    # Bounded workers and bounded wait; HTTP abuse controls belong to ACC-02C.
    if not _slots.acquire(timeout=1):
        raise AuthenticationUnavailable()
    try:
        yield
    finally:
        _slots.release()


def hash_password(value):
    encoded = password_bytes(value)
    with _kdf_slot():
        try:
            return _hasher.hash(encoded)
        except HashingError:
            raise AuthenticationUnavailable() from None


def verify_password(phc, value):
    try:
        encoded = password_bytes(value)
    except InvalidPassword:
        return False
    if not isinstance(phc, str) or not 1 <= len(phc) <= 512 or not phc.isascii() or "\x00" in phc:
        return False
    try:
        parameters = extract_parameters(phc)
    except (InvalidHashError, ValueError):
        return False
    # Do not allow a corrupted/untrusted PHC string to request a larger KDF budget.
    if (
        parameters.type,
        parameters.version,
        parameters.memory_cost,
        parameters.time_cost,
        parameters.parallelism,
        parameters.salt_len,
        parameters.hash_len,
    ) != (Type.ID, 19, 19456, 2, 1, 16, 32):
        return False
    with _kdf_slot():
        try:
            return _hasher.verify(phc, encoded)
        except (VerificationError, InvalidHashError):
            return False


# Random dummy PHC, never a usable credential or returned secret. Same KDF budget.
_dummy_hash = hash_password(token_urlsafe(32))


def dummy_verify(value):
    verify_password(_dummy_hash, value)
