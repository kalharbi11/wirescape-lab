# SPDX-License-Identifier: GPL-3.0-only
"""Device-free counter evidence regressions for OB-g7 (#417)."""
import unittest
import soak


class CounterEvidenceTests(unittest.TestCase):
    def test_first_failure_keeps_failing_sample(self):
        key = 'osc.routes.1.dropped'
        before = {key: 592}
        after = {key: 1324}
        result = {'counters_before': {}, 'counters_after': {}}
        with self.assertRaises(soak.Stop) as error:
            soak.record_counters(result, before, after)
        self.assertEqual(error.exception.check, 'counter_rise')
        self.assertEqual(result['counters_before'], before)
        self.assertEqual(result['counters_after'], after)

    def test_mixed_new_osc_counter_is_not_silently_ignored(self):
        baseline = {'midi.dropped': 0}
        current = {'midi.dropped': 0, 'osc.routes.1.dropped': 592}
        result = {'counters_before': {}, 'counters_after': {}}
        with self.assertRaises(soak.Stop) as error:
            soak.record_counters(result, baseline, current)
        self.assertEqual(error.exception.check, 'counter_rise')
        self.assertEqual(result['counters_before']['osc.routes.1.dropped'], 0)
        self.assertEqual(result['counters_after'], current)

    def test_first_osc_sample_counts_drops_since_fresh_service_start(self):
        key = 'osc.routes.1.dropped'
        result = {'counters_before': {}, 'counters_after': {}}
        with self.assertRaises(soak.Stop) as error:
            soak.record_counters(result, {}, {key: 987})
        self.assertEqual(error.exception.check, 'counter_rise')
        self.assertEqual(result['counters_before'], {key: 0})
        self.assertEqual(result['counters_after'], {key: 987})

    def test_midi_reset_preserves_actual_before_and_after(self):
        result = {'midi_received_before': 0, 'midi_received_after': 5661}
        with self.assertRaises(soak.Stop) as error:
            soak.record_midi_received(result, 3)
        self.assertEqual(error.exception.check, 'midi_counter_reset')
        self.assertIn('5661 -> 3', error.exception.detail)
        self.assertEqual(result['midi_received_after'], 3)


if __name__ == '__main__':
    unittest.main()
