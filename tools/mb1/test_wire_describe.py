# SPDX-License-Identifier: GPL-3.0-only
"""MB1: executable descriptor identity/legacy-index witness (device-free).

This is the descriptor-backed subset of L1, not a waiver for manifest metadata.
The full metadata equality policy awaits the B4-MB1-L1 ruling.
"""
import argparse
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def index(rows):
    result = {}
    for row in rows:
        identity = row["id"]
        if identity in result:
            raise AssertionError(f"duplicate module ID: {identity}")
        result[identity] = row
    return result


class DescriptorEquality(unittest.TestCase):
    def test_live_registry_matches_manifest_identity(self):
        self.assertTrue(DESCRIBE.is_file(), f"wire-describe missing: {DESCRIBE.name}")
        result = subprocess.run([str(DESCRIBE.resolve())], check=True,
                                capture_output=True, text=True, encoding="utf-8",
                                timeout=30)
        descriptors = index(json.loads(result.stdout)["modules"])
        paths = sorted((ROOT / "modules").glob("*/module.json"))
        paths += sorted((ROOT / "sdk/examples").glob("*/module.json"))
        manifests = index([read_json(path) for path in paths])
        self.assertEqual(set(descriptors), set(manifests))
        membership = read_json(ROOT / "bench/module_sets.json")
        frozen = membership["golden_set"]
        experimental = membership["experimental"]
        self.assertEqual(len(frozen), 34)
        self.assertEqual(len(set(frozen)), len(frozen))
        self.assertEqual(len(set(experimental)), len(experimental))
        self.assertFalse(set(frozen) & set(experimental))
        self.assertEqual(set(descriptors), set(frozen) | set(experimental))
        for identity, manifest in manifests.items():
            with self.subTest(module=identity):
                descriptor = descriptors[identity]
                for field in ("id", "name", "abi_version", "inputs", "outputs", "parameters"):
                    self.assertEqual(descriptor[field], manifest[field], field)
                self.assertIs(type(descriptor["version"]), int)
                self.assertGreaterEqual(descriptor["version"], 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--describe", type=Path,
                        default=ROOT / "build/native/wire-describe")
    args = parser.parse_args()
    DESCRIBE = args.describe
    unittest.main(argv=[__file__])
