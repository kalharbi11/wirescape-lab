# SPDX-License-Identifier: GPL-3.0-only
"""CI1 r1 changed-scope contract, including the fail-closed git boundary."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ci"))
import changed_scope as scope  # noqa: E402

BASE = "a" * 40
HEAD = "b" * 40


class ChangedScopeTests(unittest.TestCase):
    def test_notes_only(self):
        self.assertFalse(scope.requires_code([
            "proposals/0001-plan.md",
            "docs/context/SNAPSHOT.md",
            "docs/workflow/milestones/CI1.md",
            "facts/tests/new_durations.md",
            "facts/code/inventory.md",
            "README.md",
            "AGENTS.md",
        ]))

    def test_code_path_among_notes(self):
        self.assertTrue(scope.requires_code(["facts/tests/example.md", "native/engine2/engine2.cpp"]))

    def test_specs(self):
        self.assertTrue(scope.requires_code(["docs/specs/ENGINE_PROTOCOL.md"]))

    def test_dsp_facts(self):
        self.assertTrue(scope.requires_code(["facts/dsp/coverage/case.json"]))

    def test_workflows(self):
        self.assertTrue(scope.requires_code([".github/workflows/ci.yml"]))

    def test_empty_and_unlisted_paths(self):
        self.assertTrue(scope.requires_code([]))
        for path in ["extras/value.txt", "apps/studio/tests/editor.spec.ts"]:
            with self.subTest(path=path):
                self.assertTrue(scope.requires_code([path]))

    def test_prose_docs_are_notes(self):
        # Proposal 0023 R1.3 / CI-S1: every *.md under docs/ outside docs/specs/ is notes.
        for path in ["docs/INSTALL.md", "docs/sequencer/GROOVE.md", "docs/README.md"]:
            with self.subTest(path=path):
                self.assertFalse(scope.requires_code([path]))
        for path in ["docs/specs/ENGINE_PROTOCOL.md", "docs/specs/protocol.schema.json",
                     "docs/x.png", "docs/history/manifest.json"]:
            with self.subTest(path=path):
                self.assertTrue(scope.requires_code([path]))

    def test_root_non_markdown(self):
        self.assertTrue(scope.requires_code(["LICENSE"]))

    def test_subdirectories_required(self):
        for path in ["proposals", "docs/context", "docs/workflow", "facts"]:
            self.assertTrue(scope.requires_code([path]))

    def test_malformed_paths(self):
        for path in ["", "/facts/report.md", "../facts/report.md",
                     "facts/../proposals/x.md", "docs//context/x.md",
                     r"docs\workflow\notes.md", "facts/./tests/data.md"]:
            with self.subTest(path=path):
                self.assertTrue(scope.requires_code([path]))

    def test_push_manual_unknown_never_run_git(self):
        with mock.patch.object(scope, "git_changed_paths", side_effect=AssertionError("not called")):
            for event in ("push", "workflow_dispatch", "", "schedule"):
                self.assertTrue(scope.classify(event, BASE, HEAD))

    def test_pr_notes_only(self):
        with mock.patch.object(scope, "git_changed_paths",
                               return_value=["facts/tests/a.md", "docs/workflow/CURRENT.md"]):
            self.assertFalse(scope.classify("pull_request", BASE, HEAD))

    def test_pr_empty_git_diff(self):
        with mock.patch.object(scope, "git_changed_paths", return_value=[]):
            self.assertTrue(scope.classify("pull_request", BASE, HEAD))

    def test_git_failure(self):
        for error in [OSError("git absent"), ValueError("bad SHA"),
                      UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"),
                      subprocess.CalledProcessError(128, ["git"])]:
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(scope, "git_changed_paths", side_effect=error):
                    self.assertTrue(scope.classify("pull_request", BASE, HEAD))

    def test_plain_git_nul_merge_base(self):
        with mock.patch.object(scope.subprocess, "run",
                               return_value=subprocess.CompletedProcess(
                                   args=["git"], returncode=0,
                                   stdout=b"facts/tests/n.md\0native/src/engine.cpp\0")) as run:
            self.assertEqual(scope.git_changed_paths(BASE, HEAD),
                             ["facts/tests/n.md", "native/src/engine.cpp"])
            args = run.call_args.args[0]
            self.assertEqual(args[0], "git")
            self.assertIn("--no-renames", args)
            self.assertIn("-z", args)
            self.assertIn(BASE + "..." + HEAD, args)

    def test_bad_git_data_and_sha(self):
        with mock.patch.object(scope.subprocess, "run", return_value=subprocess.CompletedProcess(
                args=["git"], returncode=0, stdout=b"facts/x.md")):
            self.assertTrue(scope.classify("pull_request", BASE, HEAD))
        with mock.patch.object(scope.subprocess, "run", return_value=subprocess.CompletedProcess(
                args=["git"], returncode=0, stdout=b"facts/\xff.md\0")):
            self.assertTrue(scope.classify("pull_request", BASE, HEAD))
        self.assertTrue(scope.classify("pull_request", "bad", HEAD))
        self.assertTrue(scope.classify("pull_request", BASE, ""))


if __name__ == "__main__":
    unittest.main()
