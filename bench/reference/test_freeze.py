#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer tests for the device-off ABI1 reference packer."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import freeze


class FreezeTests(unittest.TestCase):
    def test_source_case_tag_inventory(self):
        self.assertEqual(freeze.file_kind("shim_steady"), ("shim", "shim"))
        self.assertEqual(freeze.file_kind("module_vco_44100_17"), ("module", "vco"))
        self.assertEqual(freeze.file_kind("utility_noise_96000_16_256_3"),
                         ("utility", "noise_96000"))
        with self.assertRaises(ValueError):
            freeze.file_kind("module_unknown_44100_17")
        with self.assertRaises(ValueError):
            freeze.file_kind("utility_vco_48000_1_1_1")
        cases = {"shim_steady", "shim_scripted"}
        cases.update("module_%s_%d_%d" % (n, rate, block)
                     for n in freeze.MODULES
                     for rate in freeze.RATES for block in freeze.BLOCKS)
        cases.update("utility_%s_%d_%d_%d_%d" % (n, rate, ch, block, pattern)
                     for n in freeze.UTILITIES for rate in freeze.RATES
                     for ch in freeze.CHANNELS for block in freeze.BLOCKS
                     for pattern in freeze.PATTERNS)
        self.assertEqual(freeze.verify_inventory(cases), 983)
        with self.assertRaisesRegex(ValueError, "missing"):
            freeze.verify_inventory(cases - {"shim_steady"})
        with self.assertRaisesRegex(ValueError, "unexpected"):
            freeze.verify_inventory(cases | {"module_fake_48000_1"})

    def test_refuses_missing_or_misaligned_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dest = Path(tmp) / "samples", Path(tmp) / "out"
            src.mkdir()
            (src / "shim_steady.f32le").write_bytes(b"\\x00\\x01\\x02")
            metadata = {"machine": "synthetic"}
            with self.assertRaisesRegex(ValueError, "invalid binary32"):
                freeze.package(src, dest, metadata)
            (src / "shim_steady.f32le").write_bytes(b"\\x00" * (16384 * 4))
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                freeze.package(src, dest, metadata)
            self.assertFalse(dest.exists())

    def test_crc_not_substituted_for_cryptographic_source_digest(self):
        samples = b"\\x00\\x00\\x80\\x3f"  # binary32 1.0 in LE
        digest = hashlib.sha256(samples).hexdigest()
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest,
                         "e00e5eb9444182f352323374ef4e08c9718feaa96ee1b6cdbe4bf40bd6eea6a5")


if __name__ == "__main__":
    unittest.main()
