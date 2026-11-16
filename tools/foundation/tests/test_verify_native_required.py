# SPDX-License-Identifier: GPL-3.0-only
"""CI1 r2 K6: current-attempt native required checks, including fail-closed paths."""
from __future__ import annotations

import copy
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ci"))
import verify_native_required as native  # noqa: E402

REPO = "kalharbi11/wirescape-lab"
RUN, ATTEMPT = 123456, 3
URL = f"https://api.github.com/repos/{REPO}/actions/runs/{RUN}"


def fixture():
    jobs = [
        {"id": n + 1, "name": f"native build {platform}", "run_id": RUN,
         "run_attempt": ATTEMPT, "run_url": URL, "status": "completed",
         "conclusion": "success"} for n, platform in enumerate(native.PLATFORMS)
    ]
    jobs.append({"id": 4, "name": "foundation", "run_id": RUN,
                 "run_attempt": ATTEMPT, "run_url": URL, "status": "completed",
                 "conclusion": "success"})
    return {"total_count": len(jobs), "jobs": jobs}


def verify(payload, platform="linux-x64", matrix_result="success"):
    native.verify_jobs(payload, repo=REPO, run=RUN, attempt=ATTEMPT,
                       platform=platform, matrix_result=matrix_result)


class NativeRequiredTests(unittest.TestCase):
    def test_all_three_real_platforms_pass(self):
        for platform in native.PLATFORMS:
            with self.subTest(platform=platform):
                verify(fixture(), platform)

    def test_missing_and_duplicate_target(self):
        for mode in ("missing", "duplicate"):
            p = fixture()
            if mode == "missing":
                p["jobs"].pop(0)
            else:
                duplicate = copy.deepcopy(p["jobs"][0])
                duplicate["id"] = 9
                p["jobs"].append(duplicate)
            p["total_count"] = len(p["jobs"])
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "missing/duplicate"):
                verify(p)

    def test_other_platform_missing_or_unexpected(self):
        for mode in ("missing", "unexpected"):
            p = fixture()
            if mode == "missing":
                p["jobs"].pop(1)
            else:
                unexpected = copy.deepcopy(p["jobs"][0])
                unexpected.update(id=9, name="native build unexpected")
                p["jobs"].append(unexpected)
            p["total_count"] = len(p["jobs"])
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "missing/duplicate"):
                verify(p)

    def test_failed_cancelled_skipped_and_incomplete(self):
        for status, conclusion in [
            ("completed", "failure"), ("completed", "cancelled"),
            ("completed", "skipped"), ("completed", None),
            ("in_progress", None), ("queued", None),
        ]:
            p = fixture()
            p["jobs"][1].update(status=status, conclusion=conclusion)
            with self.subTest(status=status, conclusion=conclusion):
                with self.assertRaisesRegex(ValueError, "incomplete or unsuccessful"):
                    verify(p, "linux-arm64")

    def test_native_dependency_failed_cancelled_or_skipped(self):
        for result in ("failure", "cancelled", "skipped", "", None):
            with self.subTest(result=result), self.assertRaisesRegex(ValueError, "matrix"):
                verify(fixture(), matrix_result=result)

    def test_incomplete_inventory_or_malformed_api(self):
        for p in [None, [], {}, {"jobs": []},
                  {"jobs": fixture()["jobs"], "total_count": 3},
                  {"jobs": fixture()["jobs"], "total_count": 5},
                  {"jobs": fixture()["jobs"], "total_count": True},
                  {"jobs": fixture()["jobs"], "total_count": 101}]:
            with self.subTest(response=str(p)[:45]), self.assertRaises(ValueError):
                verify(p)

    def test_malformed_job_missing_id_duplicate_id_or_missing_name(self):
        for mode in ("null", "missing_id", "duplicate_id", "bad_name"):
            p = fixture()
            if mode == "null":
                p["jobs"][0] = None
            elif mode == "missing_id":
                p["jobs"][0].pop("id")
            elif mode == "duplicate_id":
                p["jobs"][1]["id"] = 1
            else:
                p["jobs"][0]["name"] = None
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                verify(p)

    def test_stale_run_stale_attempt_and_wrong_repository(self):
        for key, value in [
            ("run_id", RUN - 1),
            ("run_attempt", ATTEMPT - 1),
            ("run_attempt", ATTEMPT + 1),
            ("run_attempt", None),
            ("run_url", "https://api.github.com/repos/other/repo/actions/runs/123456"),
        ]:
            p = fixture()
            p["jobs"][0][key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(ValueError, "wrong repository/run/current attempt"):
                    verify(p)

    def test_unknown_platform_and_invalid_run_identity(self):
        with self.assertRaisesRegex(ValueError, "unknown native platform"):
            verify(fixture(), "macos")
        self.assertEqual(native.identity(REPO, str(RUN), str(ATTEMPT)), (RUN, ATTEMPT))
        for repo, run, attempt in [
            ("invalid", str(RUN), "1"), ("owner/../repo", str(RUN), "1"),
            (REPO, "", "1"), (REPO, "0", "1"), (REPO, "-1", "1"),
            (REPO, "1", "0"), (REPO, "1", "-1"), (REPO, "1", "bad"),
        ]:
            with self.subTest(repo=repo, run=run, attempt=attempt):
                with self.assertRaises(ValueError):
                    native.identity(repo, run, attempt)

    def test_notes_only_skip(self):
        self.assertFalse(native.should_run("pull_request", "success", "false"))

    def test_push_manual_code_and_scope_failure_all_run(self):
        cases = [
            ("pull_request", "success", "true"), ("pull_request", "failure", "false"),
            ("pull_request", "cancelled", "false"), ("pull_request", "skipped", "false"),
            ("pull_request", "", ""), ("pull_request", "success", ""),
            ("push", "success", "false"), ("workflow_dispatch", "success", "false"),
            ("schedule", "success", "false"),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertTrue(native.should_run(*case))

    def test_attempt_scoped_url_and_api_failure(self):
        class Response:
            def __enter__(self):
                return io.BytesIO(json.dumps(fixture()).encode())
            def __exit__(self, *args):
                return False
        with mock.patch.object(native, "urlopen", return_value=Response()) as called:
            self.assertEqual(native.fetch_jobs(REPO, RUN, ATTEMPT), fixture())
            self.assertIn(f"/runs/{RUN}/attempts/{ATTEMPT}/jobs?per_page=100",
                          called.call_args.args[0].full_url)
            self.assertEqual(called.call_args.kwargs["timeout"], 20)
        with mock.patch.object(native, "urlopen", side_effect=URLError("API unavailable")):
            with self.assertRaises(URLError):
                native.fetch_jobs(REPO, RUN, ATTEMPT)

    def test_cli_api_failure_and_unexpected_notes_only_execution(self):
        env = {
            "GITHUB_REPOSITORY": REPO, "GITHUB_RUN_ID": str(RUN),
            "GITHUB_RUN_ATTEMPT": str(ATTEMPT), "GITHUB_EVENT_NAME": "pull_request",
            "SCOPE_RESULT": "success", "SCOPE_CODE": "true",
            "NATIVE_MATRIX_RESULT": "success",
        }
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(sys, "argv", ["check", "--platform", "linux-x64"]), \
             mock.patch.object(native, "fetch_jobs", side_effect=URLError("API down")):
            self.assertEqual(native.main(), 1)
        env["SCOPE_CODE"] = "false"
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(sys, "argv", ["check", "--platform", "linux-x64"]), \
             mock.patch.object(native, "fetch_jobs", side_effect=AssertionError("must not call")):
            self.assertEqual(native.main(), 1)

    def test_workflow_literal_checks_and_condition_identity(self):
        content = (Path(__file__).resolve().parents[3] /
                   ".github/workflows/ci.yml").read_text(encoding="utf-8")
        gate = ("if: " + chr(36) + "{{ always() && (github.event_name != 'pull_request' || "
                "needs.scope.result != 'success' || needs.scope.outputs.code != 'false') }}")
        for platform in native.PLATFORMS:
            with self.subTest(platform=platform):
                self.assertIn(f"  {platform}:\n    name: {platform}\n    needs: [scope, native]\n    {gate}", content)
                self.assertIn(f"python tools/ci/verify_native_required.py --platform {platform}", content)
        self.assertEqual(content.count("needs: [scope, native]"), 3)
        self.assertIn("name: native build " + chr(36) + "{{ matrix.name }}", content)


if __name__ == "__main__":
    unittest.main()
