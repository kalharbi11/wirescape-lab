#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic, device-free tests for CI facts staging."""
import json
from pathlib import Path
import tempfile
import unittest

from ci_stage_facts import clean, copy_tables, stage_collector, stage_full


META = {"commit": "0123456789abcdef", "date_et": "2026-11-14",
        "machine": {"cpu": "synthetic", "os": "synthetic",
                    "runner_image": "synthetic", "audio_devices": "not accessed"}}


class StageTests(unittest.TestCase):
    def test_clean_drops_logs_and_absolute_paths(self):
        data = clean({"command": ["secret-command"], "stderr_tail": "bad",
                      "detail": "/tmp/a/facts bad sample", "count": 3})
        self.assertNotIn("command", data)
        self.assertNotIn("stderr_tail", data)
        self.assertEqual(data["count"], 3)
        self.assertNotIn("/tmp", data["detail"])
        self.assertNotIn("bad", data["detail"])

    def test_failed_suite_keeps_redacted_last_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "raw"
            destination = Path(tmp) / "facts"
            (root / "tests").mkdir(parents=True)
            (root / "tests/summary.json").write_text(json.dumps({
                "suites": {"ctest": {"run": {
                    "status": "failed", "exit_code": 8,
                    "stderr_tail": "discard raw log",
                    "failure_output_lines": [
                        "Could not find configuration /tmp/ci/secret",
                        "100% tests failed"]}}}}))
            self.assertEqual(stage_collector(root, destination, "tests",
                                             "tests", META, "windows-x64"), "recorded")
            data = json.loads((destination / "tests/ci-windows-x64/tests.json").read_text())
            result = data["measurements"]["suites"]["ctest"]["run"]
            self.assertEqual(result["exit_code"], 8)
            self.assertNotIn("stderr_tail", result)
            self.assertIn("[path]", result["failure_output_lines"][0])
            self.assertNotIn("/tmp/ci/secret", str(result))

    def test_stage_collector_and_missing_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "raw"
            destination = Path(tmp) / "facts"
            (root / "protocol").mkdir(parents=True)
            (root / "protocol/summary.json").write_text(
                json.dumps({"setParam": {"p50_ms": 1.5}, "stdout_tail": "discard"}))
            status = stage_collector(root, destination, "protocol", "app", META, "linux-x64")
            self.assertEqual(status, "recorded")
            payload = json.loads((destination / "app/ci-linux-x64/protocol.json").read_text())
            self.assertEqual(payload["measurements"]["setParam"]["p50_ms"], 1.5)
            self.assertNotIn("stdout_tail", payload["measurements"])
            missing = stage_collector(root, destination, "repo", "repo", META, "linux-x64")
            self.assertEqual(missing, "collector output absent")
            self.assertEqual(json.loads(
                (destination / "repo/ci-linux-x64/repo.json").read_text())["status"],
                "unavailable")

    def test_full_pack_and_graph_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "raw"
            destination = Path(tmp) / "facts"
            (root / "full/perf").mkdir(parents=True)
            (root / "full/perf/module_cpu.json").write_text(json.dumps({"rows": [{"p50_ns": 20}]}))
            copied = stage_full(root / "full", destination, "linux-arm64", META)
            self.assertEqual(copied["module_cpu.json"], "recorded")
            self.assertTrue((destination / "dsp/ci-linux-arm64/unavailable.json").exists())
            (root / "repo").mkdir(parents=True)
            (root / "repo/cmake-targets.csv").write_text("target,links,used_by\na,b,c\n")
            (root / "repo/binary_sizes.csv").write_text("path,bytes\n/tmp/work,3\n")
            copy_tables(root, destination, "linux-arm64", META)
            self.assertTrue((destination / "repo/ci-linux-arm64/cmake-targets.csv").exists())
            self.assertFalse((destination / "repo/ci-linux-arm64/binary_sizes.csv").exists())


if __name__ == "__main__":
    unittest.main()
