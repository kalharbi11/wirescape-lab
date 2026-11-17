# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic failure-closed tests; no devices, Callgrind or network."""
import copy
import unittest

from bench.m1.paired import CHORD, FIELDS, REASON, compare_pair
from bench.gate.compare import expected_ids

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
        self.assertEqual(result["measured_count"], 95)
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


if __name__ == "__main__":
    unittest.main()
