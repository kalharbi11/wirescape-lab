# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic Windows evidence acceptance tests: no processes or devices."""
import json
from pathlib import Path
import tempfile
import unittest

from verify_windows_facts import verify


def write_doc(root, area, name, measurements):
    dest = Path(root) / area / "ci-windows-x64"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / (name + ".json")).write_text(
        json.dumps({"measurements": measurements}), encoding="utf-8")


class WindowsFactChecks(unittest.TestCase):
    def test_accepts_real_measurement_shapes_and_rejects_placeholders(self):
        with tempfile.TemporaryDirectory() as root:
            write_doc(root, "tests", "tests", {"suites": {
                "ctest": {"run": {"status": "passed", "exit_code": 0}},
                "playwright_desktop": {"run": {"status": "passed", "exit_code": 0}}}})
            write_doc(root, "app", "memory", {
                "engine_idle_rss_kib": 5000,
                "largest_bundled_patch": {"rss_kib": 6000}})
            write_doc(root, "app", "startup", {
                "runs": [{"electron_idle": {"rss_kib": 7000}} for _ in range(10)],
                "summary": {"first_paint": {"n": 10}}})
            write_doc(root, "dsp", "oscillators", {
                "rows": [{"status": "measured", "peak_fs": 0.5}]})
            write_doc(root, "perf", "module_cpu", {
                "rows": [{"status": "measured", "mean_ns": 1}]})
            write_doc(root, "perf", "engine_cpu", {"rows": [
                {"status": "measured", "block_frames": x} for x in (64, 128, 256)]})
            self.assertEqual(verify(root)["engine_blocks"], [64, 128, 256])
            write_doc(root, "app", "memory", {
                "engine_idle_rss_kib": None,
                "largest_bundled_patch": {"rss_kib": None}})
            with self.assertRaisesRegex(ValueError, "idle RSS"):
                verify(root)


if __name__ == "__main__":
    unittest.main()
