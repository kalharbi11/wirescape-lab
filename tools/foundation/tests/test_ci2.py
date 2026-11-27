# SPDX-License-Identifier: GPL-3.0-only
"""CI2 / A42: draft scope and four-shard acceptance regression."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/ci"))
import changed_scope as scope
import verify_native_required as verifier


class CI2Tests(unittest.TestCase):
    def test_engine_source_only_skips_ui_on_draft(self):
        self.assertFalse(scope.requires_studio(["engine/render.cpp", "engine/edit.cpp"]))
        self.assertFalse(scope.requires_studio(["engine/render.cpp", "docs/workflow/CURRENT.md"]))

    def test_ui_inputs_and_unknown_paths_fail_closed(self):
        for path in ("apps/studio/src/app/App.ts", "apps/desktop/main.ts",
                     "protocol/v0/schema.json", "host/sidecar/session.cpp",
                     "engine/control/module_registry.cmake", "engine/control/module_registry.cpp.in",
                     "tools/mb1/descriptor_inventory.json", "modules/vco/module.cpp", "tests/protocol/golden_v0.ndjson",
                     "tests/native/compat/fixtures/legacy_documents/example.json",
                     "host/examples/patch.json", ".github/workflows/ci.yml",
                     "engine/unknown.json", "unknown/file.cpp", "engine/../apps/a.cpp",
                     "engine//render.cpp", "/engine/render.cpp", r"engine\\render.cpp"):
            with self.subTest(path=path):
                self.assertTrue(scope.requires_studio(["engine/render.cpp", path]))
        self.assertTrue(scope.requires_studio([]))

    def test_scope_output_is_fail_closed(self):
        for event, paths, expected in (
                ("pull_request", ["engine/render.cpp"], "false"),
                ("pull_request", ["apps/studio/src/app/App.ts"], "true"),
                ("pull_request", [], "true"),
                ("push", [], "true"), ("workflow_dispatch", [], "true")):
            with self.subTest(event=event, paths=paths), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "output"
                env = {"CI_EVENT_NAME": event, "CI_BASE_SHA": "a" * 40,
                       "CI_HEAD_SHA": "b" * 40, "GITHUB_OUTPUT": str(output)}
                with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(
                        scope, "git_changed_paths", return_value=paths):
                    self.assertEqual(scope.main(), 0)
                self.assertIn("studio=" + expected, output.read_text().splitlines())
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"
            with mock.patch.dict(os.environ, {"CI_EVENT_NAME": "pull_request",
                    "GITHUB_OUTPUT": str(output)}, clear=True), mock.patch.object(
                    scope, "git_changed_paths", side_effect=subprocess.SubprocessError("git failed")):
                self.assertEqual(scope.main(), 0)
            self.assertEqual(output.read_text().splitlines(), ["code=true", "studio=true"])

    def test_four_shards(self):
        self.assertEqual(verifier.STUDIO, tuple(f"studio shard {n}/4" for n in range(1, 5)))
        text = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertIn("shard: [1, 2, 3, 4]", text)
        self.assertIn("--shard=${{ matrix.shard }}/4", text)

    def test_evidence_workflows_reopen_on_ready(self):
        for name in ("golden-renders", "m1-stage-evidence", "instruction-gate",
                     "offline-facts", "ob-g7-hosted-soak", "portability"):
            with self.subTest(workflow=name):
                text = (ROOT / ".github/workflows" / (name + ".yml")).read_text()
                self.assertIn("ready_for_review", text)
                self.assertIn("github.event.pull_request.draft == false", text)


if __name__ == "__main__":
    unittest.main()
