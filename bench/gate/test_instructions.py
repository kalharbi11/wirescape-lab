# SPDX-License-Identifier: GPL-3.0-only
"""Mocked native Callgrind probe evidence; no binaries, devices, or LAN."""
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from instructions import FRAMES, RATE, difference, module_rows, verify_module_probe


PROBE = {"module": "essentials.vco", "instances": 1, "channels": 1,
         "sample_rate": RATE, "block": FRAMES}


def evidence(blocks, *, module="essentials.vco", channels=1, faults=0, **overrides):
    report = {
        "module": module, "instances": 1, "sample_rate": RATE,
        "block": FRAMES, "channels": channels,
        "seconds": blocks * FRAMES / RATE, "input_mode": "normal",
        "blocks": blocks, "render_ns": {"max": 300, "p99": 200},
        "period_ns": 1e9 * FRAMES / RATE, "allocations": 0,
        "faults": faults, "peak": 0.5, "params": "", "alternate": "",
    }
    report.update(overrides)
    return "module_cpu_probe " + json.dumps(report) + "\n"


def completed(stdout, returncode=0):
    return subprocess.CompletedProcess(["valgrind", "probe"], returncode,
                                       stdout=stdout, stderr="")


def measure(result_12, result_24, ir=(1000, 2200)):
    with (patch("instructions.subprocess.run", side_effect=[
            completed(result_12), completed(result_24)]) as invoked,
          patch("instructions.read_ir", side_effect=ir) as reader):
        result = difference(lambda n: ["probe", "--blocks", n], "valgrind",
                            module_probe=PROBE)
    return result, invoked.call_count, reader.call_count


class ModuleEvidenceTests(unittest.TestCase):
    def test_healthy_two_length_known_answer(self):
        result, runs, totals = measure(evidence(12), evidence(24))
        self.assertEqual(result, {"totals": [1000, 2200], "ir_per_block": 100})
        self.assertEqual((runs, totals), (2, 2))

    def test_exit_zero_faults_rejected_at_first_length(self):
        with (patch("instructions.subprocess.run", return_value=completed(evidence(12, faults=24))),
              patch("instructions.read_ir") as reader):
            with self.assertRaisesRegex(RuntimeError, "faults=24"):
                difference(lambda n: ["probe"], "valgrind", module_probe=PROBE)
            reader.assert_not_called()

    def test_exit_zero_faults_rejected_at_second_length(self):
        with (patch("instructions.subprocess.run", side_effect=[
                completed(evidence(12)), completed(evidence(24, faults=24))]) as invoked,
              patch("instructions.read_ir", return_value=1000) as reader):
            with self.assertRaisesRegex(RuntimeError, "faults=24"):
                difference(lambda n: ["probe"], "valgrind", module_probe=PROBE)
            self.assertEqual(invoked.call_count, 2)
            self.assertEqual(reader.call_count, 1)

    def test_missing_malformed_oversized_and_duplicate_lines_rejected(self):
        bad = ("", "  ", "not module JSON",
               "module_cpu_probe {oops}", "module_cpu_probe {}",
               evidence(12) + evidence(12), "x" * 4097,
               evidence(12).replace('"faults": 0', '"faults": 24, "faults": 0'),
               evidence(12).replace('"faults": 0', '"faults": NaN'))
        expected = {**PROBE, "blocks": 12, "seconds": 12 * FRAMES / RATE}
        for stdout in bad:
            with self.subTest(stdout=repr(stdout[:35])):
                with self.assertRaises(RuntimeError):
                    verify_module_probe(stdout, expected)

    def test_missing_and_invalid_faults_rejected(self):
        expected = {**PROBE, "blocks": 12, "seconds": 12 * FRAMES / RATE}
        for faults in (None, -1, True, 0.0, "0", 12):
            with self.subTest(faults=faults):
                with self.assertRaisesRegex(RuntimeError, "faults"):
                    verify_module_probe(evidence(12, faults=faults), expected)
        no_faults = json.loads(evidence(12).split(" ", 1)[1])
        del no_faults["faults"]
        with self.assertRaisesRegex(RuntimeError, "faults"):
            verify_module_probe("module_cpu_probe " + json.dumps(no_faults), expected)

    def test_wrong_identity_window_and_parameters_rejected(self):
        expected = {**PROBE, "blocks": 12, "seconds": 12 * FRAMES / RATE}
        for override in ({"module": "essentials.vca"},
                         {"channels": 8}, {"instances": 2}, {"blocks": 24},
                         {"block": 64}, {"sample_rate": 44100},
                         {"seconds": .5}, {"input_mode": "denormal"},
                         {"params": "cutoff=100"}, {"alternate": "x=0:1:2"},
                         {"render_ns": {"max": -1, "p99": 3}},
                         {"period_ns": 0}, {"peak": "nan"},
                         {"allocations": -1}):
            with self.subTest(override=override):
                with self.assertRaises(RuntimeError):
                    verify_module_probe(evidence(12, **override), expected)

    def test_collector_marks_faulty_module_unavailable_without_losing_rows(self):
        with (patch("instructions.modules", return_value=["essentials.vco"]),
              patch("instructions.binary", return_value=Path("/tmp/module_cpu_probe")),
              patch("instructions.subprocess.run", side_effect=[
                  completed(evidence(12, faults=24)),
                  completed(evidence(12, channels=8)),
                  completed(evidence(24, channels=8))]),
              patch("instructions.read_ir", side_effect=[1000, 2200])):
            rows = module_rows(Path("/tmp"), "valgrind")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "module/essentials.vco/voices1")
        self.assertEqual(rows[0]["status"], "unavailable")
        self.assertIn("faults=24", rows[0]["reason"])
        self.assertNotIn("ir_per_block", rows[0])
        self.assertEqual(rows[1]["id"], "module/essentials.vco/voices8")
        self.assertEqual(rows[1]["status"], "measured")
        self.assertEqual(rows[1]["totals"], [1000, 2200])
        self.assertEqual(rows[1]["ir_per_block"], 100)


if __name__ == "__main__":
    unittest.main()
