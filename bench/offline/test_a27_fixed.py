# SPDX-License-Identifier: GPL-3.0-only
import unittest

import numpy as np
from scipy import signal

from a27_fixed import WINDOWS, measure_pair, require_pin, validate_reports


class FixedWindowTests(unittest.TestCase):
    def test_windows_are_fixed_and_half_open(self):
        self.assertEqual(WINDOWS, {"mode": (48000, 85201),
                                   "tone": (48000, 67200),
                                   "division_clocked": (48000, 49200)})
        for name, (begin, end) in WINDOWS.items():
            control = np.zeros((96000, 2), dtype=np.float64)
            control[:, :] = (0.1 * np.sin(2 * np.pi * 440 *
                                         np.arange(96000) / 48000))[:, None]
            switched = control.copy()
            switched[begin + 9] += .25
            switched[end] += 10
            row = measure_pair(name, switched, control)
            sos = signal.butter(2, 2000, btype="highpass", fs=48000, output="sos")
            # Independent full causal filter, not a filter reset at window start.
            peak = lambda x: float(np.max(np.abs(
                signal.sosfilt(sos, x[:, 0])[begin:end])))
            self.assertEqual(row["status"], "measured")
            self.assertEqual(row["window_start_frame"], begin)
            self.assertEqual(row["window_end_frame_exclusive"], end)
            self.assertEqual(row["switch_click_peak_fs"], peak(switched))
            self.assertEqual(row["no_switch_floor_fs"], peak(control))
            self.assertAlmostEqual(row["click_excess_db"],
                                   20 * np.log10(peak(switched) / peak(control)))
            changed = switched.copy()
            changed[end:] = 0
            self.assertEqual(measure_pair(name, changed, control)["switch_click_peak_fs"],
                             row["switch_click_peak_fs"])

    def test_r19_classification_uses_old_floor_before_target_validity(self):
        from a27_fixed import classify_r19
        row = classify_r19(.01, .02, .009, .01)
        self.assertEqual(row["classification"], "old_floor_met")
        self.assertEqual(row["governing_floor"], .01)
        self.assertFalse(row["target_steady_state"])
        row = classify_r19(.01, .02, .0201, .01999)
        self.assertEqual(row["classification"], "steady_target_met")
        self.assertEqual(row["governing_floor"], .02)
        self.assertTrue(row["target_steady_state"])
        row = classify_r19(.01, .02, .0201, .01)
        self.assertEqual(row["classification"], "target_not_steady_old_floor_exceeded")
        self.assertEqual(row["governing_floor"], .01)
        row = classify_r19(.01, .02, .021, .02001)
        self.assertEqual(row["classification"], "steady_target_exceeded")
        self.assertEqual(classify_r19(.01, .02, .019, .03)["classification"],
                         "target_not_steady_old_floor_exceeded")
        self.assertEqual(classify_r19(.01, .02, .01 * 10**(.1/20), 0)["classification"],
                         "old_floor_met")
        self.assertEqual(classify_r19(0, 0, 0, 0)["classification"], "old_floor_met")
        for invalid in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                classify_r19(.01, .02, .021, invalid)

    def test_endpoint_floor_uses_larger_control_and_signed_excess(self):
        from a27_fixed import endpoint_columns
        for old, target, switched, expected in ((.01, .02, .02, 0),
                                               (.02, .01, .01, -6.020599913279624),
                                               (.01, .02, .021, .42378598139876184)):
            row = endpoint_columns(old, target, switched)
            self.assertEqual(row["old_floor"], old)
            self.assertEqual(row["target_floor"], target)
            self.assertEqual(row["endpoint_floor"], max(old, target))
            self.assertEqual(row["switched"], switched)
            self.assertAlmostEqual(row["excess_over_endpoint_db"], expected)
        self.assertEqual(endpoint_columns(0, 0, 0)["excess_over_endpoint_db"], 0)
        self.assertEqual(endpoint_columns(0, 0, .01)["excess_over_endpoint_db"], "inf")
        self.assertEqual(endpoint_columns(.01, 0, 0)["excess_over_endpoint_db"], "-inf")
        for invalid in (-1, None, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                endpoint_columns(.01, invalid, .01)

    def test_target_patch_preserves_clock_and_every_other_parameter(self):
        import copy
        from a27_fixed import target_patch
        patch = {"modules": [{"id": 1, "module": "fx.delay", "parameters": {"division": 5, "mix": 1}},
                             {"id": 4, "module": "essentials.clock", "parameters": {"bpm": 120}}],
                 "connections": [{"from": {"module": 4, "port": "clock"},
                                  "to": {"module": 1, "port": "clock"}}],
                 "settings": {"seed": 7}}
        original = copy.deepcopy(patch)
        expected = copy.deepcopy(patch)
        expected["modules"][0]["parameters"]["division"] = 1
        self.assertEqual(target_patch(patch, "division", 5, 1), expected)
        self.assertEqual(patch, original)
        with self.assertRaises(ValueError):
            target_patch(patch, "division", 4, 1)

    def test_unclocked_requires_full_pair_equality(self):
        a = np.zeros((96000, 2))
        self.assertEqual(measure_pair("division_unclocked", a, a)["status"], "no_effect")
        self.assertIsNone(measure_pair("division_unclocked", a, a)["click_excess_db"])
        b = a.copy()
        b[-1, 1] = .25
        self.assertEqual(measure_pair("division_unclocked", b, a)["status"], "unexpected_effect")

    def test_bad_pcm_is_explicit(self):
        a = np.zeros((96000, 2))
        b = a.copy()
        b[0] = .1
        self.assertEqual(measure_pair("mode", b, a)["status"], "unavailable")
        self.assertEqual(measure_pair("mode", a[:-1], a)["status"], "unavailable")
        b = a.copy()
        b[-1] = np.nan
        self.assertEqual(measure_pair("mode", b, a)["status"], "unavailable")

    def test_pin_validation(self):
        base, subject = "a" * 40, "b" * 40
        self.assertEqual(require_pin(base), base)
        for bad in ("", "main", "a" * 39, "a" * 41, "A" * 40, "a" * 39 + ";"):
            with self.assertRaises(ValueError):
                require_pin(bad)
        with self.assertRaises(ValueError):
            validate_reports({"source_commit": subject}, {"source_commit": subject},
                             base, subject)
        with self.assertRaises(ValueError):
            validate_reports({"source_commit": base}, {}, base, subject)
        with self.assertRaises(ValueError):
            validate_reports({"source_commit": base}, {"source_commit": subject},
                             base, subject)  # Missing row inventory.


if __name__ == "__main__":
    unittest.main()
