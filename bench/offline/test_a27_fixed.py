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
