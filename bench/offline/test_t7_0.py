# SPDX-License-Identifier: GPL-3.0-only
"""T7.0 source completeness, neutral unavailable rows and switch fixture routing."""
import copy
import json
import unittest
from unittest.mock import patch

import numpy as np

import run_all
import t7_0


def artifact():
    rows = [
        dict(module=t7_0.MODULE, waveform=wave, sample_rate_hz=rate,
             target_hz=hz, status="measured", nonfinite_samples=0,
             alias_expected_bin_count=3, alias_floor_dbfs=-24.5, rms_fs=.35)
        for rate, wave, hz in t7_0.CASES
    ]
    return dict(section="oscillators", provenance=dict(commit="a" * 40), rows=rows)


class T70Alias(unittest.TestCase):
    def test_exact_24_case_cross_product_and_source_pin(self):
        self.assertEqual(len(t7_0.CASES), 24)
        self.assertEqual(len(set(t7_0.CASES)), 24)
        observed = t7_0.extract_chaos(artifact(), "a" * 40)
        self.assertEqual(len(observed), 24)
        self.assertEqual({r["status"] for r in observed}, {"measured"})
        self.assertEqual({r["sample_rate_hz"] for r in observed}, set(t7_0.RATES))
        self.assertEqual({r["target_hz"] for r in observed}, set(t7_0.HERTZ))
        self.assertEqual({r["waveform"] for r in observed}, set(t7_0.WAVES))
        self.assertTrue(all(r["rms_fs"] == .35 and r["alias_floor_dbfs"] == -24.5
                            for r in observed))
        self.assertEqual(observed[0]["module"], "essentials.chaos_lite")
        with self.assertRaisesRegex(ValueError, "source commit"):
            t7_0.extract_chaos(artifact(), "b" * 40)

    def test_omitted_and_duplicate_source_cases_fail_closed(self):
        absent = artifact()
        absent["rows"].pop(0)
        with self.assertRaisesRegex(ValueError, "missing CHAOS alias"):
            t7_0.extract_chaos(absent, "a" * 40)
        repeated = artifact()
        repeated["rows"].append(copy.deepcopy(repeated["rows"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate CHAOS alias"):
            t7_0.extract_chaos(repeated, "a" * 40)

    def test_unavailable_cases_cannot_be_interpolated_as_measured(self):
        missing = artifact()
        missing["rows"][0]["status"] = "render_failed"
        missing["rows"][0]["reason"] = "sample-rate refused"
        missing["rows"][1]["alias_expected_bin_count"] = 0
        missing["rows"][1]["alias_floor_dbfs"] = -300
        missing["rows"][2]["nonfinite_samples"] = 1
        output = t7_0.extract_chaos(missing, "a" * 40)
        self.assertEqual([r["status"] for r in output[:3]], ["unavailable"] * 3)
        self.assertEqual(output[0]["reason"], "sample-rate refused")
        self.assertEqual(output[1]["reason"], "no isolated folded-alias FFT bins")
        self.assertIsNone(output[1]["alias_floor_dbfs"])
        self.assertIsNone(output[2]["rms_fs"])

    def test_dedicated_runner_captures_all_24_actual_probe_cases(self):
        rate_log, wave_log = [], []

        def fake_wav(renderer, patch_doc, events, seconds, *, rate):
            rate_log.append(rate)
            wave_log.append(patch_doc["modules"][0]["parameters"]["shape_a"])
            self.assertEqual(seconds, 2)
            self.assertEqual(events, [])
            return np.zeros((8, 2)), {"status": "measured"}

        with patch.object(run_all, "run_wav", side_effect=fake_wav), \
             patch.object(run_all, "oscillator_metrics",
                          return_value={"rms_fs": .1, "alias_floor_dbfs": -30}), \
             patch.object(run_all, "save") as saved:
            rows = run_all.oscillator_sections(
                "renderer-not-executed", {t7_0.MODULE: {"version": 2}},
                {"commit": "a" * 40}, None, False,
                t7_0.RATES, t7_chaos_only=True)
        self.assertEqual(len(rows), 24)
        self.assertEqual(rate_log.count(44100), 8)
        self.assertEqual(rate_log.count(48000), 8)
        self.assertEqual(rate_log.count(96000), 8)
        self.assertEqual(wave_log.count(0), 12)
        self.assertEqual(wave_log.count(1), 12)
        self.assertEqual(saved.call_count, 1)
        with self.assertRaisesRegex(ValueError, "requires rates"):
            run_all.oscillator_sections(
                "none", {}, {}, None, False,
                (48000,), t7_chaos_only=True)


class T70Switch(unittest.TestCase):
    def test_switch_parameter_routing_and_frames(self):
        catalogue = {}
        for module, param, *_ in t7_0.SWITCHES:
            catalogue.setdefault(module, {"parameters": {}})["parameters"][param] = {
                "min": -2, "max": 8}
        catalogue["essentials.quad_vca"]["parameters"]["mode1"] = {"min": 0, "max": 1}
        # Explicit kMode is a valid stepped parameter despite the source
        # parameter extractor not decoding that C++ constant alias.
        def fake_wav(renderer, patch_doc, events, seconds, *, rate):
            self.assertEqual(rate, 48000)
            self.assertEqual(events[0]["frame"], 48000)
            self.assertEqual(events[0]["type"], "setParam")
            self.assertEqual(seconds, 2)
            return np.zeros((8, 2)), {"status": "measured", "counters": {"faults": 0}}

        with patch.object(t7_0, "build_module_patch",
                          return_value=({"modules": [], "outputs": []}, None)), \
             patch.object(t7_0, "run_wav", side_effect=fake_wav) as calls, \
             patch.object(t7_0, "switch_click_metrics",
                          return_value={"switch_click_peak_fs": .3,
                                        "switch_click_peak_dbfs": -10.4575749056}):
            results = t7_0.capture_switches("unexecuted", catalogue)
        self.assertEqual(calls.call_count, 4)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(x["status"] == "measured" for x in results))
        self.assertEqual({x["parameter"] for x in results},
                         {"mode1", "mode", "division", "tone"})

    def test_native_descriptor_identity_cannot_be_mocked_into_availability(self):
        # Read the actual native C++ descriptor and on-disk module manifest.
        # A self-referential mocked catalogue once hid "ports.quad_vca".
        manifest = json.loads(
            (run_all.ROOT / "native/modules2/quad_vca/module.json").read_text(encoding="utf-8"))
        desc = run_all.descriptors()
        quad = next(switch for switch in t7_0.SWITCHES if switch[1] == "mode1")
        self.assertEqual(manifest["id"], "essentials.quad_vca")
        self.assertEqual(quad[0], manifest["id"])
        self.assertEqual(manifest["parameters"]["mode1"], 4)
        self.assertIn(manifest["id"], desc)
        self.assertIn("mode1", desc[manifest["id"]]["parameters"])
        bounds = desc[manifest["id"]]["parameters"]["mode1"]
        self.assertEqual((bounds["min"], bounds["max"]), (0, 1))
        t7_0.require_switch_descriptors(desc)

        routed = []
        def fake_wav(renderer, patch_doc, events, seconds, *, rate):
            module = patch_doc["modules"][0]["module"]
            routed.append(module)
            self.assertIn(module, desc)
            self.assertIn(events[0]["parameter"], desc[module]["parameters"])
            self.assertEqual((seconds, rate, events[0]["frame"]), (2, 48000, 48000))
            return np.zeros((8, 2)), {"status": "measured", "counters": {"faults": 0}}

        with patch.object(t7_0, "run_wav", side_effect=fake_wav), \
             patch.object(t7_0, "switch_click_metrics",
                          return_value={"switch_click_peak_fs": .3,
                                        "switch_click_peak_dbfs": -10.4575749056}):
            rows = t7_0.capture_switches("not-executed", desc)
        self.assertEqual(len(routed), 4)
        self.assertEqual(routed[0], manifest["id"])
        self.assertEqual(rows[0]["status"], "measured")
        self.assertEqual(rows[0]["module"], manifest["id"])

        absent = dict(desc)
        absent.pop(manifest["id"])
        with self.assertRaisesRegex(ValueError, "missing native switch descriptor"):
            t7_0.require_switch_descriptors(absent)
        misspelled = (("ports.quad_vca",) + quad[1:],) + t7_0.SWITCHES[1:]
        with patch.object(t7_0, "SWITCHES", misspelled):
            with self.assertRaisesRegex(ValueError, "missing native switch descriptor"):
                t7_0.require_switch_descriptors(desc)

    def test_switch_unavailable_when_descriptor_absent(self):
        with patch.object(t7_0, "run_wav") as unused:
            results = t7_0.capture_switches("unexecuted", {})
        self.assertTrue(all(x["status"] == "unavailable" for x in results))
        self.assertEqual(unused.call_count, 0)


if __name__ == "__main__":
    unittest.main()
