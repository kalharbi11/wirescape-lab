# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic failure-closed tests; no devices, Callgrind or network."""
import copy
import unittest

from bench.m1.paired import CHORD, FIELDS, REASON, compare_pair
from bench.gate.compare import expected_ids, experimental_row_ids

BASE = "a" * 40
HEAD = "b" * 40


def fixture():
    doc = dict(schema=1, commit=BASE, machine="linux-x64", architecture="x86_64",
               valgrind_version="valgrind-3.23", method="callgrind-Ir-two-length-difference-v1",
               configuration="Release plus -g", sample_rate_hz=48000,
               measurement_block_frames=128, lengths_blocks=[12, 24],
               note_source="events")
    rows = []
    for key in sorted(expected_ids()):
        blocks = 20 if key.startswith("fixed/") else 12
        rows.append({"id": key, "status": "measured", "ir_per_block": 100.0,
                     "totals": [1000, 1000 + 100 * blocks]})
    doc["rows"] = rows
    new = copy.deepcopy(doc)
    new["commit"] = HEAD
    return doc, new


class StrictPairedTests(unittest.TestCase):
    def run_pair(self, base, head):
        return compare_pair(base, head, BASE, HEAD, "linux-x64")

    def test_equal_and_exact_boundary(self):
        b, h = fixture()
        h["rows"][0]["ir_per_block"] = 101.0
        blocks = 20 if h["rows"][0]["id"].startswith("fixed/") else 12
        h["rows"][0]["totals"][1] = 1000 + 101 * blocks
        self.assertEqual(self.run_pair(b, h)["status"], "passed")

    def test_above_one_percent_rejected(self):
        b, h = fixture()
        h["rows"][0]["ir_per_block"] = 102.0
        blocks = 20 if h["rows"][0]["id"].startswith("fixed/") else 12
        h["rows"][0]["totals"][1] = 1000 + 102 * blocks
        self.assertEqual(self.run_pair(b, h)["status"], "failed")

    def test_missing_duplicate_and_unexpected_row(self):
        for mutation in ("missing", "duplicate", "extra"):
            b, h = fixture()
            if mutation == "missing":
                h["rows"].pop()
            if mutation == "duplicate":
                h["rows"].append(copy.deepcopy(h["rows"][0]))
            if mutation == "extra":
                h["rows"].append({"id": "unexpected", "status": "measured",
                                  "ir_per_block": 1, "totals": [0, 12]})
            with self.subTest(mutation=mutation):
                self.assertEqual(self.run_pair(b, h)["status"], "failed")

    def test_provenance_and_pins_rejected(self):
        for field in FIELDS:
            b, h = fixture()
            h[field] = "wrong"
            with self.subTest(field=field):
                self.assertEqual(self.run_pair(b, h)["status"], "failed")
        b, h = fixture()
        h["commit"] = BASE
        self.assertEqual(self.run_pair(b, h)["status"], "failed")

    def test_chord_declared_paired_unavailable(self):
        b, h = fixture()
        for doc in (b, h):
            for row in doc["rows"]:
                if row["id"] in CHORD:
                    row.update(status="unavailable", reason=REASON)
                    row.pop("totals")
                    row.pop("ir_per_block")
        result = self.run_pair(b, h)
        self.assertEqual(result["status"], "passed", result["failures"])
        self.assertEqual(result["paired_unavailable_count"], 2)
        self.assertEqual(result["measured_count"], 94)
        self.assertTrue(all("NOT measured" in x["disposition"] for x in result["exceptions"]))

    def test_chord_unilateral_or_changed_reason_rejected(self):
        b, h = fixture()
        for doc in (b, h):
            for row in doc["rows"]:
                if row["id"] in CHORD:
                    row.update(status="unavailable", reason=REASON)
        h["rows"][next(i for i, x in enumerate(h["rows"]) if x["id"] in CHORD)]["reason"] = "different"
        self.assertEqual(self.run_pair(b, h)["status"], "failed")
        b, h = fixture()
        for row in b["rows"]:
            if row["id"] in CHORD:
                row.update(status="unavailable", reason=REASON)
        self.assertEqual(self.run_pair(b, h)["status"], "failed")

    def test_retired_historical_abi1_is_disclosed_not_compared(self):
        b, h = fixture()
        historic = {"id": "fixed/abi1_mono", "status": "measured",
                    "ir_per_block": 100.0, "totals": [1000, 3000]}
        b["rows"].append(copy.deepcopy(historic))
        result = self.run_pair(b, h)
        self.assertEqual(result["status"], "passed", result["failures"])
        self.assertEqual(result["expected_count"], 96)
        self.assertEqual(result["retired_count"], 1)
        self.assertEqual(result["measured_count"], 96)
        self.assertEqual(result["retired"][0]["id"], "fixed/abi1_mono")
        self.assertTrue(all(row["id"] != "fixed/abi1_mono" for row in result["measured"]))
        h["rows"].append(copy.deepcopy(historic))
        self.assertEqual(self.run_pair(b, h)["status"], "failed")
        h["rows"].pop()
        b["rows"][-1]["status"] = "unavailable"
        self.assertEqual(self.run_pair(b, h)["status"], "failed")
        b["rows"][-1] = dict(historic, id="fixed/unrecognized")
        self.assertEqual(self.run_pair(b, h)["status"], "failed")

    def test_other_unavailable_never_waived(self):
        b, h = fixture()
        for doc in (b, h):
            doc["rows"][0].update(status="unavailable", reason=REASON)
        self.assertEqual(self.run_pair(b, h)["status"], "failed")

    def test_invalid_totals_zero_nan(self):
        for bad in (0, float("nan"), float("inf")):
            b, h = fixture()
            h["rows"][0]["ir_per_block"] = bad
            with self.subTest(bad=bad):
                self.assertEqual(self.run_pair(b, h)["status"], "failed")



class ExperimentalNewRowTests(unittest.TestCase):
    """0020 section 7: head-only experimental rows are new; everything else stays strict."""

    @staticmethod
    def row(key, ir=100.0):
        return {"id": key, "status": "measured", "ir_per_block": ir,
                "totals": [1000, 1000 + int(ir * 12)]}

    def test_head_only_experimental_row_is_new_not_compared(self):
        b, h = fixture()
        key = sorted(experimental_row_ids())[0]
        h["rows"].append(self.row(key, 900.0))
        result = compare_pair(b, h, BASE, HEAD, "linux-x64")
        self.assertEqual(result["status"], "passed", result["failures"])
        self.assertEqual([r["id"] for r in result["new"]], [key])
        self.assertNotIn(key, [r["id"] for r in result["measured"]])

    def test_invalid_head_only_experimental_row_fails(self):
        b, h = fixture()
        key = sorted(experimental_row_ids())[0]
        h["rows"].append({"id": key, "status": "unavailable", "reason": "x"})
        self.assertEqual(compare_pair(b, h, BASE, HEAD, "linux-x64")["status"], "failed")

    def test_experimental_row_on_both_sides_stays_strict(self):
        b, h = fixture()
        key = sorted(experimental_row_ids())[0]
        b["rows"].append(self.row(key, 100.0))
        h["rows"].append(self.row(key, 100.0))
        self.assertEqual(compare_pair(b, h, BASE, HEAD, "linux-x64")["status"], "passed")
        h["rows"][-1] = self.row(key, 102.0)
        self.assertEqual(compare_pair(b, h, BASE, HEAD, "linux-x64")["status"], "failed")

    def test_experimental_row_lost_at_head_fails(self):
        b, h = fixture()
        b["rows"].append(self.row(sorted(experimental_row_ids())[0]))
        self.assertEqual(compare_pair(b, h, BASE, HEAD, "linux-x64")["status"], "failed")

    def test_head_only_golden_or_unknown_row_still_fails(self):
        b, h = fixture()
        h["rows"].append(self.row("module/not.listed/voices1"))
        self.assertEqual(compare_pair(b, h, BASE, HEAD, "linux-x64")["status"], "failed")


if __name__ == "__main__":
    unittest.main()
