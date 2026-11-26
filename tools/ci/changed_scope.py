#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail-closed, plain-git PR changed-path classifier for Lab CI."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterable

_SHA = re.compile(r"[0-9a-fA-F]{40}\Z")


def is_notes_path(path: str) -> bool:
    """Return True only for paths in the CI1 r1 K4-vetted notes scope."""
    if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    if len(parts) == 1:
        return path.endswith(".md")
    if parts[0] == "proposals":
        return True
    if parts[:2] in (["docs", "context"], ["docs", "workflow"]):
        return len(parts) >= 3
    if parts[0] == "docs":
        # Proposal 0023 R1.3 (CI-S1): prose guides are notes; specs stay code.
        return parts[1] != "specs" and path.endswith(".md")
    return parts[0] == "facts" and parts[1] != "dsp"


def requires_code(paths: Iterable[str]) -> bool:
    """Empty, unknown or mixed path sets all require the complete CI suite."""
    changed = list(paths)
    return not changed or any(not is_notes_path(path) for path in changed)


# Deliberately narrow allowlist: only native engine implementation and native
# engine tests. Unknown paths, generated catalogues, control/host interfaces,
# configuration, fixtures and UI inputs keep the complete browser suite.
# The actual desktop sidecar E2E still runs on these engine-only drafts.
_ENGINE_CORE = frozenset({
    "build.cpp", "edit.cpp", "engine2.cpp", "engine2.h", "impl.h",
    "instance.h", "layout.h", "midi_release.h", "render.cpp", "types.h",
})


def is_studio_independent_path(path: str) -> bool:
    if is_notes_path(path):
        return True
    if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return len(parts) == 2 and parts[0] == "engine" and parts[1] in _ENGINE_CORE


def requires_studio(paths: Iterable[str]) -> bool:
    """Empty, unknown or any UI-dependent input requires the UI suite."""
    changed = list(paths)
    return not changed or any(not is_studio_independent_path(p) for p in changed)


def git_changed_paths(base: str, head: str) -> list[str]:
    if not _SHA.fullmatch(base or "") or not _SHA.fullmatch(head or ""):
        raise ValueError("missing or invalid pull-request commit SHA")
    completed = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--no-renames", "--name-only",
         "-z", f"{base}...{head}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    raw = completed.stdout
    if raw and not raw.endswith(b"\0"):
        raise ValueError("git diff path stream has no NUL terminator")
    return [part.decode("utf-8", errors="strict") for part in raw.split(b"\0") if part]


def classify_scopes(event: str, base: str = "", head: str = "") -> tuple[bool, bool]:
    """One git diff for both outputs; errors and non-PR events run everything."""
    if event != "pull_request":
        return True, True
    try:
        paths = git_changed_paths(base, head)
        return requires_code(paths), requires_studio(paths)
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
        print(f"changed scope unavailable; running full suite: {error}", file=sys.stderr)
        return True, True


def classify(event: str, base: str = "", head: str = "") -> bool:
    """Retain the CI1 code-only classification API."""
    return classify_scopes(event, base, head)[0]


def main() -> int:
    code, studio = classify_scopes(
        os.environ.get("CI_EVENT_NAME", ""),
        os.environ.get("CI_BASE_SHA", ""),
        os.environ.get("CI_HEAD_SHA", ""),
    )
    lines = f"code={str(code).lower()}\nstudio={str(studio).lower()}\n"
    print(lines, end="")
    # A failed output write fails the scope job; consumers still run full CI.
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
