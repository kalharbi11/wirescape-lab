# SPDX-License-Identifier: GPL-3.0-only
"""Contracts for the lab's hosted-only CI; retired workflows live in ci/from-main."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/ci.yml"


class CITriggers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_pull_requests_do_not_rerun_on_ready_event(self):
        self.assertIn("types: [opened, synchronize, reopened]", self.workflow)
        self.assertIn("branches: [main]", self.workflow)
        self.assertIn("workflow_dispatch:", self.workflow)

    def test_all_required_hosted_lanes_exist(self):
        for name in ("linux-x64", "linux-arm64", "windows-x64", "sanitizers", "studio", "desktop"):
            with self.subTest(name=name):
                self.assertIn(name, self.workflow)
        for runner in ("ubuntu-latest", "ubuntu-24.04-arm", "windows-latest"):
            self.assertIn(runner, self.workflow)
        self.assertNotRegex(self.workflow, r"self-hosted|ci/pi|merge_gate|board\\.py|guard\\.py")

    def test_native_runs_real_headless_build_and_ctest(self):
        self.assertIn("python tools/dev.py build --headless", self.workflow)
        self.assertIn("python tools/dev.py test", self.workflow)
        self.assertIn("cmake==4.2.3 ninja==1.13.0", self.workflow)

    def test_sanitizers_use_linux_x64_with_real_abi2_tests(self):
        job = self.workflow.split("  sanitizers:", 1)[1].split("  studio:", 1)[0]
        self.assertIn("runs-on: ubuntu-latest", job)
        self.assertIn("-fsanitize=address,undefined", job)
        self.assertIn("ctest --test-dir build/asan -R abi2 -E", job)
        self.assertIn("sanitizer-known-ub:", self.workflow)
        self.assertIn("continue-on-error: true", self.workflow)
        self.assertIn("abi2_live_replan_tests", self.workflow)

    def test_studio_uses_playwright_and_desktop_tests_use_null_audio(self):
        self.assertIn("npx playwright install --with-deps chromium", self.workflow)
        self.assertIn("WIRESCAPE_CHROMIUM=", self.workflow)
        self.assertIn("xvfb-run -a npm test", self.workflow)
        self.assertIn("name: Python foundation regression suite", self.workflow)


if __name__ == "__main__":
    unittest.main()
