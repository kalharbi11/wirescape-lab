# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue evidence for instruction-count coverage; no devices or binaries."""
import unittest

from instructions import modules
from compare import compare


class InventoryTests(unittest.TestCase):
    def test_frozen_34_and_explicit_experimental_entries_are_included(self):
        catalogue = modules()
        from bench.golden.inventory import EXPERIMENTAL, allowed_ids, golden_ids
        self.assertEqual(set(catalogue), allowed_ids())
        self.assertEqual(len(golden_ids()), 34)
        self.assertEqual(EXPERIMENTAL, {
            "essentials.cv_to_notes", "essentials.poly_merge", "essentials.poly_split",
        })
        self.assertEqual(len(catalogue), 37)
        self.assertIn("osc.out", catalogue)

    def test_missing_osc_out_rows_fail_coverage(self):
        baseline = {"schema": 1, "machine": "linux-x64",
                    "method": "callgrind-Ir-two-length-difference-v1",
                    "rows": [{"id": "module/essentials.vco/voices1",
                              "status": "measured", "ir_per_block": 100}]}
        current = {"schema": 1, "machine": "linux-x64",
                   "method": "callgrind-Ir-two-length-difference-v1",
                   "rows": baseline["rows"] + [
                       {"id": "module/osc.out/voices1", "status": "measured",
                        "ir_per_block": 50}]}
        _, failures = compare(baseline, current)
        self.assertTrue(any("module/osc.out/voices1: missing baseline row" in f
                            for f in failures))


if __name__ == "__main__":
    unittest.main()
