# SPDX-License-Identifier: GPL-3.0-only
"""Device-free regression tests for test collector process diagnostics."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from test_facts import run
from memory_facts import rss_kib


class TestCollectorTests(unittest.TestCase):
    def test_failed_suite_keeps_last_40_lines_and_exit_code(self):
        command = [sys.executable, "-c",
                   "import sys; [print('line-%02d' % i) for i in range(45)]; sys.exit(8)"]
        with tempfile.TemporaryDirectory() as temp:
            value = run(command, Path(temp), True)
        self.assertEqual(value["status"], "failed")
        self.assertEqual(value["exit_code"], 8)
        self.assertEqual(len(value["failure_output_lines"]), 40)
        self.assertEqual(value["failure_output_lines"][0], "line-05")
        self.assertEqual(value["failure_output_lines"][-1], "line-44")

    def test_child_receives_explicit_environment(self):
        command = [sys.executable, "-c",
                   "import os,sys; print(os.environ.get('WIRESCAPE_REAL_ENGINE','absent'))"]
        with tempfile.TemporaryDirectory() as temp:
            result = run(command, Path(temp), True, {"WIRESCAPE_REAL_ENGINE": "synthetic.exe"})
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["stdout_tail"].strip(), "synthetic.exe")
        self.assertNotIn("failure_output_lines", result)

    @mock.patch("memory_facts.platform.system", return_value="Windows")
    def test_windows_memory_uses_psutil(self, _):
        fake = mock.Mock()
        fake.Process.return_value.memory_info.return_value.rss = 4096
        with mock.patch.dict(sys.modules, {"psutil": fake}):
            self.assertEqual(rss_kib(1234), 4)
        fake.Process.assert_called_once_with(1234)


if __name__ == "__main__":
    unittest.main()
