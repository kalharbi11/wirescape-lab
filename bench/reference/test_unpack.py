#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer integrity tests for the frozen ABI1 reference loader."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from unpack import decode_case, unpack


def encode(body):
    return {
        "samples": len(body) // 4,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "codec": "zlib9+b64",
        "compressed_b64": base64.b64encode(zlib.compress(body, 9)).decode(),
    }


class UnpackTests(unittest.TestCase):
    def test_known_binary32_sample_bits(self):
        data = struct.pack("<f", 1.0) + struct.pack("<f", -0.0)
        self.assertEqual(decode_case("module_vco_48000_17", encode(data)), data)
        self.assertEqual(data.hex(), "0000803f00000080")

    def test_rejects_hash_length_or_codec_mutation(self):
        body = struct.pack("<f", 1.0)
        good = encode(body)
        for value in (
            dict(good, sha256="0" * 64),
            dict(good, samples=3),
            dict(good, bytes=8),
            dict(good, codec="gzip+b64"),
            dict(good, compressed_b64="AA=="),
            dict(good, compressed_b64="*invalid*"),
        ):
            with self.subTest(value=value):
                with self.assertRaises((ValueError, zlib.error)):
                    decode_case("shim_steady", value)

    def test_rejects_incomplete_and_cross_platform_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            filename = root / "abi1_linux-x64_shim_shim.json"
            payload = {
                "schema": "abi1-reference-candidate-v1",
                "metadata": {"source_commit": "a" * 40, "machine": "linux-x64"},
                "suite": "shim", "group": "shim", "case_count": 1,
                "cases": {"shim_steady": encode(struct.pack("<f", 0.25))},
            }
            filename.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "wrong-platform"):
                unpack([filename], root / "out", "linux-arm64")
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                unpack([filename], root / "out", "linux-x64")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
