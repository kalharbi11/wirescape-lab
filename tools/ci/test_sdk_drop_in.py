# SPDX-License-Identifier: GPL-3.0-only
"""MB3 regression tests; all inputs are synthetic and device-free."""
import unittest
from sdk_drop_in import DROP_ID, verify_discovery

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

if __name__ == "__main__":
    unittest.main()
