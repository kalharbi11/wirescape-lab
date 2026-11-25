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


    def test_osc_drop_report_deduplicates_listener_observations(self):
        rows = [
            {"module": "1", "port": 9000, "dropped": 2,
             "budget_dropped": 2, "enqueue_dropped": 0,
             "listener_budget_dropped": 2, "listener_enqueue_dropped": 4},
            {"module": "17", "port": 9000, "dropped": 6,
             "budget_dropped": 2, "enqueue_dropped": 4,
             "listener_budget_dropped": 2, "listener_enqueue_dropped": 4},
            {"module": "18", "port": 9001, "dropped": 0,
             "budget_dropped": 0, "enqueue_dropped": 0,
             "listener_budget_dropped": 0, "listener_enqueue_dropped": 0},
        ]
        status = {"osc": {"routes": rows}}
        report = soak.osc_drop_diagnostics(status)
        self.assertEqual(report["routes"]["17"],
                         {"port": 9000, "budget_dropped": 2, "enqueue_dropped": 4})
        self.assertEqual(report["listeners"]["9000"],
                         [{"budget_dropped": 2, "enqueue_dropped": 4}])
        self.assertEqual(report["listeners"]["9001"],
                         [{"budget_dropped": 0, "enqueue_dropped": 0}])
        # The existing strict stop oracle must see only the legacy counters.
        self.assertEqual(soak.counters(status), {
            "osc.routes.1.dropped": 2, "osc.routes.17.dropped": 6,
            "osc.routes.18.dropped": 0})

    def test_osc_drop_report_never_fills_missing_or_merges_disagreeing_counts(self):
        status = {"osc": {"routes": [
            {"module": "1", "port": 9000, "listener_budget_dropped": 2,
             "listener_enqueue_dropped": 4},
            {"module": "17", "port": 9000, "listener_budget_dropped": 2,
             "listener_enqueue_dropped": 5, "enqueue_dropped": 5},
            {"module": "18", "port": 9001, "dropped": 8},
        ]}}
        report = soak.osc_drop_diagnostics(status)
        self.assertEqual(report["routes"], {"17": {"port": 9000, "enqueue_dropped": 5}})
        self.assertEqual(report["listeners"], {"9000": [
            {"budget_dropped": 2, "enqueue_dropped": 4},
            {"budget_dropped": 2, "enqueue_dropped": 5}]})
        self.assertEqual(soak.osc_drop_diagnostics({"osc": {"routes": [
            {"module": "1", "port": 9000, "dropped": 8}]} }),
            {"routes": {}, "listeners": {}})


    def test_a67_shutdown_reason_summaries_are_additive_and_epoch_local(self):
        line = ("osc_enqueue_reason module=17 port=9000 total=2 "
                "invalid=0 capacity=2 state=0 other=0")
        other = ("osc_enqueue_reason module=17 port=9000 total=3 "
                 "invalid=0 capacity=0 state=3 other=0")
        result = {"status": "failed", "first_failure": {"check": "counter_rise"}}
        soak.apply_shutdown_checks(result, 1, line + "\n" + other)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["first_failure"], {"check": "counter_rise"})
        self.assertEqual(result["osc_enqueue_reasons"], {
            "observations": [
                {"module": 17, "port": 9000, "total": 2, "invalid": 0,
                 "capacity": 2, "state": 0, "other": 0},
                {"module": 17, "port": 9000, "total": 3, "invalid": 0,
                 "capacity": 0, "state": 3, "other": 0}],
            "malformed": 0})
        # Different service lifetimes may share a node and port. Do not merge.

    def test_a67_missing_or_invalid_summary_is_not_a_zero(self):
        missing = {"status": "failed"}
        soak.apply_shutdown_checks(missing, 1, "unrelated stderr")
        self.assertNotIn("osc_enqueue_reasons", missing)
        invalid = {"status": "failed"}
        soak.apply_shutdown_checks(invalid, 1,
            "osc_enqueue_reason module=17 port=9000 total=2 "
            "invalid=0 capacity=1 state=0 other=0\n"
            "osc_enqueue_reason module=18 port=9000 total=1 invalid=0")
        self.assertEqual(invalid["osc_enqueue_reasons"],
                         {"observations": [], "malformed": 2})

if __name__ == '__main__':
    unittest.main()
