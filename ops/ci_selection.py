"""Conservative stdlib-only draft selection; integration mode always discovers ALL tests."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SEAMS = {
    "raceatlas/__init__.py": {"test_foundation.py", "test_hosting.py"},
    "raceatlas/auth/csrf.py": {
        "test_auth_http_foundation.py",
        "test_auth_http_sessions.py",
        "test_account_read_context.py",
    },
    "raceatlas/auth/sessions_http.py": {
        "test_auth_http_foundation.py",
        "test_auth_http_sessions.py",
        "test_account_read_context.py",
    },
    "raceatlas/planning_http.py": {
        "test_private_planning.py",
        "test_personal_calendar.py",
        "test_account_read_context.py",
    },
    "contracts/auth.openapi.json": {
        "test_auth_http_foundation.py",
        "test_auth_http_sessions.py",
        "test_auth_http_email.py",
        "test_account_read_context.py",
    },
    "contracts/planning.openapi.json": {
        "test_private_planning.py",
        "test_personal_calendar.py",
        "test_account_read_context.py",
    },
    "contracts/planning.schema.json": {"test_private_planning.py", "test_personal_calendar.py"},
    "ops/ci_selection.py": {"test_ci_selection.py"},
    ".github/workflows/ci.yml": {"test_ci_selection.py"},
}
BROWSER = {"test_e2e.py", "test_calendar_e2e.py", "test_accounts_ui_e2e.py"}
TEST = re.compile(r"tests/backend/test_[A-Za-z0-9_]+\.py\Z")


def validation_mode(event_name, event):
    pr = event.get("pull_request", {})
    labels = pr.get("labels", [])
    full = any(
        isinstance(label, dict) and str(label.get("name", "")).lower() == "ci:full"
        for label in labels
    )
    return (
        "development"
        if event_name == "pull_request" and pr.get("draft") is True and not full
        else "integrated"
    )


def select_backend(paths, available):
    selected = set()
    paths = set(paths)
    for path in paths:
        if path == "tests/backend/conftest.py" or path in {
            "requirements.txt",
            "requirements-dev.txt",
            "constraints.txt",
            "frontend/package.json",
            "frontend/pnpm-lock.yaml",
            ".env.example",
        }:
            return {"backend": "full", "tests": [], "reason": "shared-config-or-dependencies"}
        if path in SEAMS:
            selected.update("tests/backend/" + name for name in SEAMS[path])
        elif TEST.fullmatch(path):
            selected.add(path)
        elif path.startswith("frontend/src/") or path == "frontend/index.html":
            selected.update("tests/backend/" + name for name in BROWSER)
        elif path.startswith("docs/") or path in {"AGENTS.md", "README.md"}:
            continue
        else:
            return {"backend": "full", "tests": [], "reason": "unclassified-change"}
    # Missing/deleted/symlink test files must not turn a regression into a silent skip.
    if not selected.issubset(available):
        return {"backend": "full", "tests": [], "reason": "missing-seam"}
    return {
        "backend": "targeted" if selected else "none",
        "tests": sorted(selected),
        "reason": "known-seams" if selected else "docs-only-or-empty",
    }


def changed_paths(base, head):
    if not re.fullmatch(r"[a-f0-9]{40}", base) or not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("Missing verified base/head SHA")
    present = subprocess.run(["git", "cat-file", "-e", base + "^{commit}"], capture_output=True)
    if present.returncode:
        subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", base], check=True)
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", base, head], check=True, capture_output=True
    )
    return result.stdout.decode("utf-8").rstrip("\0").split("\0") if result.stdout else []


def plan(event_name, event, paths, available):
    mode = validation_mode(event_name, event)
    selection = (
        {"backend": "full", "tests": [], "reason": "required-integration"}
        if mode == "integrated"
        else select_backend(paths, available)
    )
    selection["mode"] = mode
    selection["browser"] = selection["backend"] == "full" or any(
        Path(path).name in BROWSER for path in selection["tests"]
    )
    return selection


def command(selection, junit):
    if selection.get("mode") not in {"development", "integrated"} or selection.get(
        "backend"
    ) not in {"full", "targeted", "none"}:
        raise ValueError("Invalid validation mode")
    if selection["mode"] == "integrated" and selection["backend"] != "full":
        raise ValueError("Integration cannot select a partial suite")
    if selection["backend"] == "none":
        return None
    tests = selection.get("tests", [])
    if selection["backend"] == "targeted" and (
        not tests or any(not TEST.fullmatch(path) for path in tests)
    ):
        raise ValueError("Invalid targeted test path")
    return [sys.executable, "-m", "pytest", "-v", "--junitxml=" + str(junit)] + (
        tests if selection["backend"] == "targeted" else []
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--junit", type=Path)
    args = parser.parse_args()
    if args.run:
        selected = json.loads(args.run.read_text(encoding="utf-8"))
        argv = command(selected, args.junit)
        if argv is None:
            print("Development: no backend selected (docs-only/empty); not an integration gate.")
            return 0
        return subprocess.run(argv).returncode
    if not args.plan:
        parser.error("--plan or --run is required")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    event_name = os.environ["GITHUB_EVENT_NAME"]
    mode = validation_mode(event_name, event)
    paths = (
        changed_paths(os.environ.get("PR_BASE_SHA", ""), os.environ["EXPECTED_SOURCE_SHA"])
        if mode == "development"
        else []
    )
    available = {
        p.as_posix()
        for p in Path("tests/backend").glob("test_*.py")
        if p.is_file() and not p.is_symlink()
    }
    selected = plan(event_name, event, paths, available)
    args.plan.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for key in ("mode", "backend", "reason", "browser"):
            print(f"{key}={str(selected[key]).lower()}", file=output)
    print(
        f"Validation {selected['mode']}; backend={selected['backend']}; "
        f"reason={selected['reason']}; selected={len(selected['tests'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
