# SPDX-License-Identifier: GPL-3.0-only
"""Device-off, network-free CI digest parser tests."""
import unittest
from tools.ci.ci_digest import MARKER, parse, render, safe, run


class DigestTests(unittest.TestCase):
    def test_red_fixture(self):
        result = parse("build: error: foo.cpp:10\nFAILED test_note\nGolden mismatch: x.wav\nM1 Ir +1.37%\nM1 Ir +0.8%")
        self.assertIn("build: error: foo.cpp:10", result["errors"])
        self.assertTrue(result["tests"])
        self.assertTrue(result["golden"])
        self.assertEqual(len(result["ir"]), 1)

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

    def test_refuses_unassociated_run(self):
        class NoNetwork:
            def get(self, *args, **kwargs):
                raise AssertionError("unexpected API request")
        event = {"workflow_run": {"name": "Lab CI", "event": "push",
                 "head_sha": "a" * 40, "repository": {"full_name": "x/y"}}}
        self.assertEqual(run(NoNetwork(), event, "x/y"), "ignored unrelated run")


if __name__ == "__main__":
    unittest.main()
