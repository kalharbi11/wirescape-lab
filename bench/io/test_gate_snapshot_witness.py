# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer checks for the bounded OSC Out snapshot model (#475)."""
import unittest

from gate_snapshot_witness import enumerate_schedules, run_schedule


class GateSnapshotTests(unittest.TestCase):
    def test_coherent_poll_before_publish(self):
        result = run_schedule(("C.blocks", "C.rises", "C.falls", "C.value",
                               "P.value", "P.rises", "P.blocks"))
        self.assertEqual(result["expected"], [0, 1, 0])
        self.assertEqual(result["emitted"], result["expected"])
        self.assertEqual(result["drops"], 0)

    def test_coherent_poll_after_publish(self):
        result = run_schedule(("P.value", "P.rises", "P.blocks",
                               "C.blocks", "C.rises", "C.falls", "C.value"))
        self.assertEqual(result["emitted"], [0, 1, 0])
        self.assertEqual(result["drops"], 0)

    def test_partial_publish_before_counter(self):
        result = run_schedule(("P.value", "C.blocks", "C.rises", "C.falls",
                               "C.value", "P.rises", "P.blocks"))
        self.assertEqual(result["snapshots"][1], {"blocks": 1, "rises": 0,
                                                  "falls": 0, "value": 1})
        self.assertEqual(result["emitted"], [0, 1, 0, 1, 0])
        self.assertEqual(result["drops"], 0)
        self.assertEqual(result["expected"], [0, 1, 0])

    def test_all_order_preserving_interleavings(self):
        rows = list(enumerate_schedules())
        self.assertEqual(len(rows), 35)
        self.assertEqual(len({tuple(row["schedule"]) for row in rows}), 35)
        self.assertTrue(any(row["emitted"] != row["expected"] for row in rows))
        self.assertTrue(any(row["emitted"] == row["expected"] for row in rows))
        self.assertTrue(all(row["drops"] == 0 for row in rows))

    def test_invalid_schedule_rejected(self):
        with self.assertRaises(ValueError):
            run_schedule(("C.value", "P.value"))


if __name__ == "__main__":
    unittest.main()
