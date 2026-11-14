# SPDX-License-Identifier: GPL-3.0-only
"""Pure arithmetic tests for native float32 catalogue parameter boundaries."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import quantize


def native_float(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


class NativeParameterBoundTests(unittest.TestCase):
    def test_rounding_never_drops_below_reverb_minimum(self):
        lo = native_float(.2)
        hi = native_float(12.)
        self.assertGreater(lo, .2)
        self.assertEqual(quantize(lo, lo, hi, 0), lo)
        self.assertGreaterEqual(quantize(lo, lo, hi, 0), lo)

    def test_rounding_never_raises_above_native_maximum(self):
        lo = native_float(0.)
        hi = native_float(.7)
        self.assertLess(hi, .7)
        self.assertEqual(quantize(hi, lo, hi, 0), hi)
        self.assertLessEqual(quantize(hi, lo, hi, 0), hi)

    def test_step_quantization_remains_within_float32_limits(self):
        lo, hi = native_float(.2), native_float(.7)
        step = native_float(.05)
        for fraction in (0., .01, .25, .5, .75, .99, 1.):
            value = quantize(lo + (hi - lo) * fraction, lo, hi, step)
            self.assertLessEqual(value, hi)
            self.assertGreaterEqual(value, lo)


if __name__ == "__main__":
    unittest.main()
