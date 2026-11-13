import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock
from types import SimpleNamespace

import pytest
from argon2 import extract_parameters
from argon2.exceptions import HashingError
from argon2.low_level import Type

from raceatlas.auth import passwords
from raceatlas.auth.errors import AuthenticationUnavailable, InvalidPassword


@pytest.mark.parametrize(
    "secret",
    [
        "a" * 15,
        " " * 15,
        " Mixed Case passphrase ",
        "é" * 15,
        "🚲" * 128,
        "x" * 128,
        "\x00" + "a" * 14,
    ],
)
def test_real_argon2id_exact_unicode_policy_and_fresh_salts(secret):
    first, second = passwords.hash_password(secret), passwords.hash_password(secret)
    params = extract_parameters(first)
    assert (
        params.type,
        params.version,
        params.memory_cost,
        params.time_cost,
        params.parallelism,
        params.salt_len,
        params.hash_len,
    ) == (Type.ID, 19, 19456, 2, 1, 16, 32)
    assert first != second and secret not in first
    assert passwords.verify_password(first, secret)
    assert not passwords.verify_password(first, secret + "!")


def test_password_is_not_trimmed_lowercased_or_unicode_normalized():
    phc = passwords.hash_password("  Éxact Secret Phrase  ")
    assert passwords.verify_password(phc, "  Éxact Secret Phrase  ")
    for changed in [
        "Éxact Secret Phrase",
        "  éxact secret phrase  ",
        "  E\u0301xact Secret Phrase  ",
    ]:
        assert not passwords.verify_password(phc, changed)


@pytest.mark.parametrize(
    "value", [None, 1, {}, "a" * 14, "a" * 129, "x" * 14 + "\ud800", "x" * 14 + "\udfff"]
)
def test_invalid_passwords_are_bounded_and_generic(value):
    with pytest.raises(InvalidPassword, match="^Invalid password\\.$"):
        passwords.hash_password(value)
    assert not passwords.verify_password("invalid", value)


@pytest.mark.parametrize(
    "phc",
    [None, "", "x" * 513, "not-a-phc", "$argon2id$v=19$m=999999999,t=2,p=1$a$b", "\ud800", "\x00"],
)
def test_malformed_or_unbounded_phc_never_requests_native_kdf(phc, monkeypatch):
    def forbidden(*args):
        raise AssertionError("Malformed PHC reached KDF")

    monkeypatch.setattr(passwords, "_hasher", SimpleNamespace(verify=forbidden))
    assert not passwords.verify_password(phc, "synthetic valid passphrase")


def test_real_kdf_work_is_bounded_and_slots_release(monkeypatch):
    original_hasher = passwords._hasher
    original = original_hasher.hash
    gate, release, lock = Event(), Event(), Lock()
    state = {"active": 0, "peak": 0}

    def observed(secret):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            if state["active"] == 2:
                gate.set()
        try:
            assert release.wait(5)
            return original(secret)
        finally:
            with lock:
                state["active"] -= 1

    monkeypatch.setattr(
        passwords, "_hasher", SimpleNamespace(hash=observed, verify=original_hasher.verify)
    )
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(passwords.hash_password, "synthetic bounded passphrase") for _ in range(3)
        ]
        try:
            assert gate.wait(5)
            assert state["peak"] == 2
        finally:
            release.set()
        hashes = [future.result(timeout=10) for future in futures]
    assert state == {"active": 0, "peak": 2}
    assert all(passwords.verify_password(phc, "synthetic bounded passphrase") for phc in hashes)


def test_kdf_wait_and_failure_are_bounded_without_leaking_input(monkeypatch):
    with passwords._kdf_slot(), passwords._kdf_slot():
        with pytest.raises(
            AuthenticationUnavailable, match="^Authentication temporarily unavailable\\.$"
        ):
            passwords.hash_password("synthetic waiting passphrase")
    original_hasher = passwords._hasher

    def failure(*args):
        raise HashingError("synthetic native failure")

    monkeypatch.setattr(passwords, "_hasher", SimpleNamespace(hash=failure))
    with pytest.raises(
        AuthenticationUnavailable, match="^Authentication temporarily unavailable\\.$"
    ):
        passwords.hash_password("synthetic error passphrase")
    monkeypatch.setattr(passwords, "_hasher", original_hasher)
    assert passwords.verify_password(
        passwords.hash_password("synthetic recovered phrase"), "synthetic recovered phrase"
    )


def test_record_current_local_cost_without_secrets():
    hashes_ms, verify_ms = [], []
    for _ in range(3):
        started = time.perf_counter()
        phc = passwords.hash_password("synthetic measurement phrase")
        hashes_ms.append(round((time.perf_counter() - started) * 1000, 2))
        started = time.perf_counter()
        assert passwords.verify_password(phc, "synthetic measurement phrase")
        verify_ms.append(round((time.perf_counter() - started) * 1000, 2))
    output = Path(".local-tools/auth-kdf-cost.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "hash_ms": hashes_ms,
                "verify_ms": verify_ms,
                "max_concurrent": 2,
                "memory_parameter_kib": 19456,
                "rss_or_render_measured": False,
            }
        ),
        encoding="utf-8",
    )
