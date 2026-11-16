# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer tests for the end-to-end runner's pure parts: reference alignment refinement
inside the offsets two marks allow, and the worst-of-repeats rule."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import marks as mk  # noqa: E402
import probe  # noqa: E402
import run  # noqa: E402

RATE, BLOCK = 48000, 256


def tone(n, start=0):
    return [math.sin(2 * math.pi * 1000 * (t - start) / RATE) if t >= start else 0.0 for t in range(n)]


class Refine(unittest.TestCase):
    def test_exact_offset_is_found_inside_the_allowed_range(self):
        # Reference B started 3 blocks earlier than A: B's block k is A's block k + 3.
        n = 3 * RATE
        a, b = tone(n, 10 * BLOCK), tone(n, 7 * BLOCK)
        got = run.refine(a, b, mk.Alignment(3, 1, 5, 4), edit=2 * RATE)
        self.assertEqual((got['offset'], got['residual'], got['exact_offsets']), (3, 0.0, [3]))

    def test_no_exact_match_reports_the_residual(self):
        n = 3 * RATE
        a = tone(n, 10 * BLOCK)
        b = [0.5 * v for v in tone(n, 7 * BLOCK)]
        got = run.refine(a, b, mk.Alignment(3, 1, 5, 4), edit=2 * RATE)
        self.assertEqual(got['exact_offsets'], [])
        self.assertGreater(got['residual'], 0.4)

    def test_offset_outside_the_marks_is_never_chosen(self):
        n = 3 * RATE
        a, b = tone(n, 10 * BLOCK), tone(n, 7 * BLOCK)  # true offset 3, marks allow only 0..1
        got = run.refine(a, b, mk.Alignment(0, 0, 1, 1), edit=2 * RATE)
        self.assertIn(got['offset'], (0, 1))
        self.assertGreater(got['residual'], 0.0)


class Worst(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(run.worst([1.0, 5.0, None], 'silence_ms'), 5.0)
        self.assertEqual(run.worst([-3.0, '-inf', -1.0], 'dip_db'), '-inf')
        self.assertEqual(run.worst([0.5, -2.0, 1.0], 'time_slip_ms'), -2.0)
        self.assertEqual(run.worst([False, True, None], 'restarted'), True)
        self.assertEqual(run.worst([None, False], 'restarted'), False)
        self.assertIsNone(run.worst([None, None], 'jump_ratio'))


class Probe(unittest.TestCase):
    def test_patch_and_edits_are_well_formed(self):
        p = probe.base()
        ids = {mod['id'] for mod in p['modules']}
        for c in p['connections']:
            self.assertIn(c['from']['module'], ids)
            self.assertIn(c['to']['module'], ids)
        channels = sorted(o['bus_channel'] for o in p['outputs'])
        self.assertEqual(channels, list(range(9)))
        names = [e['name'] for e in probe.edits()]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 21)
        for e in probe.edits():
            self.assertTrue(e['subject'] is None or 0 <= e['subject'] < 16)


if __name__ == '__main__':
    unittest.main()
