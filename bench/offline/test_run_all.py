# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue probe metadata extraction tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from run_all import (cabled_module_patch, descriptors, linear_sweep_events,
                     markdown_rows, modules, parameter_info, parsed_command,
                     scripted_keyboard_patch, soak_patches, soak_seconds_for,
                     steady_module_patch)


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


class ScriptedSoakTests(unittest.TestCase):
    def source_patch(self):
        return {
            "format": "wirescape.native.patch", "version": 2,
            "modules": [{"id": 3, "module": "host.keyboard", "version": 1,
                         "parameters": {"voices": 8}},
                        {"id": 8, "module": "essentials.output", "version": 2,
                         "parameters": {}}],
            "connections": [{"kind": "signal",
                             "from": {"module": 3, "port": "pitch"},
                             "to": {"module": 8, "port": "audio"}}],
            "outputs": [{"module": 8, "port": "audio", "bus_channel": 0}]}

    def test_derived_patch_preserves_original_and_existing_cables(self):
        original = self.source_patch()
        generated, count = scripted_keyboard_patch(original)
        self.assertEqual(count, 1)
        self.assertEqual(original["modules"][0]["module"], "host.keyboard")
        self.assertEqual(original["modules"][0]["parameters"], {"voices": 8})
        self.assertEqual(generated["modules"][0]["module"], "example.step_sequencer")
        self.assertEqual(generated["modules"][0]["version"], 2)
        self.assertEqual(generated["modules"][0]["parameters"], {"run": 1, "length": 8})
        self.assertEqual(generated["modules"][-1]["id"], 9)
        self.assertEqual(generated["modules"][-1]["module"], "essentials.clock")
        self.assertEqual(generated["connections"][0], original["connections"][0])
        self.assertEqual(generated["connections"][-1], {
            "kind": "signal", "from": {"module": 9, "port": "clock"},
            "to": {"module": 3, "port": "clock"}})
        self.assertIsNone(scripted_keyboard_patch({
            "modules": [{"id": 3, "module": "essentials.vco"}]})[0])

    def test_duration_defaults_and_validation(self):
        self.assertEqual(soak_seconds_for(False, None), 30.)
        self.assertEqual(soak_seconds_for(True, None), .05)
        self.assertEqual(soak_seconds_for(False, 5.25), 5.25)
        for seconds in (0., -1., 3601., float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                soak_seconds_for(False, seconds)

    @mock.patch("run_all.call")
    def test_nonzero_returns_original_stderr_and_code(self, fake_call):
        fake_call.return_value = {"exit_code": 2, "stdout": "",
                                  "stderr": "module_cpu_probe: create/prepare failed\n"}
        actual = parsed_command(["fake"], prefix="module_cpu_probe ")
        self.assertEqual(actual["status"], "unavailable")
        self.assertEqual(actual["exit_code"], 2)
        self.assertIn("create/prepare failed", actual["reason"])
        self.assertEqual(actual["error_text"], "module_cpu_probe: create/prepare failed")

    @mock.patch("run_all.save")
    @mock.patch("run_all.parsed_command")
    def test_keyboard_fallback_is_measurement_with_explicit_provenance(self, run, save):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "keyboard.json"
            path.write_text(json.dumps(self.source_patch()), encoding="utf-8")

            def emulate(command, **kwargs):
                candidate = Path(command[2])
                if candidate == path:
                    return {"status": "unavailable", "exit_code": 1,
                            "error_text": "wirescape_soak: graph setup/render failed"}
                return {"status": "measured", "render_ns": {"p99": 100},
                        "seconds": float(command[-1])}
            run.side_effect = emulate
            result = soak_patches("wirescape_soak", [path],
                                  {"machine": {"cpu": "synthetic"}}, Path(temp), 30., "engine")
            self.assertEqual(result, 1)
            output = {call.args[2]: call.args[4] for call in save.call_args_list}
            rows = output["patch_soak"]
            self.assertEqual(len(rows), 3)
            for row in rows:
                self.assertEqual(row["status"], "measured")
                self.assertEqual(row["input_mode"], "clocked_step_sequencer_for_host_keyboard")
                self.assertEqual(row["source_patch_exit_code"], 1)
                self.assertEqual(row["keyboard_sources_replaced"], 1)
                self.assertEqual(row["seconds"], 30.)
            self.assertEqual(output["soak_failures"], [])


if __name__ == "__main__":
    unittest.main()
