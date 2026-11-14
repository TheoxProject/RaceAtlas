from pathlib import Path

import pytest

from ops.ci_selection import BROWSER, SEAMS, command, plan, select_backend, validation_mode

AVAILABLE = {"tests/backend/" + name for names in SEAMS.values() for name in names} | {
    "tests/backend/" + name for name in BROWSER
}
DRAFT = {"pull_request": {"draft": True, "labels": []}}


def test_draft_documents_are_explicit_no_backend_and_never_integrated():
    selected = plan(
        "pull_request", DRAFT, ["docs/lot-7/accounts-ui-mission.md", "AGENTS.md"], AVAILABLE
    )
    assert selected["mode"] == "development" and selected["backend"] == "none"
    assert command(selected, "report.xml") is None


@pytest.mark.parametrize(
    "event,body",
    [
        ("push", {}),
        ("pull_request", {"pull_request": {"draft": False}}),
        ("pull_request", {"pull_request": {"draft": True, "labels": [{"name": "ci:full"}]}}),
        ("pull_request", {"pull_request": {"draft": True, "labels": [{"name": "CI:FULL"}]}}),
    ],
)
def test_integration_gate_always_runs_all_backend_even_docs(event, body):
    selected = plan(event, body, ["README.md"], AVAILABLE)
    assert (
        selected["mode"] == "integrated" and selected["backend"] == "full" and selected["browser"]
    )
    assert command(selected, "report.xml")[-1] == "--junitxml=report.xml"


def test_known_http_and_frontend_seams_include_browsers_and_new_tests():
    available = AVAILABLE | {"tests/backend/test_new_feature.py"}
    selected = plan(
        "pull_request",
        DRAFT,
        ["raceatlas/auth/csrf.py", "frontend/src/App.jsx", "tests/backend/test_new_feature.py"],
        available,
    )
    assert selected["mode"] == "development" and selected["backend"] == "targeted"
    assert {"tests/backend/" + name for name in BROWSER}.issubset(selected["tests"])
    assert "tests/backend/test_auth_http_foundation.py" in selected["tests"]
    assert "tests/backend/test_new_feature.py" in selected["tests"]
    assert selected["browser"]


@pytest.mark.parametrize(
    "path",
    [
        "raceatlas/auth/core.py",
        "raceatlas/models.py",
        "migrations/versions/new.py",
        "tests/backend/conftest.py",
        "requirements-dev.txt",
        "frontend/pnpm-lock.yaml",
        "frontend/vite.config.js",
        "frontend/.npmrc",
        "unexpected/file",
    ],
)
def test_unknown_runtime_or_shared_config_falls_back_full_but_not_integrated(path):
    selected = plan("pull_request", DRAFT, [path], AVAILABLE)
    assert (
        selected["backend"] == "full" and selected["mode"] == "development" and selected["browser"]
    )


def test_missing_deleted_seam_and_unsafe_argv_cannot_skip():
    assert select_backend(["raceatlas/auth/csrf.py"], set())["backend"] == "full"
    with pytest.raises(ValueError):
        command(
            {"mode": "integrated", "backend": "targeted", "tests": ["tests/backend/test_new.py"]},
            "x.xml",
        )
    with pytest.raises(ValueError):
        command({"mode": "development", "backend": "targeted", "tests": ["--override"]}, "x.xml")


def test_real_seams_exist_and_workflow_retains_full_gate_and_guards():
    actual = {path.as_posix() for path in Path("tests/backend").glob("test_*.py")}
    assert AVAILABLE.issubset(actual)
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    for event in ("labeled", "unlabeled", "ready_for_review", "converted_to_draft"):
        assert event in workflow
    assert "persist-credentials: false" in workflow and "contents: read" in workflow
    assert "pull_request_target" not in workflow
    assert "raceatlas-check-source.sh" in workflow and "ci:full" in workflow
    assert validation_mode("pull_request", DRAFT) == "development"
