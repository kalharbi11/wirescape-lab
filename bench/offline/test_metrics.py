# SPDX-License-Identifier: GPL-3.0-only
"""Pure DSP measurement tests; no hardware, network or built engine needed."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy import signal

from metrics import (basic, click_events, direct_envelope_metrics, filter_metrics,
                     folded_alias_frequencies, oscillator_metrics, patch_metrics,
                     read_audio, self_oscillation_metrics, step_metrics, sweep_residual_metrics)


class MetricsTests(unittest.TestCase):
    def test_float_wav_and_levels(self):
        rate = 48000
        t = np.arange(rate) / rate
        tone = (0.5 * np.sin(2 * math.pi * 440 * t)).astype("<f4")
        data = np.column_stack([tone, tone]).astype("<f4").tobytes()
        length = len(data)
        header = (b"RIFF" + struct.pack("<I", 36 + length) + b"WAVEfmt " +
                  struct.pack("<IHHIIHH", 16, 3, 2, rate, rate * 8, 8, 32) +
                  b"data" + struct.pack("<I", length))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tone.wav"
            path.write_bytes(header + data)
            audio = read_audio(path)
        levels = basic(audio)
        self.assertEqual(audio.shape, (rate, 2))
        self.assertEqual(levels["nonfinite_samples"], 0)
        self.assertAlmostEqual(levels["peak_fs"], .5, places=4)
        self.assertAlmostEqual(levels["rms_fs"], math.sqrt(.125), places=4)

    def test_pitch_and_thd(self):
        t = np.arange(48000) / 48000
        sine = np.sin(2 * math.pi * 440 * t)
        stereo = np.column_stack([sine, sine])
        result = oscillator_metrics(stereo, 440)
        self.assertLess(abs(result["pitch_cents"]), .1)
        self.assertLess(result["thd_db"], -60)
        self.assertTrue(math.isfinite(result["alias_floor_dbfs"]))

    def test_folded_aliases_only_at_expected_harmonics(self):
        rate, fundamental = 48000, 7040
        predicted = folded_alias_frequencies(fundamental, rate, max_harmonic=8)
        self.assertIn(12800., predicted)  # 5 * 7040 -> 12800
        self.assertIn(19840., predicted)  # 4 * 7040 -> 19840
        self.assertNotIn(7040., predicted)  # fundamental is not an alias
        t = np.arange(rate, dtype=float) / rate
        clean = .6 * np.sin(math.tau * fundamental * t)
        alias = clean + .2 * np.sin(math.tau * 12800 * t)
        metric = lambda x: oscillator_metrics(np.column_stack([x, x]), fundamental, rate)
        a, b = metric(clean), metric(alias)
        self.assertGreater(b["alias_floor_dbfs"], a["alias_floor_dbfs"] + 25)
        self.assertGreater(b["alias_expected_bin_count"], 0)
        self.assertGreater(b["nonharmonic_floor_dbfs"], a["nonharmonic_floor_dbfs"] + 25)

    def test_nonfinite(self):
        data = np.zeros((50, 2))
        data[8, 0] = np.nan
        self.assertEqual(basic(data)["nonfinite_samples"], 1)

    def test_click_and_silence(self):
        data = np.zeros((48000, 2))
        data[10000:20000] = .2
        metrics = patch_metrics(data)
        self.assertGreaterEqual(metrics["silence_segments"], 1)
        self.assertEqual(metrics["nonfinite_samples"], 0)

    def test_click_detector_known_answer_sine_and_saw(self):
        rate = 48000
        time = np.arange(rate * 2) / rate
        sine = .1 * np.sin(math.tau * 440 * time)
        saw = .1 * (2 * ((440 * time + .5) % 1) - 1)
        for label, clean in (("sine", sine), ("saw", saw)):
            with self.subTest(shape=label):
                self.assertEqual(click_events(clean, rate), [])
                shifted = clean.copy()
                shifted[int(rate * .31):] += .6
                shifted[int(rate * 1.13):] -= .6
                found = click_events(shifted, rate)
                self.assertEqual(len(found), 2, found)
                self.assertAlmostEqual(found[0]["time_s"], .31, delta=.003)
                self.assertAlmostEqual(found[1]["time_s"], 1.13, delta=.003)
                for event in found:
                    self.assertAlmostEqual(event["size_fs"], .6, delta=.1)
                    self.assertGreaterEqual(event["highpass_energy_ratio"], 3)
                stereo = np.column_stack([shifted, shifted])
                report = patch_metrics(stereo, rate)
                self.assertEqual(report["click_count"], 2)
                self.assertEqual(len(report["click_events"]), 2)
                self.assertNotIn("click_delta_outliers", report)

    def test_direct_envelope_timing(self):
        rate = 48000
        x = np.concatenate([np.linspace(0, 1, 2400), np.ones(21600),
                            np.linspace(1, 0, 4800), np.zeros(19200)])
        stereo = np.column_stack([x, x])
        record = direct_envelope_metrics(stereo, 0, 24000, .05, .1)
        self.assertAlmostEqual(record["rise_measured_s"], .05, delta=.001)
        self.assertAlmostEqual(record["fall_measured_s"], .1, delta=.002)

    def test_filter_cutoff_and_resonance_interpolation(self):
        rate = 48000
        rng = np.random.default_rng(17)
        dry = rng.normal(0, .1, rate * 3)
        # Third-order lowpass IIR has an analytic -3.01 dB corner at 1k.
        wet = signal.sosfilt(signal.butter(3, 1000, fs=rate, output="sos"), dry)
        stereo = lambda x: np.column_stack([x, x])
        record = filter_metrics(stereo(dry), stereo(wet), rate,
                                cutoff_hz=1000, resonance=0, output_tap="test.lowpass")
        self.assertEqual(record["output_tap"], "test.lowpass")
        self.assertAlmostEqual(record["cutoff_3db_hz"], 1000, delta=80)
        self.assertAlmostEqual(record["cutoff_error_hz"], 0, delta=80)
        f = np.arange(0, 4000, 100, dtype=float)
        response = -((f - 750) / 200) ** 2 + 2
        from metrics import parabolic_peak_hz
        self.assertAlmostEqual(parabolic_peak_hz(f, response, 7), 750, delta=1)

    def test_sweep_residual_ratio_known_answer(self):
        rate = 48000
        fast_time = np.arange(rate) / rate
        slow_time = np.arange(rate * 8) / rate
        fast = .1 * np.sin(math.tau * 440 * fast_time)
        fast += .08 * np.sin(math.tau * 8000 * fast_time)
        slow = .1 * np.sin(math.tau * 440 * slow_time)
        record = sweep_residual_metrics(fast, slow, rate)
        self.assertGreater(record["fast_to_slow_highpass_ratio"], 10)
        self.assertEqual(record["fast_duration_s"], 1)
        self.assertEqual(record["slow_duration_s"], 8)

    def test_post_impulse_tail_rms_known_answer(self):
        rate = 48000
        silent = np.zeros(rate * 3)
        silent[0] = 1
        measure = self_oscillation_metrics(silent, rate)
        self.assertEqual(measure["status"], "measured")
        self.assertEqual(measure["tail_rms_fs"], 0)
        sustained = silent.copy()
        sustained[rate * 2:] = .1
        active = self_oscillation_metrics(sustained, rate)
        self.assertAlmostEqual(active["tail_rms_fs"], .1, places=7)

    def test_response_and_step(self):
        t = np.arange(48000) / 48000
        dry = np.column_stack([np.sin(t * math.tau * 440)] * 2)
        wet = dry * .5
        response = filter_metrics(dry, wet)
        self.assertEqual(len(response["frequency_hz"]), 2049)
        index = int(np.argmin(abs(np.asarray(response["frequency_hz"]) - 440)))
        self.assertAlmostEqual(response["magnitude_db"][index], -6.0206, places=2)
        self.assertIsNotNone(step_metrics(wet, 24000)["highpass_peak_fs"])


if __name__ == "__main__":
    unittest.main()
