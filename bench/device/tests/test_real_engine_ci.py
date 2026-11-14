# SPDX-License-Identifier: GPL-3.0-only
"""Pure file-based checks for real-null-sink CI scripts; never spawn devices."""
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "bench" / "compare"))
from generate_scaling import scaling_patch


class NullSinkFixtureTests(unittest.TestCase):
    def test_n16_is_a_real_96_module_scaling_graph(self):
        patch = scaling_patch(16, enforce_graph_limit=False)
        self.assertEqual(len(patch["modules"]), 96)
        self.assertEqual(len(patch["connections"]), 95)
        self.assertEqual(len(set(m["id"] for m in patch["modules"])), 96)

    def test_default_generator_still_refuses_n16(self):
        with self.assertRaisesRegex(ValueError, "64-module"):
            scaling_patch(16)

    def test_probes_need_existing_executable(self):
        result = subprocess.run([sys.executable, str(HERE / "probe_limits.py"),
                                 "--engine", str(HERE / "absent-not-an-executable")],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--engine is not a built executable", result.stderr)


if __name__ == "__main__":
    unittest.main()
