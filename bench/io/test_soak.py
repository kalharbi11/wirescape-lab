# SPDX-License-Identifier: GPL-3.0-only
"""Offline self-tests. No engine, hardware, LAN, audio or external packages."""
import json
from pathlib import Path
import tempfile
import unittest

import soak


class SoakTests(unittest.TestCase):
    def test_profile_shapes(self):
        for profile in soak.PROFILES:
            graph = soak.patch(profile, 9000, 9001)
            self.assertEqual(graph["format"], "wirescape.native.patch")
            self.assertFalse(graph["modules"][0]["config"]["lan"])
            self.assertEqual(graph["modules"][1]["config"]["port"], 9001)
            rows = [row for module in graph["modules"] if 10 <= module["id"] < 18
                    for row in module["config"]["rows"]]
            self.assertEqual(len(rows), 64 if profile in soak.OSC_LOAD_PROFILES else 0)
            self.assertEqual(len({row["pattern"] for row in rows}), len(rows))
            if rows:
                self.assertEqual({row["kind"] for row in rows}, {"cv", "gate"})
            midi = [m for m in graph["modules"] if m["module"] == "midi.in"]
            converter = [m for m in graph["modules"] if m["module"] == "midi.to_cv"]
            self.assertEqual(len(midi), int(profile in soak.MIDI_PROFILES))
            self.assertEqual(len(converter), len(midi))
            if midi:
                self.assertEqual(midi[0]["config"]["endpoint"], "all_enabled")
                self.assertEqual(converter[0]["parameters"]["voice_count"], 4)
                self.assertIn({"kind": "event",
                               "from": {"module": 80, "port": "midi"},
                               "to": {"module": 81, "port": "midi"}}, graph["connections"])

    def test_midi_profile_uses_injected_flag_only(self):
        for profile in soak.PROFILES:
            args = soak.sidecar_args("engine", "settings.json", profile)
            self.assertEqual(args[:5], ["engine", "--null-audio", "--bench-summary",
                                        "--settings", "settings.json"])
            self.assertEqual("--scripted-midi" in args, profile in soak.MIDI_PROFILES)
            self.assertNotIn("--confirm-midi", args)
            self.assertNotIn("--confirm-lan", args)

    def test_midi_release_panic_and_missing_counter_coverage(self):
        data = {"received": 16, "dropped": 0, "ring_full": 0,
                "malformed": 0, "send_fail": 0, "release_panics": 0}
        status = {"midi": {"counters": data}}
        self.assertEqual(soak.midi_received(status), 16)
        first = soak.counters({"status": status})
        for name in soak.MIDI_STOP_FIELDS:
            increased = dict(first)
            increased["midi." + name] += 1
            with self.assertRaises(soak.Stop) as error:
                soak.check_counters(first, increased)
            self.assertEqual(error.exception.check, "counter_rise")
        for invalid in ({"midi": {}},
                        {"midi": {"counters": {**data, "received": True}}},
                        {"midi": {"counters": {k: v for k, v in data.items()
                                              if k != "release_panics"}}}):
            with self.assertRaises(soak.Stop) as error:
                soak.midi_received(invalid)
            self.assertEqual(error.exception.check, "midi_counters_unavailable")

    def test_osc_codec(self):
        for value in (0, .2, .5, 1):
            address, got = soak.decode(soak.encode("/io/seq", value))
            self.assertEqual(address, "/io/seq")
            self.assertAlmostEqual(got, value, places=6)

    def test_kill_drop_stuck_fault_injection(self):
        self.assertEqual(soak.self_test(), ["engine_exit", "missing_echo", "stuck_gate"])

    def test_successful_sequence_and_edges(self):
        watch = soak.Watch()
        _, value = watch.send_seq(1)
        watch.send_gate(1, True)
        watch.receive(1.003, "/io/echo", value)
        watch.receive(1.005, "/io/edge", 1)
        watch.send_gate(1.020, False)
        watch.receive(1.025, "/io/edge", 0)
        watch.check(1.040)
        self.assertAlmostEqual(watch.latencies_ms[0], 3)
        self.assertFalse(watch.expected_edges)
        self.assertFalse(watch.expected_seq)

    def test_counter_rise_reset(self):
        first = soak.counters({"status": {"osc": {
            "routes": [{"module": "1", "dropped": 0}],
            "out": [{"module": "2", "dropped": 0}]},
            "midi": {"ring_full": 0}}})
        for key in ("osc.routes.1.dropped", "osc.out.2.dropped", "midi.ring_full"):
            increased = dict(first)
            increased[key] = 1
            with self.assertRaises(soak.Stop) as caught:
                soak.check_counters(first, increased)
            self.assertEqual(caught.exception.check, "counter_rise")
        soak.check_counters(first, first)
        self.assertEqual(soak.counters({"status": {"midi": {"release_panic": 0}}}),
                         {"midi.release_panic": 0})

    def test_bench_fault(self):
        stats = soak.bench_line("notice\nbench blocks=12 p99=2.2 overruns=0 faults=0 overrun_render_count=0 overrun_wake_count=0\n")
        self.assertEqual(stats["p99"], 2.2)
        soak.check_bench(stats)
        stats["overruns"] = 1
        with self.assertRaises(soak.Stop) as caught:
            soak.check_bench(stats)
        self.assertEqual(caught.exception.check, "bench_fault")

    def test_tier_baseline_and_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.json"
            path.write_text(json.dumps({
                "status": "passed", "tier": "L0", "source_sha": "abcde",
                "profile": "osc-gates", "edit_mode": "still", "p99_ms": 7.1}))
            self.assertEqual(soak.load_baseline(path, "abcde", "osc-gates", "still"), 7.1)
            soak.check_previous(path, "L1", "abcde", "osc-gates", "still")
            with self.assertRaises(soak.Stop):
                soak.check_previous(path, "L2", "abcde", "osc-gates", "still")
            with self.assertRaises(soak.Stop):
                soak.load_baseline(path, "different", "osc-gates", "still")

    def test_expected_failure_requires_measured_edit_failure(self):
        watch = soak.Watch()
        watch.send_seq(10.0)
        watch.begin_edit(1, 10.01)
        watch.end_edit(10.03)
        with self.assertRaises(soak.Stop) as caught:
            watch.check(10.26)
        failure = {"check": caught.exception.check, "detail": caught.exception.detail}
        observation = watch.attribute_fault(caught.exception, 10.26)
        self.assertIsNotNone(observation)
        self.assertEqual(observation["edit_id"], 1)
        self.assertEqual(observation["pending_at_edit"]["sequences"], 1)
        self.assertEqual(soak.classify("config-edits", False, failure, observation)[0], "xfail")
        self.assertEqual(soak.classify("config-edits", False, failure)[0], "failed")
        self.assertEqual(soak.classify("config-edits", False, None)[0], "xpass")
        self.assertEqual(soak.classify("config-edits", True, None)[0], "passed")
        self.assertEqual(soak.classify("still", False, failure, observation)[0], "failed")

    def test_later_unrelated_sequence_fault_after_prior_edit_is_failure(self):
        watch = soak.Watch()
        _, value = watch.send_seq(10.0)
        watch.begin_edit(1, 10.01)
        watch.end_edit(10.03)
        watch.receive(10.04, "/io/echo", value)  # pre-edit in-flight seq resolved
        watch.send_seq(10.05)                     # new, unrelated sequence
        with self.assertRaises(soak.Stop) as caught:
            watch.check(10.31)
        self.assertEqual(caught.exception.check, "missing_echo")
        self.assertIsNone(watch.attribute_fault(caught.exception, 10.31))
        failure = {"check": caught.exception.check, "detail": caught.exception.detail}
        self.assertEqual(soak.classify("config-edits", False, failure)[0], "failed")

    def test_old_edit_does_not_excuse_late_fault(self):
        watch = soak.Watch()
        watch.send_seq(10)
        watch.begin_edit(1, 10.01)
        watch.end_edit(10.03)
        with self.assertRaises(soak.Stop) as caught:
            watch.check(11)
        self.assertIsNone(watch.attribute_fault(caught.exception, 11))
        failure = {"check": caught.exception.check, "detail": caught.exception.detail}
        self.assertEqual(soak.classify("config-edits", False, failure)[0], "failed")

    def test_unrelated_gate_edge_after_prior_edit_remains_failure(self):
        watch = soak.Watch()
        watch.send_seq(10)
        watch.begin_edit(1, 10.01)
        watch.end_edit(10.03)
        watch.send_gate(10.04, True)  # rising edge is *not* part of edit snapshot
        with self.assertRaises(soak.Stop) as caught:
            watch.check(10.10)
        self.assertEqual(caught.exception.check, "missing_gate_edge")
        self.assertIsNone(watch.attribute_fault(caught.exception, 10.10))

    def test_qualifying_gate_stuck_across_edit(self):
        watch = soak.Watch()
        watch.send_gate(10.0, True)
        watch.receive(10.003, "/io/edge", 1.0)
        watch.begin_edit(1, 10.01)
        watch.end_edit(10.03)
        watch.send_gate(10.04, False)
        with self.assertRaises(soak.Stop) as caught:
            watch.check(10.10)
        self.assertEqual(caught.exception.check, "stuck_gate")
        observation = watch.attribute_fault(caught.exception, 10.10)
        self.assertIsNotNone(observation)
        failure = {"check": caught.exception.check, "detail": caught.exception.detail}
        self.assertEqual(soak.classify("config-edits", False, failure, observation)[0], "xfail")

    def test_xfail_bad_shutdown_bench_remains_failure_and_retains_a2(self):
        observation = {"edit_id": 1, "fault": {"check": "missing_echo",
                                              "detail": "inflight seq 2"}}
        result = {"status": "xfail", "first_failure": {"check": "A2_expected_failure"},
                  "a2_observation": observation, "bench": None}
        bad = "bench blocks=100 overruns=1 faults=0 overrun_render_count=0 overrun_wake_count=0"
        soak.apply_shutdown_checks(result, 0, bad)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["first_failure"]["check"], "bench_fault")
        self.assertEqual(result["a2_observation"], observation)
        self.assertEqual(result["bench"]["overruns"], 1)

    def test_xfail_missing_bench_and_exit_also_fail(self):
        for code, stderr, expected in [
            (0, "bench blocks=100 overruns=0 faults=0", "bench_missing"),
            (0, "invalid log with no bench line", "bench_missing"),
            (137, "bench blocks=10 overruns=0 faults=0 "
             "overrun_render_count=0 overrun_wake_count=0", "engine_exit"),
        ]:
            result = {"status": "xfail", "first_failure": {"check": "A2_expected_failure"},
                      "a2_observation": {"edit_id": 1}, "bench": None}
            soak.apply_shutdown_checks(result, code, stderr)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["first_failure"]["check"], expected)
            self.assertEqual(result["a2_observation"], {"edit_id": 1})

    def test_missing_engine_writes_both_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            result = soak.run_tier(path / "missing-engine", "osc-gates", "still", "L0",
                                   path, 9000, 9001, None, None, False)
            self.assertEqual(result["status"], "blocked")
            target = path / "osc-gates" / "still" / "L0"
            self.assertTrue((target / "report.json").is_file())
            self.assertTrue((target / "report.md").is_file())
            self.assertEqual(json.loads((target / "report.json").read_text())["first_failure"]["check"],
                             "engine_missing")


if __name__ == "__main__":
    unittest.main()
