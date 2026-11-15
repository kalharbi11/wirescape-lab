# SPDX-License-Identifier: GPL-3.0-only
"""Device-free synthetic signal, click detection and hardware authorization tests."""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import latency
from latency import (CLICK_PEAK, CLICKS, MIN_CLICKS, click_patch,
                     measure, synthetic_capture)


class LatencyTests(unittest.TestCase):
    def call(self, *flags):
        return subprocess.run([sys.executable, str(HERE / "latency.py"), *flags],
                              capture_output=True, text=True, timeout=90)

    def test_known_delay_plus_noise_within_one_sample(self):
        for rate, block in ((44100, 64), (48000, 128), (96000, 256)):
            with self.subTest(rate=rate, block=block):
                audio, first, delay = synthetic_capture(rate, block, noise=0.0015)
                result = measure(audio, rate, first, phase_known=True)
                self.assertEqual(result["clicks_found"], CLICKS)
                self.assertLessEqual(abs(result["frames"]["median"] - delay), 1)
                self.assertLessEqual(max(abs(a["delay_frames"] - delay)
                                         for a in result["arrivals"]), 1)

    def test_low_level_refused_even_if_a_tone_is_present(self):
        audio, first, _ = synthetic_capture(48000, 128, noise=0)
        with self.assertRaisesRegex(ValueError, "below -40 dBFS"):
            measure(audio * 0.0001, 48000, first)

    def test_too_few_clicks_refused(self):
        rate = 48000
        audio, first, _ = synthetic_capture(rate, 128, noise=0)
        audio[first + 18 * (rate // 2):, :] = 0
        with self.assertRaisesRegex(ValueError, "at least 30 required"):
            measure(audio, rate, first)

    def test_clock_patch_bounded_and_muted_until_armed(self):
        patch = click_patch(48000, 128)
        modules = {m["id"]: m for m in patch["modules"]}
        self.assertEqual(modules[1]["parameters"]["bpm"], 120)
        self.assertEqual(modules[1]["parameters"]["run"], 0)
        self.assertEqual(modules[4]["parameters"]["gain"], 0)
        self.assertLessEqual(CLICK_PEAK, 0.2)
        self.assertEqual(len(patch["outputs"]), 2)
        self.assertEqual(len(patch["connections"]), 4)
        self.assertAlmostEqual(20 * math.log10(CLICK_PEAK), -13.9794001, places=3)

    def test_authorization_rejected_before_creating_results(self):
        with tempfile.TemporaryDirectory() as root:
            proc = self.call("--results", root, "--machine", "gate")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--confirm-audio is required", proc.stderr)
            self.assertFalse(list(Path(root).iterdir()))
            proc = self.call("--dry-run", "--confirm-audio", "--results", root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--dry-run prohibits", proc.stderr)
            self.assertFalse(list(Path(root).iterdir()))
            proc = self.call("--confirm-audio", "--results", root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("requires both --device and --input-device", proc.stderr)
            self.assertFalse(list(Path(root).iterdir()))

    def test_no_authorization_no_external_process_or_output(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("subprocess.Popen", side_effect=AssertionError("spawn forbidden")):
                with self.assertRaises(SystemExit):
                    latency.main(["--machine", "gate", "--results", root])
                with self.assertRaises(SystemExit):
                    latency.main(["--dry-run", "--confirm-audio", "--results", root])
            self.assertFalse(list(Path(root).iterdir()))

    def test_live_shaped_fixture_is_not_reported_as_calibrated_latency(self):
        rate, block = 48000, 128
        audio, first, _ = synthetic_capture(rate, block, noise=0.001)
        metadata = {
            "rate_hz": rate, "buffer_frames": block,
            "expected_first_frame": first,
            "timing_model": {
                "measurement_quantity": "uncalibrated_host_command_midpoint_to_input_click_onset",
                "calibrated_dac_to_adc_round_trip": False,
                "request_ack_window_ms": 7.0,
                "absolute_error_bound_ms": None,
            },
        }
        with tempfile.TemporaryDirectory() as root:
            args = SimpleNamespace(dry_run=False, results=Path(root),
                                   machine="fixture", rate=rate)
            with patch.object(latency, "physical_capture", return_value=(audio, metadata)):
                self.assertTrue(latency.run_one(args, block, "abcdef0123456", "2026-11-15"))
            evidence = list(Path(root).rglob("latency.json"))
            self.assertEqual(len(evidence), 1)
            values = json.loads(evidence[0].read_text(encoding="utf-8"))
            report = (evidence[0].parent / "report.md").read_text(encoding="utf-8")
            self.assertTrue(values["completed"])
            self.assertFalse(values["issue_54_calibrated_round_trip_requirement_met"])
            self.assertFalse(values["measurement"]["calibrated_round_trip"])
            self.assertFalse(values["uncalibrated_nominal_comparison"]["meaningful_device_overhead"])
            self.assertIsNone(values["timing_model"]["absolute_error_bound_ms"])
            self.assertNotIn("difference_from_2x_buffer_frames", values)
            self.assertIn("NOT calibrated DAC-to-ADC", report)
            self.assertIn("NOT an estimate of hardware/device overhead", report)
            self.assertIn("not an error bound", report)

    def test_dry_run_sweep_is_synthetic_and_has_reports(self):
        with tempfile.TemporaryDirectory() as root:
            proc = self.call("--dry-run", "--sweep", "--machine", "synthetic",
                             "--results", root)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            reports = sorted(Path(root).rglob("latency.json"))
            self.assertEqual(len(reports), 3)
            self.assertEqual({json.loads(p.read_text())["buffer_frames"]
                              for p in reports}, {64, 128, 256})
            for path in reports:
                result = json.loads(path.read_text())
                self.assertTrue(result["dry_run"])
                self.assertTrue(result["completed"])
                self.assertEqual(result["kind"], "uncalibrated-command-to-adc-diagnostic")
                self.assertEqual(result["measurement"]["quantity"], "synthetic_known_sample_delay")
                self.assertFalse(result["measurement"]["calibrated_round_trip"])
                self.assertEqual(result["measurement"]["clicks_found"], CLICKS)
                self.assertLessEqual(abs(result["measurement"]["frames"]["median"]
                                         - result["synthetic_delay_frames"]), 1)
                self.assertFalse((path.parent / "capture.flac").exists())


if __name__ == "__main__":
    unittest.main()
