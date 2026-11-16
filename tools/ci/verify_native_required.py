#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail-closed checks for real native matrix legs in the current GitHub run attempt."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.request import Request, urlopen

PLATFORMS = ("linux-x64", "linux-arm64", "windows-x64")
PREFIX = "native build "
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def should_run(event: str, scope_result: str, code: str) -> bool:
    """Match the workflow gate: only successfully classified notes-only PRs skip."""
    return not (event == "pull_request" and scope_result == "success" and code == "false")


def identity(repo: str, run: str, attempt: str) -> tuple[int, int]:
    if not REPOSITORY.fullmatch(repo):
        raise ValueError("invalid GitHub repository")
    if not run.isascii() or not run.isdecimal() or int(run) < 1:
        raise ValueError("invalid run ID")
    if not attempt.isascii() or not attempt.isdecimal() or int(attempt) < 1:
        raise ValueError("invalid current run attempt")
    return int(run), int(attempt)


def verify_jobs(payload: object, *, repo: str, run: int, attempt: int,
                platform: str, matrix_result: str) -> None:
    if platform not in PLATFORMS:
        raise ValueError("unknown native platform")
    if matrix_result != "success":
        raise ValueError(f"native matrix did not succeed: {matrix_result!r}")
    if not isinstance(payload, dict):
        raise ValueError("invalid jobs API response")
    jobs = payload.get("jobs")
    count = payload.get("total_count")
    if (not isinstance(jobs, list) or type(count) is not int or count != len(jobs)
            or count > 100):
        raise ValueError("missing or incomplete jobs inventory")
    expected_url = f"https://api.github.com/repos/{repo}/actions/runs/{run}"
    seen_ids: set[int] = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("invalid job entry")
        job_id = job.get("id")
        if type(job_id) is not int or job_id < 1 or job_id in seen_ids:
            raise ValueError("missing or duplicate job ID")
        seen_ids.add(job_id)
        if (type(job.get("run_id")) is not int or job["run_id"] != run
                or type(job.get("run_attempt")) is not int or job["run_attempt"] != attempt
                or job.get("run_url") != expected_url):
            raise ValueError(f"job {job_id} has wrong repository/run/current attempt")
        if not isinstance(job.get("name"), str):
            raise ValueError(f"job {job_id} has no name")
    native = [job for job in jobs if job["name"].startswith(PREFIX)]
    names = sorted(job["name"] for job in native)
    expected = sorted(PREFIX + p for p in PLATFORMS)
    if names != expected:
        raise ValueError(f"native jobs missing/duplicate/unexpected: {names}; expected {expected}")
    target = next(job for job in native if job["name"] == PREFIX + platform)
    if target.get("status") != "completed" or target.get("conclusion") != "success":
        raise ValueError(f"{target['name']} incomplete or unsuccessful: "
                         f"{target.get('status')}/{target.get('conclusion')}")


def fetch_jobs(repo: str, run: int, attempt: int) -> object:
    # Attempt-scoped endpoint, not the unscoped run/jobs URL. No token or retries.
    url = (f"https://api.github.com/repos/{repo}/actions/runs/{run}"
           f"/attempts/{attempt}/jobs?per_page=100")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "wirescape-required-native-check",
    })
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=PLATFORMS)
    platform = parser.parse_args().platform
    try:
        if not should_run(os.environ.get("GITHUB_EVENT_NAME", ""),
                          os.environ.get("SCOPE_RESULT", ""),
                          os.environ.get("SCOPE_CODE", "")):
            raise ValueError("notes-only PR must skip this check")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run, attempt = identity(repo, os.environ.get("GITHUB_RUN_ID", ""),
                                os.environ.get("GITHUB_RUN_ATTEMPT", ""))
        matrix = os.environ.get("NATIVE_MATRIX_RESULT", "")
        if matrix != "success":
            raise ValueError(f"native matrix did not succeed: {matrix!r}")
        verify_jobs(fetch_jobs(repo, run, attempt), repo=repo, run=run,
                    attempt=attempt, platform=platform, matrix_result=matrix)
    except Exception as exc:
        print(f"Required native check failed closed: {exc}", file=sys.stderr)
        return 1
    print(f"Verified real native build {platform} in run {run}, attempt {attempt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
