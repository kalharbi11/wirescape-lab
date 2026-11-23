# SPDX-License-Identifier: GPL-3.0-only
"""Device-off, network-free CI digest parser tests."""
import unittest
import io
import urllib.error
from unittest.mock import patch
from tools.ci.ci_digest import download_log, API
from tools.ci.ci_digest import MARKER, parse, render, safe, run


class DigestTests(unittest.TestCase):
    def test_red_fixture(self):
        result = parse("build: error: foo.cpp:10\nFAILED test_note\nGolden mismatch: x.wav\nM1 Ir +1.37%\nM1 Ir +0.8%")
        self.assertIn("build: error: foo.cpp:10", result["errors"])
        self.assertTrue(result["tests"])
        self.assertTrue(result["golden"])
        self.assertEqual(len(result["ir"]), 1)

    def test_actual_m1_paired_failure_rows(self):
        # M1 x64 job 137790998469 emits rows without M1/Ir prefixes.
        log = ("FAIL: module/essentials.lfo/voices1: +1.857869316% exceeds strict +1%\\n"
               "FAIL: module/essentials.lfo/voices8: +1.2% exceeds strict +1%\\n"
               "FAIL: module/essentials.lfo/voices1: +0.9% exceeds strict +1%\\n"
               "FAIL: module/essentials.lfo/voices1: +1.0% exceeds strict +1%\\n"
               "noise: +8.0% exceeds strict +1%")
        result = parse(log)
        self.assertEqual(len(result["ir"]), 2)
        self.assertIn("+1.857869316%", result["ir"][0])
        self.assertIn("voices8", result["ir"][1])

    def test_green_fixture(self):
        self.assertEqual(parse("all tests passed\nIr +0.5%"), {
            "errors": [], "tests": [], "golden": [], "ir": []})

    def test_hostile_text(self):
        text = safe("@team ``` [link](url) <!-- attack -->")
        self.assertNotIn("@team", text)
        self.assertNotIn("```", text)
        self.assertNotIn("<!-- attack -->", text)

    def test_limit_and_marker(self):
        data = {"errors": ["FAILED x"] * 100, "tests": [], "golden": [], "ir": []}
        body = render("a" * 40, {}, [("job", "step", data)] * 5)
        self.assertLessEqual(len(body.splitlines()), 60)
        self.assertIn(MARKER, body)

    def test_redirect_never_sends_token(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = io.BytesIO(data)
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, n):
                return self.data.read(n)
        class Opener:
            def __init__(self):
                self.requests = []
            def open(self, request, timeout):
                self.requests.append(request)
                if len(self.requests) == 1:
                    raise urllib.error.HTTPError(request.full_url, 302, "redirect",
                        {"Location": "https://storage.example.test/log"}, None)
                return FakeResponse(b"FAILED test_note")
        opener = Opener()
        self.assertIn("FAILED", download_log(
            "https://api.github.com/repos/x/y/actions/jobs/1/logs", "SECRET", opener))
        self.assertEqual(opener.requests[0].get_header("Authorization"), "Bearer SECRET")
        self.assertIsNone(opener.requests[1].get_header("Authorization"))
        with self.assertRaises(ValueError):
            download_log("http://api.github.com/evil", "SECRET", opener)
        class Unsafe(Opener):
            def open(self, request, timeout):
                raise urllib.error.HTTPError(request.full_url, 302, "redirect",
                    {"Location": "http://evil.example/log"}, None)
        with self.assertRaises(ValueError):
            download_log("https://api.github.com/repos/x/y/actions/jobs/1/logs",
                         "SECRET", Unsafe())

    def test_two_heads_same_comment_id_and_stale_event(self):
        class FakeAPI:
            root = "https://api.github.com/repos/x/y"
            token = "fake"
            def __init__(self):
                self.head = "a" * 40
                self.comment = None
                self.comment_id = 71
                self.writes = []
                self.stale_at = False
            def get(self, path, method="GET", data=None, raw=False):
                if path.startswith("/pulls/"):
                    return {"state": "open", "head": {"sha": self.head},
                            "base": {"repo": {"full_name": "x/y"}}}
                if method in ("POST", "PATCH"):
                    self.comment = data["body"]
                    self.writes.append((method, self.comment_id, self.head))
                    return {"id": self.comment_id}
                raise AssertionError(path)
            def pages(self, path, key=None):
                if path.startswith("/actions/runs?"):
                    return [{"id": 1, "name": "Lab CI", "event": "pull_request",
                             "head_sha": self.head, "conclusion": "success",
                             "pull_requests": [{"number": 9}]}]
                if path.startswith("/issues/"):
                    if self.stale_at:
                        self.head = "c" * 40
                    return [] if self.comment is None else [{
                        "id": self.comment_id, "body": self.comment,
                        "user": {"login": "github-actions[bot]"}}]
                raise AssertionError(path)
        api = FakeAPI()
        def event(sha):
            return {"workflow_run": {"id": 1, "name": "Lab CI",
                "event": "pull_request", "head_sha": sha,
                "repository": {"full_name": "x/y"},
                "pull_requests": [{"number": 9}]}}
        self.assertEqual(run(api, event(api.head), "x/y"), "updated #9")
        api.head = "b" * 40
        self.assertEqual(run(api, event(api.head), "x/y"), "updated #9")
        self.assertEqual([x[0] for x in api.writes], ["POST", "PATCH"])
        self.assertEqual({x[1] for x in api.writes}, {71})
        self.assertIn("b" * 40, api.comment)
        self.assertEqual(run(api, event("a" * 40), "x/y"),
                         "no validated current-head PR")
        api.stale_at = True
        self.assertEqual(run(api, event("b" * 40), "x/y"),
                         "stale event: head changed before comment write")
        self.assertEqual(len(api.writes), 2)

    def test_refuses_unassociated_run(self):
        class NoNetwork:
            def get(self, *args, **kwargs):
                raise AssertionError("unexpected API request")
        event = {"workflow_run": {"name": "Lab CI", "event": "push",
                 "head_sha": "a" * 40, "repository": {"full_name": "x/y"}}}
        self.assertEqual(run(NoNetwork(), event, "x/y"), "ignored unrelated run")


if __name__ == "__main__":
    unittest.main()
