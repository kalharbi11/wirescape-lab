# SPDX-License-Identifier: GPL-3.0-only
"""Speaker check tests: no physical audio/MIDI access or network sockets."""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from speaker_check import FREQUENCY_HZ, TARGET_PEAK, TARGET_RMS_DBFS, tone_patch


class SpeakerCheckTests(unittest.TestCase):
    def call(self, *args):
        return subprocess.run([sys.executable, str(HERE / "run.py"), "--speaker-check", *args],
                              capture_output=True, text=True, timeout=20)

    def test_real_audio_denied_before_backend_or_files(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.call("--results", temp, "--machine", "speaker-test")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--confirm-audio is required", result.stderr)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_dry_run_null_sink_without_device_permission(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.call("--dry-run", "--results", temp, "--machine", "speaker-test")
            self.assertEqual(result.returncode, 0, result.stderr)
            reports = list(Path(temp).rglob("owner-observations.json"))
            self.assertEqual(len(reports), 1)
            obs = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertEqual(obs["mode"], "null-audio")
            self.assertEqual(obs["heard"], "not-applicable-null-sink")
            self.assertTrue(obs["completed"])
            self.assertAlmostEqual(obs["target_rms_dbfs"], -18.0)
            self.assertEqual(obs["tone_seconds"], 5.0)
            manifest = json.loads((reports[0].parent / "manifest.json").read_text())
            self.assertEqual(manifest["scenario"], "speaker-check")
            self.assertTrue(manifest["completed"])
            self.assertIn(manifest["engine_mode"], ("simulation", "null-audio"))

    def test_speaker_mode_does_not_authorize_midi(self):
        result = self.call("--confirm-audio", "--confirm-midi")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--speaker-check does not use MIDI", result.stderr)

    def test_tone_patch_has_bounded_stereo_sine_gain(self):
        patch = tone_patch(48000, 128)
        modules = [m["module"] for m in patch["modules"]]
        self.assertEqual(modules, ["essentials.vco", "essentials.vca", "essentials.output"])
        self.assertEqual(patch["modules"][0]["parameters"]["frequency"], FREQUENCY_HZ)
        self.assertEqual(patch["modules"][1]["parameters"]["gain"], 0.0)
        self.assertEqual(len(patch["outputs"]), 2)
        self.assertLess(TARGET_PEAK, 1)
        self.assertAlmostEqual(20 * math.log10(TARGET_PEAK / math.sqrt(2)),
                               TARGET_RMS_DBFS, places=3)


if __name__ == "__main__":
    unittest.main()
