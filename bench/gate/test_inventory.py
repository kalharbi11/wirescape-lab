# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue evidence for instruction-count coverage; no devices or binaries."""
import unittest

from instructions import modules
from compare import compare, module_sets


class InventoryTests(unittest.TestCase):
    def test_all_34_runtime_catalogue_entries_are_included(self):
        catalogue = modules()
        golden, experimental = module_sets()
        self.assertEqual(len(golden), 34)
        self.assertEqual(catalogue[:34], sorted(golden))
        self.assertEqual(catalogue[34:], sorted(experimental))  # 0020 section 7
        self.assertEqual(len(set(catalogue)), len(catalogue))
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
