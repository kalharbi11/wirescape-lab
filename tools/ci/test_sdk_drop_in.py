# SPDX-License-Identifier: GPL-3.0-only
"""MB3 regression tests; all inputs are synthetic and device-free."""
import tempfile
from pathlib import Path
import unittest
from sdk_drop_in import DROP_ID, remove_empty_configure_reports, verify_discovery

def descriptor():
    return {
        "id": DROP_ID, "name": "MB3 Scratch Gain", "abi_version": 2,
        "version": 1, "inputs": {"audio": "signal"},
        "outputs": {"audio": "signal"}, "parameters": {"gain": 0},
        "parameter_details": [{"id": "gain", "minimum": 0,
                               "maximum": 2, "default": 1}],
    }

class DiscoveryTests(unittest.TestCase):
    def test_missing_registration(self):
        with self.assertRaisesRegex(ValueError, "not discovered"):
            verify_discovery({"modules": []})

    def test_duplicate_registration(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify_discovery({"modules": [descriptor(), descriptor()]})

    def test_wrong_descriptor(self):
        row = descriptor()
        row["parameters"] = {}
        with self.assertRaisesRegex(ValueError, "parameters"):
            verify_discovery({"modules": [row]})

    def test_positive(self):
        self.assertEqual(verify_discovery({"modules": [descriptor()]}), descriptor())

class ConfigureReportsTests(unittest.TestCase):
    def test_empty_directories_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "build_reports/abi2").mkdir(parents=True)
            remove_empty_configure_reports(root)
            self.assertFalse((root / "build_reports").exists())
            remove_empty_configure_reports(root)

    def test_nonempty_directory_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "build_reports/abi2/unexpected.json"
            report.parent.mkdir(parents=True)
            report.write_text("unexpected", encoding="utf-8")
            with self.assertRaises(OSError):
                remove_empty_configure_reports(root)
            self.assertEqual(report.read_text(encoding="utf-8"), "unexpected")

if __name__ == "__main__":
    unittest.main()
