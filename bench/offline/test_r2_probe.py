# SPDX-License-Identifier: GPL-3.0-only
"""Device-free known-answer tests of R2 sample routing and refusal/status logic."""
import json
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from r2_probe import collect_r2, invoke


class R2ProbeTests(unittest.TestCase):
    def test_no_audio_input_explicitly_not_applicable(self):
        data = {
            "essentials.vcf": {
                "inputs": [{"port": "audio", "type": "WS2_AUDIO"}],
                "outputs": [{"port": "low12", "type": "WS2_AUDIO"}]},
            "essentials.clock": {
                "inputs": [{"port": "reset", "type": "WS2_GATE"}],
                "outputs": [{"port": "clock", "type": "WS2_GATE"}]},
            "ports.input_only": {
                "inputs": [{"port": "audio", "type": "WS2_AUDIO"}],
                "outputs": [{"port": "env", "type": "WS2_GATE"}]},
        }
        with tempfile.TemporaryDirectory() as temp, \
             mock.patch("r2_probe.platform.system", return_value="Linux"):
            impulse, tails = collect_r2(Path(temp), data, True, (48000,))
        self.assertEqual(len(impulse), 3)
        self.assertEqual(len(tails), 3)
        by_name = {r["module"]: r for r in impulse}
        self.assertEqual(by_name["essentials.clock"]["status"], "not_applicable")
        self.assertEqual(by_name["essentials.clock"]["reason"],
                         "descriptor has no WS2_AUDIO input")
        self.assertEqual(by_name["ports.input_only"]["reason"],
                         "descriptor has no WS2_AUDIO output tap")
        self.assertEqual(by_name["essentials.vcf"]["status"], "not_run_quick_mode")

    def test_probe_requires_exact_module_rate_mode(self):
        class Result:
            returncode = 0
            stdout = json.dumps({"status": "measured", "module": "different",
                                 "rate_hz": 48000, "mode": "impulse"}) + "\n"
            stderr = ""
        with mock.patch("r2_probe.subprocess.run", return_value=Result()):
            row = invoke(Path("probe"), "impulse", "essentials.vcf",
                         Path("libws2_vcf.so"), 48000, Path("capture.f32le"))
        self.assertEqual(row["status"], "probe_malformed_result")
        self.assertIn("identity mismatch", row["reason"])

    def test_probe_command_failure_preserves_exit_and_reason(self):
        class Result:
            returncode = 7
            stdout = ""
            stderr = "engine prepare refused module config"
        with mock.patch("r2_probe.subprocess.run", return_value=Result()):
            row = invoke(Path("probe"), "tail", "essentials.vcf",
                         Path("libws2_vcf.so"), 44100, Path("capture.f32le"))
        self.assertEqual(row["status"], "probe_execution_error")
        self.assertEqual(row["exit_code"], 7)
        self.assertIn("prepare refused", row["reason"])


if __name__ == "__main__":
    unittest.main()
