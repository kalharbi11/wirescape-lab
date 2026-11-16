# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer tests for locating a command from its marks (ruling R7, QUESTIONS Q10):
parsing and refusal, block-to-sample mapping across segments, the metric window from a
bracket, first divergence inside and outside the bracket, and alignment on a shared mark."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture  # noqa: E402
import marks as mk  # noqa: E402
import metrics as m  # noqa: E402

RATE = 48000


def line(**kw):
    base = {'re': 'r1', 'type': 'loadGraph', 'ok': True, 'gen': '1', 'b0': 10, 'b1': 12}
    base.update(kw)
    return json.dumps(base)


def seg(index, block, blocks, value=0.0):
    return capture.Segment(index, RATE, 1, block, True, [[value] * (block * blocks)])


class Parse(unittest.TestCase):
    def test_good_file(self):
        text = line() + '\n' + line(re='r2', type='noteOn', gen='1', b0=12, b1=12) + '\n'
        got = mk.parse(text)
        self.assertEqual(got[0], mk.Mark('r1', 'loadGraph', True, '1', 10, 12))
        self.assertEqual(got[1].width, 1)
        self.assertEqual(got[0].width, 3)

    def test_missing_and_extra_keys_are_refused(self):
        bad = json.loads(line())
        del bad['gen']
        with self.assertRaises(ValueError):
            mk.parse(json.dumps(bad))
        with self.assertRaises(ValueError):
            mk.parse(json.dumps({**json.loads(line()), 'time': 1.5}))

    def test_wrong_types_are_refused(self):
        for kw in ({'gen': 1}, {'gen': '-1'}, {'gen': '1.5'}, {'ok': 1}, {'b0': True},
                   {'b1': 12.0}, {'re': 7}, {'b0': -1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                mk.parse(line(**kw))

    def test_b0_after_b1_is_refused(self):
        with self.assertRaises(ValueError):
            mk.parse(line(b0=13, b1=12))

    def test_out_of_order_is_refused(self):
        with self.assertRaises(ValueError):
            mk.parse(line() + '\n' + line(re='r2', b0=9, b1=20))

    def test_refused_request_without_id_or_type_is_kept(self):
        # The sidecar marks a refused request that had no valid id/type with nulls (#104).
        got = mk.parse(line() + '\n' + line(re=None, type=None, ok=False, b0=12, b1=12) + '\n' +
                       line(re=None, type=None, ok=False, b0=12, b1=13))
        self.assertEqual([g.re for g in got], ['r1', None, None])
        for kw in ({'re': None}, {'type': None}):  # an accepted command always carries both
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                mk.parse(line(**kw))

    def test_equal_b0_is_allowed(self):
        self.assertEqual(len(mk.parse(line() + '\n' + line(re='r2', b0=10, b1=10))), 2)

    def test_repeated_request_id_and_bad_lines_are_refused(self):
        for text in (line() + '\n' + line(), line() + '\n\n' + line(re='r2'), '[1]', '{'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                mk.parse(text)

    def test_locate(self):
        ms = mk.parse(line() + '\n' + line(re='r2', b0=20, b1=21))
        self.assertEqual((mk.locate(ms, 'r2').b0, mk.locate(ms, 'r2').b1), (20, 21))
        with self.assertRaises(KeyError):
            mk.locate(ms, 'r3')


class Mapping(unittest.TestCase):
    # Segment 0: 100 blocks of 256 (25600 samples); segment 1 (after setBufferFrames): 50 of 128.
    geo = mk.Geometry.of([seg(0, 256, 100), seg(1, 128, 50)])

    def test_first_segment(self):
        self.assertEqual(mk.block_position(self.geo, 0), (0, 0))
        self.assertEqual(mk.block_position(self.geo, 99), (0, 99 * 256))
        self.assertEqual(mk.block_sample(self.geo, 99), 25344)

    def test_second_segment_uses_its_own_block(self):
        self.assertEqual(mk.block_position(self.geo, 100), (1, 0))
        self.assertEqual(mk.block_position(self.geo, 103), (1, 3 * 128))
        self.assertEqual(mk.block_sample(self.geo, 103), 25600 + 384)

    def test_end_and_outside(self):
        self.assertEqual(mk.block_sample(self.geo, 150), 25600 + 6400)
        with self.assertRaises(ValueError):
            mk.block_position(self.geo, 151)
        with self.assertRaises(ValueError):
            mk.block_position(self.geo, -1)

    def test_sample_to_block_inverts(self):
        for b in (0, 57, 99, 100, 149):
            self.assertEqual(mk.sample_block(self.geo, mk.block_sample(self.geo, b)), b)
        self.assertEqual(mk.sample_block(self.geo, 25600 + 127), 100)
        self.assertEqual(mk.sample_block(self.geo, 25600 + 128), 101)

    def test_mixed_rates_are_refused(self):
        other = capture.Segment(1, 44100, 1, 128, True, [[0.0] * 128])
        with self.assertRaises(ValueError):
            mk.Geometry.of([seg(0, 256, 1), other])


class EditWindow(unittest.TestCase):
    def test_window_from_bracket(self):
        geo = mk.Geometry.of([seg(0, 256, 400)])  # 102400 samples
        w = mk.edit_window(geo, mk.Mark('e', 'connect', True, '5', 100, 103))
        self.assertEqual((w.edit, w.late, w.width_blocks), (25600, 104 * 256, 4))
        self.assertEqual((w.lo, w.hi), (25600 - 4800, 104 * 256 + 48000))

    def test_window_across_a_segment_change(self):
        geo = mk.Geometry.of([seg(0, 256, 100), seg(1, 128, 500)])
        w = mk.edit_window(geo, mk.Mark('e', 'setBufferFrames', True, '5', 99, 100))
        self.assertEqual((w.edit, w.late), (99 * 256, 25600 + 128))
        self.assertEqual(w.width_blocks, 2)

    def test_window_outside_capture_is_refused(self):
        geo = mk.Geometry.of([seg(0, 256, 200)])
        with self.assertRaises(ValueError):
            mk.edit_window(geo, mk.Mark('e', 'x', True, '1', 10, 10))   # 100 ms before b0 < 0
        with self.assertRaises(ValueError):
            mk.edit_window(geo, mk.Mark('e', 'x', True, '1', 150, 160))  # 1 s after past end

    def test_metrics_window_spans_the_bracket(self):
        x = [0.0] * 120000
        self.assertEqual(m.window(x, RATE, 30000, 31024), (30000 - 4800, 31024 + 48000))
        self.assertEqual(m.window(x, RATE, 30000), (25200, 78000))
        with self.assertRaises(ValueError):
            m.window(x, RATE, 30000, 29999)

    def test_silence_after_the_bracket_start_is_inside_the_window(self):
        # A 10 ms gap starting 1 s + 20 samples after b0 is outside a zero-width window, inside a 2-block one.
        w = 2 * math.pi * 1000 / RATE
        x = [0.5 * math.sin(w * t) for t in range(120000)]
        for i in range(30000 + 48020, 30000 + 48020 + 480):
            x[i] = 0.0
        self.assertLess(m.silence_ms(x, RATE, 30000), 1.0)
        self.assertAlmostEqual(m.silence_ms(x, RATE, 30000, 30000 + 512), 10.0, delta=0.1)


class Divergence(unittest.TestCase):
    geo = mk.Geometry.of([seg(0, 256, 400)])
    mark = mk.Mark('e', 'setParam', True, '3', 100, 103)  # effect in blocks 100..104

    def _pair(self, at):
        ref = [0.25] * self.geo.total_samples
        x = list(ref)
        for i in range(at, len(x)):
            x[i] = 0.75
        return x, ref

    def test_inside_narrows_the_bracket(self):
        x, ref = self._pair(102 * 256 + 17)
        w = mk.edit_window(self.geo, self.mark)
        d = mk.first_divergence(x, ref, w.lo, w.hi, 1e-3)
        self.assertEqual(d, 102 * 256 + 17)
        got = mk.place_divergence(self.geo, self.mark, d)
        self.assertTrue(got.inside)
        self.assertEqual(got.narrowed, (100, 102))
        self.assertIsNone(got.finding)

    def test_latest_block_is_inside(self):
        got = mk.place_divergence(self.geo, self.mark, 104 * 256 + 255)
        self.assertTrue(got.inside)

    def test_outside_is_a_finding_not_a_position(self):
        for at, where in ((99 * 256, 'before'), (105 * 256, 'after')):
            x, ref = self._pair(at)
            w = mk.edit_window(self.geo, self.mark)
            got = mk.place_divergence(self.geo, self.mark, mk.first_divergence(x, ref, w.lo, w.hi, 1e-3))
            with self.subTest(where=where):
                self.assertFalse(got.inside)
                self.assertIsNone(got.narrowed)
                self.assertIn(where, got.finding)

    def test_no_divergence(self):
        ref = [0.25] * 1000
        self.assertIsNone(mk.first_divergence(ref, list(ref), 0, 1000, 1e-3))
        self.assertEqual(mk.place_divergence(self.geo, self.mark, None).inside, None)


class Align(unittest.TestCase):
    def test_offset_and_uncertainty_from_a_shared_mark(self):
        a = mk.parse(line(re='n1', type='noteOn', b0=50, b1=51) + '\n' + line(re='e', b0=90, b1=92))
        b = mk.parse(line(re='n1', type='noteOn', b0=47, b1=47))
        al = mk.align_offset(a, b, 'n1')
        self.assertEqual(al.offset, 3)
        self.assertEqual((al.lo, al.hi), (50 - 48, 52 - 47))
        self.assertEqual(al.uncertainty, a[0].width + b[0].width)

    def test_type_mismatch_and_missing_are_refused(self):
        a = mk.parse(line(re='n1', type='noteOn'))
        b = mk.parse(line(re='n1', type='noteOff'))
        with self.assertRaises(ValueError):
            mk.align_offset(a, b, 'n1')
        with self.assertRaises(KeyError):
            mk.align_offset(a, a, 'n2')

    def test_aligned_reference_has_no_divergence(self):
        # The same signal starts 3 blocks later in A than in B; aligning on the mark removes it.
        block = 256
        sig = [math.sin(0.01 * t) for t in range(20 * block)]
        ref = sig + [0.0] * (3 * block)
        x = [0.0] * (3 * block) + sig
        al = mk.align_offset([mk.Mark('n1', 'noteOn', True, '1', 5, 5)],
                             [mk.Mark('n1', 'noteOn', True, '1', 2, 2)], 'n1')
        moved = mk.shift(ref, al.offset * block)
        self.assertIsNone(mk.first_divergence(x, moved, 3 * block, len(x), 1e-9))
        self.assertIsNotNone(mk.first_divergence(x, ref, 3 * block, len(x), 1e-3))
        with self.assertRaises(ValueError):
            mk.first_divergence(x, moved, 0, len(x), 1e-9)  # padding is not a reference


if __name__ == '__main__':
    unittest.main()
