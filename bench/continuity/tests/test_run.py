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


class ControlComparison(unittest.TestCase):
    def test_identical_tail_with_natural_silence_is_neutral(self):
        edit, late = RATE, RATE + BLOCK
        control = [0.15] * RATE + [0.0] * BLOCK + [0.1] * RATE
        result = run.compare_control(control, control, 'tail', edit, late)
        self.assertTrue(result['identical'])
        self.assertEqual(result['samples'], 2 * RATE + BLOCK)
        self.assertEqual(result['silence_ms'], 0)
        self.assertEqual(result['dip_db'], 0)
        self.assertEqual(result['jump_ratio'], 1)

    def test_edit_silence_is_measured_against_sounding_control(self):
        edit, late = RATE, RATE + BLOCK
        control = [0.1] * (2 * RATE + BLOCK)
        edited = control[:edit] + [0.0] * BLOCK + control[late:]
        result = run.compare_control(edited, control, 'held_note', edit, late)
        self.assertFalse(result['identical'])
        self.assertEqual(result['first_mismatch_from_edit'], 0)
        self.assertAlmostEqual(result['silence_ms'], 1000 * BLOCK / RATE)
        self.assertEqual(result['dip_db'], '-inf')
        self.assertIsNone(result['jump_ratio'])

    def test_alignment_padding_is_rejected(self):
        control = [0.1] * (2 * RATE)
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            run.compare_control(control, [math.nan, *control[1:]], 'tone', RATE, RATE)


def _marks():
    return [mk.Mark('load', 'loadGraph', True, '1', 10, 12), mk.Mark('note', 'noteOn', True, '1', 400, 400),
            mk.Mark('edit', 'loadGraph', True, '2', 800, 802)]


class SubjectRestart(unittest.TestCase):
    """Runner-level: the reset reference the subject is compared with (lead review on #106)."""
    N = 6 * RATE
    NOTE, EDIT, LATE = 400 * BLOCK, 800 * BLOCK, 803 * BLOCK
    GEO = mk.Geometry(((6 * RATE // BLOCK, BLOCK),), RATE)

    def held(self):
        w = 2 * math.pi * 440 / RATE
        return [0.0 if t < self.NOTE else 0.7 * min(1.0, (t - self.NOTE) / 240) * math.sin(w * t)
                for t in range(self.N)]

    def test_held_note_reset_to_silence_is_unobservable_not_false(self):
        cont = self.held()
        x = cont[:self.EDIT] + [0.0] * (self.N - self.EDIT)  # graph reset: the held gate is gone
        state, note = run.subject_restart(x, cont, self.GEO, _marks(), 3, self.EDIT, self.LATE)
        self.assertIsNone(state, note)
        self.assertIn('silent reference', note)

    def test_held_note_reference_is_its_idle_silence_not_the_attack(self):
        ref = run.reset_reference(self.held(), self.GEO, _marks(), 3, self.EDIT)
        self.assertEqual(len(ref), RATE // 4)
        self.assertTrue(all(v == 0.0 for v in ref))

    def test_held_note_that_continues_did_not_restart(self):
        cont = self.held()
        state, _ = run.subject_restart(list(cont), cont, self.GEO, _marks(), 3, self.EDIT, self.LATE)
        self.assertIs(state, False)

    def test_held_note_sounding_before_its_note_is_refused(self):
        x = [0.1] * self.N
        with self.assertRaises(ValueError):
            run.reset_reference(x, self.GEO, _marks(), 3, self.EDIT)

    def test_sounding_subject_restart_from_first_sound(self):
        # Subject sounds from the load swap (block 14, after a silent lead from b0 = 10). A reset at
        # the edit repeats it from its first sound; the reference must not include the silent lead.
        w = 2 * math.pi * 330.3 / RATE
        first = 14 * BLOCK
        cont = [0.0 if t < first else math.sin(w * (t - first)) for t in range(self.N)]
        x = cont[:self.EDIT] + cont[first:first + self.N - self.EDIT]
        state, _ = run.subject_restart(x, cont, self.GEO, _marks(), 5, self.EDIT, self.LATE)
        self.assertIs(state, True)

    def test_changed_subject_false_becomes_not_testable(self):
        w = 2 * math.pi * 330.3 / RATE
        cont = [math.sin(w * t) for t in range(self.N)]
        x = cont[:self.EDIT] + [math.sin(w * 1.33 * t) for t in range(self.EDIT, self.N)]
        state, note = run.subject_restart(x, cont, self.GEO, _marks(), 5, self.EDIT, self.LATE, True)
        self.assertIsNone(state)
        self.assertIn('not testable', note)


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
        self.assertEqual(len(names), 29)
        for e in probe.edits():
            self.assertTrue(e['subject'] is None or 0 <= e['subject'] < 16)


if __name__ == '__main__':
    unittest.main()
