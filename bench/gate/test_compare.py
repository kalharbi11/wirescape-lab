# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic, device-free instruction regression gate tests."""
import unittest

from compare import compare, expected_ids, indexed, render


def facts(rows, machine="linux-x64"):
    return {"schema": 1, "machine": machine,
            "method": "callgrind-Ir-two-length-difference-v1",
            "rows": [{"id": key, "status": status, "ir_per_block": count}
                     for key, status, count in rows]}


class CompareTests(unittest.TestCase):
    def test_unchanged_and_improvement_pass(self):
        before = facts([("a", "measured", 100), ("b", "measured", 200)])
        after = facts([("a", "measured", 100), ("b", "measured", 190)])
        changes, errors = compare(before, after)
        self.assertEqual(errors, [])
        self.assertEqual([r["id"] for r in changes], ["b", "a"])

    def test_threshold_3_percent_is_strictly_greater(self):
        before = facts([("a", "measured", 100)])
        at = facts([("a", "measured", 103)])
        above = facts([("a", "measured", 104)])
        self.assertEqual(compare(before, at)[1], [])
        errors = compare(before, above)[1]
        self.assertEqual(len(errors), 1)
        self.assertIn("+4.00%", errors[0])

    def test_missing_or_failed_measured_rows_fail_closed(self):
        before = facts([("a", "measured", 100), ("b", "measured", 200)])
        after = facts([("a", "unavailable", None), ("c", "measured", 2)])
        self.assertEqual(len(compare(before, after)[1]), 3)

    def test_previously_unavailable_never_passes_as_measured(self):
        before = facts([("a", "unavailable", None), ("b", "unavailable", None)])
        after = facts([("a", "unavailable", None), ("b", "measured", 100)])
        changes, errors = compare(before, after)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("a: baseline unavailable" in item for item in errors))
        self.assertTrue(any("a: current unavailable" in item for item in errors))
        self.assertTrue(any("b: baseline unavailable" in item for item in errors))
        self.assertEqual({r["status"] for r in changes},
                         {"unavailable", "newly_measured"})

    def test_failed_baseline_and_current_are_not_false_green(self):
        before = facts([("a", "failed", None)])
        current = facts([("a", "failed", None)])
        changes, errors = compare(before, current)
        self.assertEqual(changes[0]["status"], "unavailable")
        self.assertEqual(len(errors), 2)

    def test_same_missing_row_cannot_be_silent(self):
        before = facts([("a", "unavailable", None)])
        current = facts([("a", "unavailable", None)])
        self.assertTrue(compare(before, current)[1])

    def test_rejects_nonpositive_and_nonfinite(self):
        b = facts([("a", "measured", 100)])
        for invalid in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid):
                self.assertEqual(len(compare(b, facts([("a", "measured", invalid)]))[1]), 1)

    def test_architecture_and_method_mismatch(self):
        b = facts([("a", "measured", 100)])
        with self.assertRaisesRegex(ValueError, "architecture"):
            compare(b, facts([("a", "measured", 100)], "linux-arm64"))
        current = facts([("a", "measured", 100)])
        current["method"] = "different"
        with self.assertRaisesRegex(ValueError, "method"):
            compare(b, current)

    def test_reject_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            indexed(facts([("a", "measured", 1), ("a", "measured", 1)]))

    def test_expected_inventory_has_all_96_rows(self):
        required = expected_ids()
        self.assertEqual(len(required), 96)
        self.assertNotIn("fixed/abi1_mono", required)
        self.assertIn("module/osc.out/voices1", required)
        self.assertIn("module/osc.out/voices8", required)

    def test_single_historic_retired_row_is_disclosed_not_passed(self):
        old = facts([("fixed/abi1_mono", "measured", 100),
                     ("fixed/abi2_mono", "measured", 100)])
        new = facts([("fixed/abi2_mono", "measured", 100)])
        old["rows"][0]["totals"] = [1000, 3000]
        old["rows"][1]["totals"] = [1000, 3000]
        new["rows"][0]["totals"] = [1000, 3000]
        changes, errors = compare(old, new, required_ids={"fixed/abi2_mono"}, verify_totals=True)
        self.assertEqual(errors, [])
        retired = [r for r in changes if r["status"] == "retired"]
        self.assertEqual([r["id"] for r in retired], ["fixed/abi1_mono"])
        self.assertIsNone(retired[0]["percent"])
        self.assertEqual(len([r for r in changes if r["status"] == "measured"]), 1)
        new["rows"].append(old["rows"][0].copy())
        self.assertTrue(compare(old, new, required_ids={"fixed/abi2_mono"}, verify_totals=True)[1])
        new["rows"].pop()
        old["rows"][0]["status"] = "unavailable"
        self.assertTrue(compare(old, new, required_ids={"fixed/abi2_mono"}, verify_totals=True)[1])

    def test_missing_on_both_sides_fails_with_required_inventory(self):
        a = facts([("fixed/abi2_mono", "measured", 100)])
        _, errors = compare(a, a, required_ids={
            "fixed/abi2_mono", "module/osc.out/voices1"})
        self.assertTrue(any("module/osc.out/voices1: missing baseline row" in e
                            for e in errors))

    def test_measured_row_needs_real_callgrind_totals_in_strict_mode(self):
        a = facts([("fixed/abi2_mono", "measured", 100)])
        _, errors = compare(a, a, verify_totals=True)
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid baseline", errors[0])
        a["rows"][0]["totals"] = [1000, 3000]
        self.assertEqual(compare(a, a, verify_totals=True)[1], [])
        a["rows"][0]["totals"] = [1000, 3001]
        self.assertTrue(compare(a, a, verify_totals=True)[1])

    def test_newly_recovered_row_requires_real_numeric_measurement(self):
        baseline = facts([("module/essentials.chord/voices1", "unavailable", None)])
        current = facts([("module/essentials.chord/voices1", "measured", None)])
        changes, failures = compare(baseline, current, verify_totals=True)
        self.assertEqual(changes[0]["status"], "invalid_measurement")
        self.assertTrue(any("invalid current Ir" in failure for failure in failures))

    def test_valgrind_version_mismatch_rejected(self):
        a = facts([("fixed/abi2_mono", "measured", 100)])
        b = facts([("fixed/abi2_mono", "measured", 100)])
        a["valgrind_version"] = "valgrind-3.22.0"
        b["valgrind_version"] = "valgrind-3.23.0"
        with self.assertRaisesRegex(ValueError, "Valgrind version"):
            compare(a, b)

    def test_markdown_contains_ten_largest_and_failure(self):
        b = facts([(f"r{i}", "measured", 100) for i in range(15)])
        c = facts([(f"r{i}", "measured", 100 + i) for i in range(15)])
        changes, errors = compare(b, c)
        text = render(changes, errors, 3, markdown=True)
        self.assertIn("r14", text)
        self.assertIn("**Exceeded threshold", text)
        self.assertNotIn("| r0 |", text)


if __name__ == "__main__":
    unittest.main()
