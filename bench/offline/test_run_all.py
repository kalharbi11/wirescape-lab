# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue probe metadata extraction tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from run_all import (descriptors, markdown_rows, modules, scripted_keyboard_patch,
                     soak_seconds_for, soak_patches, parsed_command)


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
                                  "stderr": "module_cpu_probe: create/prepare failed\\n"}
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
