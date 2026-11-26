# SPDX-License-Identifier: GPL-3.0-only
"""MB1: executable descriptor identity/legacy-index witness (device-free).

A97 classifies non-descriptor manifest metadata separately.
"""
import argparse
import json
import re
import sys
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
        locations = {read_json(path)['id']: path for path in paths}
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
                self.assertFalse(set(manifest) - {"id", "name", "abi_version", "inputs",
                                                      "outputs", "parameters", "schema_version",
                                                      "library", "license", "description"},
                                 "unclassified manifest field; escalate under L1")
                path = locations[identity]
                # SDK examples use the existing ws2_example_<folder> CMake targets.
                prefix = "ws2_example_" if path.parent.parent.name == "examples" else "ws2_"
                self.assertEqual(manifest["library"], prefix + path.parent.name)
                self.assertEqual(manifest["schema_version"], 2)
                if "license" in manifest:
                    source = path.with_name("module.cpp").read_text(encoding="utf-8")
                    spdx = re.search(r"(?m)^// SPDX-License-Identifier: (.+)$", source)
                    self.assertIsNotNone(spdx, str(path))
                    self.assertEqual(manifest["license"], spdx[1].strip())
                if "description" in manifest:
                    self.assertIsInstance(manifest["description"], str)
                self.assertIs(type(descriptor["version"]), int)
                self.assertGreaterEqual(descriptor["version"], 1)

    def test_live_generator_matches_committed_outputs(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/gen_ui_catalogue.py"),
                                 "--check", "--describe", str(DESCRIBE.resolve())],
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--describe", type=Path,
                        default=ROOT / "build/native/wire-describe")
    args = parser.parse_args()
    DESCRIBE = args.describe
    unittest.main(argv=[__file__])
