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
from urllib.error import URLError, HTTPError

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

    def test_authenticated_attempt_scoped_url_and_no_redirect(self):
        class Response:
            def __enter__(self):
                return io.BytesIO(json.dumps(fixture()).encode())
            def __exit__(self, *args):
                return False
        sentinel = "LOCAL_FAKE_TOKEN_SENTINEL"
        with mock.patch.object(native, "build_opener") as build:
            build.return_value.open.return_value = Response()
            self.assertEqual(native.fetch_jobs(REPO, RUN, ATTEMPT, sentinel), fixture())
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header("Authorization"), "Bearer " + sentinel)
            self.assertEqual(request.host, "api.github.com")
            self.assertIn(f"/runs/{RUN}/attempts/{ATTEMPT}/jobs?per_page=100", request.full_url)
            self.assertEqual(build.return_value.open.call_args.kwargs["timeout"], 20)
            self.assertIsInstance(build.call_args.args[0], native._NoRedirect)
            self.assertIsNone(native._NoRedirect().redirect_request(
                request, None, 302, "Redirect", {}, "https://elsewhere.example/"))
            self.assertEqual(build.return_value.open.call_count, 1)
        with self.assertRaisesRegex(ValueError, "token"):
            native.fetch_jobs(REPO, RUN, ATTEMPT, "")

    def test_http_401_403_429_fail_without_fallback(self):
        token = "MOCK_TOKEN_SENSITIVE"
        for code in (401, 403, 429):
            with mock.patch.object(native, "build_opener") as build:
                build.return_value.open.side_effect = HTTPError(
                    "https://api.github.com/", code, token, {}, None)
                with self.subTest(code=code), self.assertRaises(HTTPError):
                    native.fetch_jobs(REPO, RUN, ATTEMPT, token)
                self.assertEqual(build.return_value.open.call_count, 1)

    def test_studio_shards_malformed_stale_duplicate_missing_failing(self):
        valid = fixture()
        valid["jobs"].extend(
            {"id": 10 + i, "name": f"studio shard {i + 1}/4",
             "run_id": RUN, "run_attempt": ATTEMPT, "run_url": URL,
             "status": "completed", "conclusion": "success"}
            for i in range(4))
        valid["total_count"] = len(valid["jobs"])
        native.verify_studio(valid, repo=REPO, run=RUN, attempt=ATTEMPT,
                             matrix_result="success")
        for mode in ("missing", "duplicate", "failed", "cancelled", "skipped",
                     "incomplete", "stale", "wrong_repository", "wrong_run",
                     "malformed", "incomplete_inventory", "unexpected"):
            p = copy.deepcopy(valid)
            if mode == "missing":
                p["jobs"].pop()
            elif mode == "duplicate":
                p["jobs"].append({**p["jobs"][-1], "id": 40})
            elif mode in ("failed", "cancelled", "skipped"):
                p["jobs"][-1]["conclusion"] = mode if mode != "failed" else "failure"
            elif mode == "incomplete":
                p["jobs"][-1].update(status="queued", conclusion=None)
            elif mode == "stale":
                p["jobs"][-1]["run_attempt"] = ATTEMPT - 1
            elif mode == "wrong_repository":
                p["jobs"][-1]["run_url"] = "https://api.github.com/repos/else/repo/actions/runs/123456"
            elif mode == "wrong_run":
                p["jobs"][-1]["run_id"] = RUN + 1
            elif mode == "malformed":
                p["jobs"][-1] = None
            elif mode == "incomplete_inventory":
                p["total_count"] -= 1
            elif mode == "unexpected":
                p["jobs"].append({**p["jobs"][-1], "id": 40, "name": "studio shard 5/4"})
            if mode not in ("incomplete_inventory",):
                p["total_count"] = len(p["jobs"])
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                native.verify_studio(p, repo=REPO, run=RUN, attempt=ATTEMPT,
                                     matrix_result="success")
        for value in ("failure", "cancelled", "skipped"):
            with self.assertRaisesRegex(ValueError, "matrix"):
                native.verify_studio(valid, repo=REPO, run=RUN, attempt=ATTEMPT,
                                     matrix_result=value)

    def test_cli_error_does_not_expose_token(self):
        secret = "MOCK_TOKEN_NOT_REAL"
        for is_studio in (False, True):
            env = {"GITHUB_REPOSITORY": REPO, "GITHUB_RUN_ID": str(RUN),
                   "GITHUB_RUN_ATTEMPT": str(ATTEMPT), "GITHUB_EVENT_NAME": "push",
                   "SCOPE_RESULT": "success", "SCOPE_CODE": "true",
                   "NATIVE_MATRIX_RESULT": "success", "STUDIO_MATRIX_RESULT": "success",
                   "ACTIONS_READ_TOKEN": secret}
            argv = ["check", "--studio"] if is_studio else ["check", "--platform", "linux-x64"]
            stderr = io.StringIO()
            with mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(native, "fetch_jobs", side_effect=HTTPError(
                     "https://api.github.com/", 403, secret, {}, None)) as called, \
                 mock.patch("sys.stderr", stderr):
                self.assertEqual(native.main(), 1)
                self.assertEqual(called.call_count, 1)
            self.assertNotIn(secret, stderr.getvalue())
            self.assertNotIn("Authorization", stderr.getvalue())

    def test_cli_unavailable_and_unexpected_notes_only_execution(self):
        env = {
            "GITHUB_REPOSITORY": REPO, "GITHUB_RUN_ID": str(RUN),
            "GITHUB_RUN_ATTEMPT": str(ATTEMPT), "GITHUB_EVENT_NAME": "pull_request",
            "SCOPE_RESULT": "success", "SCOPE_CODE": "true",
            "NATIVE_MATRIX_RESULT": "success", "ACTIONS_READ_TOKEN": "MOCK_TOKEN",
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
        # Split only at two-space job headings, not four-space job fields.
        # A search for "\n  " also matches the prefix of "    name:" and
        # silently truncates permission and verification-step assertions.
        import re
        match_jobs = list(re.finditer(r"(?m)^  ([a-z][a-z0-9_-]*):\s*$", content))
        sections = {
            m.group(1): content[m.start():match_jobs[i + 1].start()
                                      if i + 1 < len(match_jobs) else len(content)]
            for i, m in enumerate(match_jobs)
        }
        token_binding = "ACTIONS_READ_TOKEN: " + chr(36) + "{{ github.token }}"
        for platform in native.PLATFORMS:
            with self.subTest(platform=platform):
                section = sections[platform]
                self.assertIn(f"    name: {platform}\n", section)
                self.assertIn("    needs: [scope, native]\n", section)
                self.assertIn(f"    {gate}\n", section)
                self.assertIn(f"python tools/ci/verify_native_required.py --platform {platform}", section)
        self.assertEqual(content.count("needs: [scope, native]"), 3)
        self.assertIn("name: native build " + chr(36) + "{{ matrix.name }}", content)
        for jobname in (*native.PLATFORMS, "studio"):
            with self.subTest(job=jobname):
                section = sections[jobname]
                self.assertIn(f"    name: {jobname}\n", section)
                self.assertIn("    permissions:\n      contents: read\n      actions: read\n", section)
                self.assertEqual(section.count(token_binding), 1)
                self.assertIn("      - name: Verify ", section)
                self.assertEqual(section.count("      - name: Verify "), 1)
                if jobname == "studio":
                    self.assertIn("    needs: [scope, studio_shards]\n", section)
                    studio_gate = ("if: " + chr(36) + "{{ always() && (github.event_name != 'pull_request' || "
                                   "needs.scope.result != 'success' || (needs.scope.outputs.code != 'false' && "
                                   "(github.event.pull_request.draft != true || needs.scope.outputs.studio != 'false'))) }}")
                    self.assertIn(f"    {studio_gate}\n", section)
                    self.assertIn("run: python tools/ci/verify_native_required.py --studio", section)
                    self.assertIn("persist-credentials: false", section)
                else:
                    self.assertIn(f"run: python tools/ci/verify_native_required.py --platform {jobname}", section)
        self.assertNotIn("python - <<'PY'", content)
        self.assertEqual(content.count("actions: read"), 4)
        self.assertIn("permissions:\n  contents: read\n", content)
        # No other job obtains Actions API read permission or a token binding.
        for jobname, section in sections.items():
            if jobname not in (*native.PLATFORMS, "studio"):
                self.assertNotIn("actions: read", section, jobname)
                self.assertNotIn(token_binding, section, jobname)


if __name__ == "__main__":
    unittest.main()
