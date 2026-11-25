# SPDX-License-Identifier: GPL-3.0-only
from collections import Counter
from pathlib import Path
from unittest.mock import Mock
import tempfile
import unittest

from keyboard_attribution import compare, exclusive


class AttributionTests(unittest.TestCase):
    def test_excludes_call_arcs_and_combines_repeated_functions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "profile"
            profile = ("part: 1\npositions: line\nevents: Ir\nsummary: 19\n"
                       f"ob={root}/probe\nfl={root}/dsp.h\nfn=render\n"
                       "0 3\ncfn=helper\ncalls=1 0\n0 10\n0 4\n"
                       "fn=helper\n0 10\nfn=render\n0 2\n")
            path.write_text(profile, encoding="utf-8")
            result = exclusive(path, root)
            self.assertEqual(result[("<source>/probe", "<source>/dsp.h", "render")], 9)
            self.assertEqual(sum(result.values()), 19)
            path.write_text(profile.replace("summary: 19", "summary: 29"), encoding="utf-8")
            with self.assertRaises(ValueError):
                exclusive(path, root)

    def test_native_and_posix_absolute_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path = root / "profile"
            for prefix in (root.as_posix(), str(root), root.as_posix().replace("/", "\\")):
                with self.subTest(prefix=prefix):
                    path.write_text("part: 1\npositions: line\nevents: Ir\nsummary: 7\n"
                                    f"ob={prefix}/probe\nfl={prefix}/engine/../sdk/a.h\n"
                                    "fn=render\n0 7\n", encoding="utf-8")
                    self.assertEqual(exclusive(path, root), Counter({
                        ("<source>/probe", "<source>/sdk/a.h", "render"): 7}))

    def test_lexical_root_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "profile"
            lexical = Path(temp) / "alias"
            canonical = Path(temp) / "canonical"
            root = Mock()
            root.absolute.return_value = lexical
            root.resolve.return_value = canonical
            root.name = lexical.name
            path.write_text("part: 1\npositions: line\nevents: Ir\nsummary: 7\n"
                            f"ob={lexical}/probe\nfl={canonical}/dsp.h\n"
                            "fn=render\n0 7\n", encoding="utf-8")
            self.assertEqual(exclusive(path, root), Counter({
                ("<source>/probe", "<source>/dsp.h", "render"): 7}))

    def test_literal_parentheses_and_inline_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "base"
            root.mkdir()
            path = root / "profile"
            path.write_text("part: 1\npositions: line\nevents: Ir\nsummary: 7\n"
                            "ob=base/probe\nfl=base/engine/../sdk/a.h\n"
                            "fn=(anonymous namespace)::render()\n0 3\n"
                            "fi=base/modules/dsp.h\n0 4\n",
                            encoding="utf-8")
            result = exclusive(path, root)
            self.assertEqual(result[("<source>/probe", "<source>/sdk/a.h",
                                     "(anonymous namespace)::render()")], 3)
            self.assertEqual(result[("<source>/probe", "<source>/modules/dsp.h",
                                     "(anonymous namespace)::render()")], 4)
            path.write_text(path.read_text().replace(
                "(anonymous namespace)::render()", "(12)"), encoding="utf-8")
            with self.assertRaises(ValueError):
                exclusive(path, root)

    def test_two_length_difference_and_missing_symbol(self):
        key = ("obj", "file", "render")
        new = ("obj", "file", "new")
        rows = compare(Counter({key: 100}), Counter({key: 220}),
                       Counter({key: 110, new: 12}), Counter({key: 254, new: 48}))
        self.assertEqual(rows[0]["function"], "new")
        self.assertEqual(rows[0]["delta_ir_per_block"], 3)
        self.assertEqual(rows[1]["delta_ir_per_block"], 2)


if __name__ == "__main__":
    unittest.main()
