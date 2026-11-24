# SPDX-License-Identifier: GPL-3.0-only
"""Portability probe parsing tests; no toolchain or hardware needed."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from probe import first_error, section_sizes, sources, symbol_flags


class ProbeTests(unittest.TestCase):
    def test_source_inventory_covers_catalog_and_sdk(self):
        files, count = sources()
        from bench.golden.inventory import EXPERIMENTAL, allowed_ids, golden_ids
        self.assertEqual(count, len(allowed_ids()))
        self.assertEqual(len(golden_ids()), 34)
        self.assertEqual(EXPERIMENTAL, {"essentials.cv_to_notes"})
        self.assertEqual(len(files), 36)
        self.assertTrue(any(str(p).endswith("sdk/template/module.cpp") for p in files))
        self.assertEqual(sum("sdk/examples/" in p.as_posix() for p in files), 2)

    def test_section_size_classification(self):
        output = ("obj.o :\nsection size addr\n"
                  ".text 10 0\n.text.foo 25 0\n.rodata 7 0\n"
                  ".data 3 0\n.data.bar 4 0\n.bss 2 0\n.sbss.blah 6 0\n")
        self.assertEqual(section_sizes(output),
                         {"text_bytes": 35, "data_bytes": 7, "bss_bytes": 8})

    def test_symbol_detection(self):
        flags = symbol_flags(["__aeabi_dadd", "__aeabi_fdiv", "pow", "sinf",
                              "malloc", "_Znwm", "__cxa_guard_acquire", "foo"])
        self.assertEqual(flags["double_or_softfloat_symbols"],
                         ["__aeabi_dadd", "__aeabi_fdiv", "pow"])
        self.assertEqual(flags["float_libm_symbols"], ["sinf"])
        self.assertEqual(flags["heap_symbols"], ["_Znwm", "malloc"])
        self.assertEqual(flags["static_guard_symbols"], ["__cxa_guard_acquire"])

    def test_first_error_normalized(self):
        got = first_error("note: informational\nnative/module.cpp:9: error: bad conversion\n")
        self.assertEqual(got, "native/module.cpp:9: error: bad conversion")


if __name__ == "__main__":
    unittest.main()
