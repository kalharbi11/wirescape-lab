# SPDX-License-Identifier: GPL-3.0-only
"""MB2: executable descriptor/projection equality and A97 preservation (device-free).

The pre-removal MB1 manifest comparison is retained in the PR history.
"""
import argparse
import json
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
    def test_live_registry_matches_generated_projection(self):
        self.assertTrue(DESCRIBE.is_file(), f"wire-describe missing: {DESCRIBE.name}")
        result = subprocess.run([str(DESCRIBE.resolve())], check=True,
                                capture_output=True, text=True, encoding="utf-8",
                                timeout=30)
        rows = json.loads(result.stdout)["modules"]
        ids = [row["id"] for row in rows]
        self.assertEqual(ids, sorted(ids), "MB2 registry must be ordered by module ID")
        descriptors = index(rows)
        snapshot = read_json(ROOT / "tools/mb1/descriptor_inventory.json")
        projected = index(snapshot["modules"])
        fields = {"id", "name", "abi_version", "version", "inputs", "outputs", "parameters"}
        self.assertEqual(set(descriptors), set(projected))
        self.assertEqual(list(projected), sorted(projected))
        known = [line.strip() for line in
                 (ROOT / "tools/foundation/fixtures/known_module_ids.txt").read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.startswith("#")]
        self.assertEqual(known, ids)
        self.assertEqual(len(known), len(set(known)))
        membership = read_json(ROOT / "bench/module_sets.json")
        frozen = membership["golden_set"]
        experimental = membership["experimental"]
        self.assertEqual(len(frozen), 34)
        self.assertEqual(len(set(frozen)), len(frozen))
        self.assertEqual(len(set(experimental)), len(experimental))
        self.assertFalse(set(frozen) & set(experimental))
        self.assertEqual(set(descriptors), set(frozen) | set(experimental))
        for identity, row in projected.items():
            with self.subTest(module=identity):
                descriptor = descriptors[identity]
                self.assertEqual(set(row), fields, "unclassified generated projection field")
                self.assertEqual({field: descriptor[field] for field in fields}, row)
                self.assertIs(type(descriptor["version"]), int)
                self.assertGreaterEqual(descriptor["version"], 1)
                if identity == "essentials.output":
                    self.assertEqual(descriptor["parameters"], {})
                    self.assertEqual(descriptor["parameter_details"], [])

    def test_no_builtin_manifests(self):
        paths = sorted((ROOT / "modules").glob("*/module.json"))
        paths += sorted((ROOT / "sdk/examples").glob("*/module.json"))
        self.assertEqual(paths, [], "built-in descriptors must not have a second authored manifest")

    def test_a97_manifest_descriptions_survive(self):
        # Frozen pre-MB2 metadata, not an input to the registry or generator.
        descriptions = read_json(ROOT / "tools/mb1/manifest_descriptions.json")
        self.assertEqual(len(descriptions), 25)
        for folder, expected in descriptions.items():
            with self.subTest(folder=folder):
                lines = (ROOT / folder / "README.md").read_text(encoding="utf-8").splitlines()
                title = next(i for i, line in enumerate(lines) if line.startswith("# "))
                description = next(line for line in lines[title + 1:] if line.strip())
                self.assertEqual(description, expected)

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
