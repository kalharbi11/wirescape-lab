# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue probe metadata extraction tests."""
import unittest

from run_all import (cabled_module_patch, descriptors, linear_sweep_events,
                     markdown_rows, modules, parameter_info, steady_module_patch)


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

    def test_continuous_and_stepped_parameters(self):
        flags = ('ws::param("rate", "Rate", 1, 200, 20, "Hz", flags, WS2_LINEAR, 0),'
                 'ws::param("shape", "Shape", 0, 3, 0, "", stepped, WS2_LINEAR, 1)')
        parsed = parameter_info(flags)
        self.assertFalse(parsed["rate"]["stepped"])
        self.assertTrue(parsed["shape"]["stepped"])
        self.assertTrue(descriptors()["ports.macro_oscillator"]["parameters"]["model"]["stepped"])
        self.assertFalse(descriptors()["essentials.vcf"]["parameters"]["cutoff"]["stepped"])

    def test_linear_sweep_endpoints_and_gate_fixture(self):
        events = linear_sweep_events("cutoff", 20, 20000, 48000, 1)
        self.assertEqual(events[0]["frame"], 0)
        self.assertEqual(events[0]["value"], 20)
        self.assertEqual(events[-1]["frame"], 47999)
        self.assertEqual(events[-1]["value"], 20000)
        self.assertTrue(all(x["frame"] < y["frame"] for x, y in zip(events, events[1:])))
        slower = linear_sweep_events("cutoff", 20, 20000, 48000, 8)
        self.assertEqual(len(events), 121)
        self.assertEqual(len(slower), 121)
        self.assertLessEqual(len(slower), 128)
        self.assertEqual(slower[-1]["frame"], 8 * 48000 - 1)
        self.assertEqual([e["value"] for e in slower], [e["value"] for e in events])
        with self.assertRaisesRegex(ValueError, "renderer event cap"):
            linear_sweep_events("cutoff", 20, 20000, 48000, 8, control_points=129)
        descriptor = descriptors()["essentials.chaos_lite"]
        patch, reason = steady_module_patch("essentials.chaos_lite", descriptor)
        self.assertIsNone(reason)
        incoming = [c["to"]["port"] for c in patch["connections"]]
        self.assertIn("gate", incoming)
        self.assertIn("velocity", incoming)

    def test_cabled_fixture_does_not_duplicate_existing_input(self):
        catalogue = descriptors()
        for ident in ("essentials.vcf", "essentials.ladder", "fx.reverb"):
            with self.subTest(module=ident):
                patch, selected, reason = cabled_module_patch(ident, catalogue[ident])
                self.assertIsNone(reason)
                incoming = [edge for edge in patch["connections"]
                            if edge["to"]["module"] == 1 and
                               edge["to"]["port"] == selected["port"]]
                self.assertEqual(len(incoming), 1)
                origin = incoming[0]["from"]["module"]
                source = next(node for node in patch["modules"] if node["id"] == origin)
                self.assertEqual(source["module"], "essentials.vco")
                self.assertEqual(source["parameters"]["frequency"], 3520)

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
