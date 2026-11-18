# SPDX-License-Identifier: GPL-3.0-only
"""Device-free synthetic offline analysis; ABI1 execution and manual capture removed."""
import unittest
from analysis import analyse, pilot, resample, stimulus


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.reference = pilot(stimulus('pulses', 1))

    def test_clean_capture_has_latency_and_passes(self):
        report = analyse(self.reference, [0.0] * 4800 + self.reference + [0.0] * 4800)
        self.assertEqual(report['status'], 'pass', report)
        self.assertAlmostEqual(report['metrics']['latency_ms'], 100)

    def test_silence_is_detected(self):
        self.assertIn('silence', analyse(self.reference, [0.0] * len(self.reference))['failures'])

    def test_clipping_is_detected(self):
        x = self.reference.copy()
        x[5000:5500] = [1.0] * 500
        self.assertIn('clipping', analyse(self.reference, x)['failures'])

    def test_mismatch_is_detected(self):
        self.assertIn('mismatch', analyse(self.reference, pilot(stimulus('sweep', 1)))['failures'])

    def test_dropout_is_detected(self):
        x = self.reference.copy()
        x[5000:7500] = [0.0] * 2500
        result = analyse(self.reference, x)
        self.assertIn('dropout', result['failures'])
        self.assertGreater(result['metrics']['dropout_windows'], 0)

    def test_discontinuity_is_detected(self):
        x = self.reference.copy()
        x[5000] += 0.1
        self.assertIn('discontinuity', analyse(self.reference, x)['failures'])

    def test_truncated_capture_fails(self):
        self.assertIn('dropout', analyse(self.reference, self.reference[:-5000])['failures'])

    def test_sample_rate_conversion_and_gain(self):
        x = [0.0] * 4410 + resample(self.reference, 48000, 44100) + [0.0] * 4410
        result = analyse(self.reference, [v * 0.8 for v in x], 44100)
        self.assertEqual(result['status'], 'pass', result)
        self.assertTrue(result['metrics']['resampled'])

    def test_audio_outside_reference_is_detected(self):
        result = analyse(self.reference, self.reference + [0.02] * 4800)
        self.assertIn('unexpected_audio', result['failures'])

    def test_shifted_envelope_edges_are_detected(self):
        x = self.reference[:1280] + [0.0] * 2000 + self.reference[1280:]
        self.assertIn('timing', analyse(self.reference, x)['failures'])

    def test_bounds_and_nonfinite(self):
        for x in ([], [float('nan')] * 2000):
            with self.assertRaises(ValueError):
                analyse(self.reference, x)
        with self.assertRaises(ValueError):
            stimulus('tone', 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
