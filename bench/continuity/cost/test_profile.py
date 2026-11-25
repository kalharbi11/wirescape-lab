# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic parser fixtures only; never report their numbers as measured Ir."""
import unittest
from profile_blocks import parse_dump, summarize


def dump(block, ir, adopt=False, housekeeping=False):
    label = f"block-{block}"
    extra = ("cfn=(7) wirescape::engine2::Engine::Impl::adopt_layout(Layout*)\n"
             "calls=1 20\n10 4\n") if adopt or housekeeping else ""
    return (f"version: 1\ndesc: Trigger: Client Request: {label}\n"
            f"events: Ir\nsummary: {ir}\nfn=(1) render\n"
            f"10 {ir-4 if extra else ir}\n{extra}totals: {ir}\n")


class ProfileTest(unittest.TestCase):
    def test_block_identity_and_ir(self):
        self.assertEqual(parse_dump(dump(42, 123456)), {"block": 42, "ir": 123456, "adopt_calls": 0})
        self.assertEqual(parse_dump(dump(43, 234567, True)),
                         {"block": 43, "ir": 234567, "adopt_calls": 1})

    def test_reject_non_block_or_wrong_event(self):
        for text in (dump(42, 1).replace("block-42", "Program termination"),
                     dump(42, 1).replace("events: Ir", "events: Ir Dr"),
                     dump(42, 1).replace("summary: 1", "summary: 0"),
                     dump(42, 2).replace("totals: 2", "totals: 1")):
            with self.assertRaises(ValueError):
                parse_dump(text)

    def test_symbol_reference(self):
        text = dump(42, 100, True).replace("fn=(1) render",
            "fn=(7) wirescape::engine2::Engine::Impl::adopt_layout(Layout*)\n20 2\nfn=(1) render").replace(
            "cfn=(7) wirescape::engine2::Engine::Impl::adopt_layout(Layout*)", "cfn=(7)")
        self.assertEqual(parse_dump(text)["adopt_calls"], 1)

    def test_steady_and_transition(self):
        # 20 ms at 48k/256 spans four render calls; housekeeping is later.
        rows = [parse_dump(dump(i, v, i == 3, i == 7))
                for i, v in enumerate([100, 101, 102, 200, 300, 210, 180, 110, 105, 104])]
        steady = summarize([parse_dump(dump(i, v)) for i, v in enumerate([10, 12, 11])],
                           "single", 0)
        self.assertEqual(steady["max_block_ir"], 12)
        dual = summarize(rows, "dual", 960, request_block=2)
        self.assertEqual(dual["adoption_block"], 3)
        self.assertEqual(dual["adoption_block_ir"], 200)
        self.assertEqual(dual["max_dual_instance_block_ir"], 300)
        self.assertEqual(dual["housekeeping_block"], 7)
        self.assertEqual(dual["request_block"], 2)
        self.assertEqual(dual["housekeeping_block_ir"], 110)
        self.assertEqual(dual["max_audible_fade_block_ir"], 300)
        for request in (None, 1, 4, 99):
            with self.assertRaises(ValueError):
                summarize(rows, "dual", 960, request_block=request)
        with self.assertRaises(ValueError):
            summarize(rows[:-1], "dual", 960, request_block=2)
        self.assertEqual([r["block"] for r in dual["window"]], list(range(0, 10)))

    def test_missing_duplicate_and_unsettled_rejected(self):
        rows = [parse_dump(dump(i, 10, i == 3, i == 7)) for i in range(10)]
        for bad in (rows[:3] + rows[4:], rows + [rows[2]], rows[:7], 
                    [dict(row, adopt_calls=0) for row in rows]):
            with self.assertRaises(ValueError):
                summarize(bad, "dual", 960, request_block=2)


if __name__ == "__main__":
    unittest.main()
