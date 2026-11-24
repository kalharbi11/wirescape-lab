#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail-closed authenticated checks for native and Studio jobs in the current run attempt."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.request import HTTPRedirectHandler, Request, build_opener

PLATFORMS = ("linux-x64", "linux-arm64", "windows-x64")
PREFIX = "native build "
STUDIO = tuple(f"studio shard {i}/4" for i in (1, 2, 3, 4))
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def should_run(event: str, scope_result: str, code: str) -> bool:
    return not (event == "pull_request" and scope_result == "success" and code == "false")


def identity(repo: str, run: str, attempt: str) -> tuple[int, int]:
    if not REPOSITORY.fullmatch(repo):
        raise ValueError("invalid GitHub repository")
    if not run.isascii() or not run.isdecimal() or int(run) < 1:
        raise ValueError("invalid run ID")
    if not attempt.isascii() or not attempt.isdecimal() or int(attempt) < 1:
        raise ValueError("invalid current run attempt")
    return int(run), int(attempt)


def _inventory(payload: object, *, repo: str, run: int, attempt: int) -> list[dict]:
    if not isinstance(payload, dict):
        raise ValueError("invalid jobs API response")
    jobs, count = payload.get("jobs"), payload.get("total_count")
    if not isinstance(jobs, list) or type(count) is not int or count != len(jobs) or count > 100:
        raise ValueError("missing or incomplete jobs inventory")
    expected_url = f"https://api.github.com/repos/{repo}/actions/runs/{run}"
    seen: set[int] = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("invalid job entry")
        job_id = job.get("id")
        if type(job_id) is not int or job_id < 1 or job_id in seen:
            raise ValueError("missing or duplicate job ID")
        seen.add(job_id)
        if (type(job.get("run_id")) is not int or job["run_id"] != run
                or type(job.get("run_attempt")) is not int or job["run_attempt"] != attempt
                or job.get("run_url") != expected_url):
            raise ValueError("job has wrong repository/run/current attempt")
        if not isinstance(job.get("name"), str):
            raise ValueError("job has no name")
    return jobs


def verify_jobs(payload: object, *, repo: str, run: int, attempt: int,
                platform: str, matrix_result: str) -> None:
    if platform not in PLATFORMS:
        raise ValueError("unknown native platform")
    if matrix_result != "success":
        raise ValueError("native matrix did not succeed")
    native = [job for job in _inventory(payload, repo=repo, run=run, attempt=attempt)
              if job["name"].startswith(PREFIX)]
    if sorted(job["name"] for job in native) != sorted(PREFIX + p for p in PLATFORMS):
        raise ValueError("native jobs missing/duplicate/unexpected")
    for job in native:
        if job.get("status") != "completed" or job.get("conclusion") != "success":
            raise ValueError("native job incomplete or unsuccessful")


def verify_studio(payload: object, *, repo: str, run: int, attempt: int,
                  matrix_result: str) -> None:
    if matrix_result != "success":
        raise ValueError("studio matrix did not succeed")
    studio = [job for job in _inventory(payload, repo=repo, run=run, attempt=attempt)
              if job["name"].startswith("studio shard ")]
    if sorted(job["name"] for job in studio) != sorted(STUDIO):
        raise ValueError("studio shards missing/duplicate/unexpected")
    for job in studio:
        if job.get("status") != "completed" or job.get("conclusion") != "success":
            raise ValueError("studio shard incomplete or unsuccessful")


class _NoRedirect(HTTPRedirectHandler):
    """Never forward an Authorization header to a redirected host."""
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch_jobs(repo: str, run: int, attempt: int, token: str) -> object:
    if not token or chr(10) in token or chr(13) in token:
        raise ValueError("missing or invalid Actions token")
    url = (f"https://api.github.com/repos/{repo}/actions/runs/{run}"
           f"/attempts/{attempt}/jobs?per_page=100")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "wirescape-required-check",
        "Authorization": f"Bearer {token}",
    })
    with build_opener(_NoRedirect()).open(request, timeout=20) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--platform", choices=PLATFORMS)
    group.add_argument("--studio", action="store_true")
    args = parser.parse_args()
    try:
        if not should_run(os.environ.get("GITHUB_EVENT_NAME", ""),
                          os.environ.get("SCOPE_RESULT", ""),
                          os.environ.get("SCOPE_CODE", "")):
            raise ValueError("notes-only PR must skip this check")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run, attempt = identity(repo, os.environ.get("GITHUB_RUN_ID", ""),
                                os.environ.get("GITHUB_RUN_ATTEMPT", ""))
        matrix = os.environ.get("STUDIO_MATRIX_RESULT" if args.studio else "NATIVE_MATRIX_RESULT", "")
        if matrix != "success":
            raise ValueError("matrix did not succeed")
        jobs = fetch_jobs(repo, run, attempt, os.environ.get("ACTIONS_READ_TOKEN", ""))
        if args.studio:
            verify_studio(jobs, repo=repo, run=run, attempt=attempt, matrix_result=matrix)
        else:
            verify_jobs(jobs, repo=repo, run=run, attempt=attempt,
                        platform=args.platform, matrix_result=matrix)
    except Exception as exc:
        # Never print exception text, untrusted API content, token, URL, or headers.
        print(f"Required aggregate check failed closed ({type(exc).__name__})", file=sys.stderr)
        return 1
    print(f"Verified {'Studio shards' if args.studio else 'native ' + args.platform}"
          f" in run {run}, attempt {attempt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
