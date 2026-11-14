# SPDX-License-Identifier: GPL-3.0-only
import subprocess
import sys
import unittest
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]/"run.py"


class GateTests(unittest.TestCase):
    def test_requires_audio_confirmation(self):
        result=subprocess.run([sys.executable,str(RUN),"--scenario","quick"],
                              capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("--confirm-audio is required",result.stderr)

    def test_dry_run_rejects_device_mode(self):
        result=subprocess.run([sys.executable,str(RUN),"--dry-run","--record","input"],
                              capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("--dry-run prohibits",result.stderr)


if __name__=="__main__":
    unittest.main()
