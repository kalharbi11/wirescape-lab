# SPDX-License-Identifier: GPL-3.0-only
"""Pure DSP measurement tests; no hardware, network or built engine needed."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from metrics import (basic, filter_metrics, oscillator_metrics, patch_metrics,
                     read_audio, step_metrics)


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
