# SPDX-License-Identifier: GPL-3.0-only
import unittest
from bench.portability.s2 import relocations, object_size, is_double_or_softfloat


class S2Tests(unittest.TestCase):
    def test_relocations_keep_section_and_offset(self):
        source = """RELOCATION RECORDS FOR [.text.foo]:
OFFSET   TYPE              VALUE
00000012 R_ARM_THM_CALL    __aeabi_ddiv
00000024 R_ARM_THM_CALL    __aeabi_ddiv
00000028 R_ARM_THM_CALL    sinf
RELOCATION RECORDS FOR [.text.bar]:
OFFSET   TYPE              VALUE
00000004 R_ARM_THM_CALL    __aeabi_i2d
"""
        self.assertEqual(relocations(source, {"__aeabi_ddiv", "__aeabi_i2d"}), {
            "__aeabi_ddiv": [".text.foo+0x12", ".text.foo+0x24"],
            "__aeabi_i2d": [".text.bar+0x4"],
        })

    def test_size_is_unambiguous(self):
        self.assertEqual(object_size("00000000 00000128 B ws_s2_dsp_size\n"), 128)
        with self.assertRaises(ValueError):
            object_size("00000000 00000032 B other\n")
        with self.assertRaises(ValueError):
            object_size("00000000 00000128 B ws_s2_dsp_size\n" * 2)

    def test_double_conversion_and_math(self):
        for name in ("__aeabi_ddiv", "__aeabi_i2d", "__aeabi_ui2f",
                     "__aeabi_f2d", "sqrt", "pow", "ceil"):
            self.assertTrue(is_double_or_softfloat(name), name)
        for name in ("sinf", "memcpy", "__aeabi_memcpy", "__aeabi_uidiv"):
            self.assertFalse(is_double_or_softfloat(name), name)
