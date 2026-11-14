# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue probe metadata extraction tests."""
import unittest

from run_all import descriptors, markdown_rows, modules


class CatalogueTests(unittest.TestCase):
    def test_catalogue_coverage(self):
        known = set(modules())
        observed = descriptors()
        self.assertTrue(known)
        self.assertFalse(known - set(observed))

    def test_parameter_forms(self):
        info = descriptors()
        self.assertIn("scale", info["essentials.quantizer"]["parameters"])
        self.assertEqual(info["essentials.quantizer"]["parameters"]["scale"]["max"], 13)
        self.assertIn("run", info["example.step_sequencer"]["parameters"])
        self.assertEqual(info["example.step_sequencer"]["parameters"]["run"]["initial"], 1)

    def test_fact_table_attribution(self):
        lines = markdown_rows([{"module": "essentials.vco",
                               "status": "measured", "peak_fs": .5},
                              {"module": "essentials.adsr",
                               "status": "unavailable",
                               "reason": "no signal captured"}])
        self.assertIn("module", lines[0])
        self.assertIn("status", lines[0])
        self.assertIn("essentials.vco", lines[2])
        self.assertIn("no signal captured", lines[3])

    def test_port_hints(self):
        info = descriptors()
        self.assertIn({"port": "clock", "type": "WS2_GATE"}, info["essentials.clock"]["outputs"])
        self.assertIn({"port": "pitch", "type": "WS2_PITCH"}, info["essentials.quantizer"]["outputs"])


if __name__ == "__main__":
    unittest.main()
