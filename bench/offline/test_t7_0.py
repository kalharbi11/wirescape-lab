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
        catalogue["fx.delay"]["parameters"]["time"] = {"min": .001, "max": 2, "initial": .375}
        # Explicit kMode is a valid stepped parameter despite the source
        # parameter extractor not decoding that C++ constant alias.
        def fake_wav(renderer, patch_doc, events, seconds, *, rate):
            self.assertEqual(rate, 48000)
            if events:
                self.assertEqual(events[0]["frame"], 48000)
                self.assertEqual(events[0]["type"], "setParam")
            else:
                self.assertEqual(events, [])
            self.assertEqual(seconds, 2)
            audio = np.zeros((48002, 2))
            if events:
                audio[48000] = .5
            return audio, {"status": "measured", "counters": {"faults": 0}}

        with patch.object(t7_0, "build_module_patch",
                          return_value=({"modules": [{"parameters": {}}], "outputs": []}, None)), \
             patch.object(t7_0, "run_wav", side_effect=fake_wav) as calls, \
             patch.object(t7_0, "switch_click_metrics",
                          return_value={"status": "measured",
                                        "switch_click_peak_fs": .3,
                                        "switch_click_peak_dbfs": -10.4575749056}):
            results = t7_0.capture_switches("unexecuted", catalogue)
        self.assertEqual(calls.call_count, 8)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(x["status"] == "measured" for x in results))
        self.assertEqual({x["parameter"] for x in results},
                         {"mode1", "mode", "division", "tone"})

    def test_native_descriptor_identity_cannot_be_mocked_into_availability(self):
        # Read the actual native C++ descriptor and on-disk module manifest.
        # A self-referential mocked catalogue once hid "ports.quad_vca".
        manifest = json.loads(
            (run_all.ROOT / "modules/quad_vca/module.json").read_text(encoding="utf-8"))
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
            if events:
                self.assertIn(events[0]["parameter"], desc[module]["parameters"])
                self.assertEqual((seconds, rate, events[0]["frame"]), (2, 48000, 48000))
            else:
                self.assertEqual((seconds, rate), (2, 48000))
            audio = np.zeros((48002, 2))
            if events:
                audio[48000] = .5
            return audio, {"status": "measured", "counters": {"faults": 0}}

        with patch.object(t7_0, "run_wav", side_effect=fake_wav), \
             patch.object(t7_0, "switch_click_metrics",
                          return_value={"status": "measured",
                                        "switch_click_peak_fs": .3,
                                        "switch_click_peak_dbfs": -10.4575749056}):
            rows = t7_0.capture_switches("not-executed", desc)
        self.assertEqual(len(routed), 8)
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

    def test_no_effect_is_not_zero_and_legacy_projection_is_explicit(self):
        control = np.zeros((96000, 2))
        identity = dict(module="fx.delay", parameter="division", before=5, after=6,
                        sample_rate_hz=48000, switch_frame=48000,
                        delay_default_time_s=.375)
        with patch.object(t7_0, "run_wav",
                          return_value=(control, {"status": "measured", "counters": {}})) as wav:
            actual = t7_0.measure_switch_pair(
                "not-executed", {"modules": [{"parameters": {}}]}, identity)
        self.assertEqual(wav.call_count, 2)
        self.assertEqual(wav.call_args_list[0].args[2][0]["type"], "setParam")
        self.assertEqual(wav.call_args_list[1].args[2], [])
        self.assertEqual(actual["status"], "no_effect")
        self.assertIsNone(actual["first_effect_frame"])
        self.assertIsNone(actual["click_excess_db"])
        legacy = t7_0.legacy_switch_rows([actual])
        self.assertEqual(legacy[0]["status"], "unavailable")
        self.assertIn("no_effect", legacy[0]["reason"])
        self.assertIsNone(legacy[0]["click_excess_db"])

    def test_late_mode_effect_and_second_clocked_division_fixture(self):
        rate, frame, first = 48000, 48000, 84001
        control = np.zeros((rate * 2, 2))
        changed = control.copy()
        changed[first] = .4
        identity = dict(module="fx.delay", parameter="mode", before=0, after=1,
                        sample_rate_hz=rate, switch_frame=frame,
                        delay_default_time_s=.375)
        with patch.object(t7_0, "run_wav",
                          side_effect=lambda renderer, doc, events, seconds, *, rate:
                             ((changed if events else control),
                              {"status": "measured", "counters": {}})):
            row = t7_0.measure_switch_pair(
                "none", {"modules": [{"parameters": {}}]}, identity)
        self.assertEqual(row["status"], "measured")
        self.assertEqual(row["first_effect_frame"], first)
        self.assertEqual(row["window_end_frame_exclusive"], first + 1200)
        self.assertGreater(row["switch_click_peak_fs"], 0)

        desc = run_all.descriptors()
        observed = []
        def fake_wav(renderer, patch_doc, events, seconds, *, rate):
            observed.append((copy.deepcopy(patch_doc), list(events)))
            samples = np.zeros((rate * seconds, 2))
            if events:
                samples[rate + 3000] = .3
            return samples, {"status": "measured", "counters": {}}
        with patch.object(t7_0, "run_wav", side_effect=fake_wav):
            clocked = t7_0.capture_clocked_division("not-executed", desc)
        self.assertEqual(clocked["status"], "measured")
        self.assertEqual(clocked["fixture"], "clocked")
        self.assertEqual(len(observed), 2)
        self.assertEqual(observed[0][0], observed[1][0])
        self.assertEqual(observed[1][1], [])
        node = clocked["clock_source_node"]
        self.assertTrue(any(m["id"] == node and m["module"] == "essentials.clock"
                            for m in observed[0][0]["modules"]))
        self.assertIn({"kind": "signal",
                       "from": {"module": node, "port": "clock"},
                       "to": {"module": 1, "port": "clock"}},
                      observed[0][0]["connections"])

    def test_switch_unavailable_when_descriptor_absent(self):
        with patch.object(t7_0, "run_wav") as unused:
            results = t7_0.capture_switches("unexecuted", {})
        self.assertTrue(all(x["status"] == "unavailable" for x in results))
        self.assertEqual(unused.call_count, 0)


class OfflineInventory(unittest.TestCase):
    def test_mb1_preserves_exact_pre_expansion_workload(self):
        # A103: frozen diagnostic workload, including order, at MB1 base.
        expected = [
            "essentials.adsr",
            "essentials.chaos_lite",
            "essentials.chord",
            "essentials.clock",
            "essentials.function_envelope",
            "essentials.ladder",
            "essentials.lfo",
            "essentials.mixer",
            "essentials.noise",
            "essentials.notes_to_cv",
            "essentials.output",
            "essentials.quad_vca",
            "essentials.quantizer",
            "essentials.resonator",
            "essentials.scale_offset",
            "essentials.slew",
            "essentials.vca",
            "essentials.vcf",
            "essentials.vco",
            "example.random_source",
            "example.step_sequencer",
            "fx.delay",
            "fx.reverb",
            "host.keyboard",
            "midi.cc_to_cv",
            "midi.in",
            "midi.to_cv",
            "monitor",
            "osc.in",
            "ports.macro_oscillator",
            "sequencing.groove",
            "sound.blend",
            "sound.spectral",
        ]
        self.assertEqual(run_all.modules(), expected)
        # The generated registry fixture must not be the offline workload.
        known = (run_all.ROOT / "tools/foundation/fixtures/known_module_ids.txt").read_text(encoding="utf-8")
        self.assertIn("osc.out", known.splitlines())
        self.assertNotIn("osc.out", run_all.modules())


if __name__ == "__main__":
    unittest.main()
