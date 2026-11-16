# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer tests for the six edit-continuity metrics (proposals/0005 section 4) and the capture
reader, on synthetic signals: a clean sine, a 3-block gap, a phase jump and a step."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture  # noqa: E402
import metrics as m  # noqa: E402

RATE, BLOCK, FREQ, AMP = 48000, 256, 1000.0, 0.5
TOTAL = 2 * RATE                    # 2 s of signal
EDIT = RATE                         # edit located at 1.0 s
GAP = 3 * BLOCK                     # the 3-block gap: 768 samples = 16 ms


def sine(phase_jump=0.0, jump_at=None, n=TOTAL, freq=FREQ, amp=AMP):
    w = 2 * math.pi * freq / RATE
    return [amp * math.sin(w * t + (phase_jump if jump_at is not None and t >= jump_at else 0.0))
            for t in range(n)]


def gapped():
    x = sine()
    for i in range(EDIT, EDIT + GAP):
        x[i] = 0.0
    return x


class Silence(unittest.TestCase):
    def test_clean_sine_has_no_silence(self):
        # A 1 kHz sine at 48 kHz never has two consecutive samples below -80 dBFS.
        self.assertLessEqual(m.silence_ms(sine(), RATE, EDIT), 1000 / RATE)

    def test_three_block_gap(self):
        self.assertAlmostEqual(m.silence_ms(gapped(), RATE, EDIT), 16.0, delta=2 * 1000 / RATE)

    def test_phase_jump_and_step_are_not_silence(self):
        self.assertLessEqual(m.silence_ms(sine(math.pi / 2, EDIT), RATE, EDIT), 1000 / RATE)


class Dip(unittest.TestCase):
    def test_clean_sine_is_flat(self):
        # 1 ms is exactly one period of 1 kHz: the sliding RMS equals the steady RMS.
        self.assertAlmostEqual(m.dip_db(sine(), RATE, EDIT), 0.0, delta=0.01)

    def test_gap_is_minus_infinity(self):
        self.assertEqual(m.dip_db(gapped(), RATE, EDIT), -math.inf)

    def test_half_amplitude_block_is_minus_six_db(self):
        x = sine()
        for i in range(EDIT, EDIT + 3 * BLOCK):
            x[i] *= 0.5
        self.assertAlmostEqual(m.dip_db(x, RATE, EDIT), 20 * math.log10(0.5), delta=0.05)


class TimeSlip(unittest.TestCase):
    def test_clean_sine_has_no_slip(self):
        self.assertAlmostEqual(m.time_slip_tone_ms(sine(), RATE, EDIT, FREQ), 0.0, delta=1e-6)

    def test_phase_jump_reads_as_time(self):
        # Phase advanced by pi/2 at 1 kHz: the witness is a quarter period (0.25 ms) early.
        slip = m.time_slip_tone_ms(sine(math.pi / 2, EDIT), RATE, EDIT, FREQ)
        self.assertAlmostEqual(slip, -0.25, delta=1e-6)

    def test_gap_that_pauses_the_oscillator_reads_late(self):
        # A source that stops for 3 blocks and resumes where it left off slips by 16 ms,
        # which would wrap modulo a 1 ms period; the 10 Hz slip tone keeps it under half a period.
        f = 10.0
        w = 2 * math.pi * f / RATE
        x = [AMP * math.sin(w * t) for t in range(EDIT)] + [0.0] * GAP
        x += [AMP * math.sin(w * t) for t in range(EDIT, TOTAL - GAP)]
        self.assertAlmostEqual(m.time_slip_tone_ms(x, RATE, EDIT, f), 16.0, delta=1e-3)

    def test_clock_grid(self):
        period = 12000  # 250 ms, i.e. 240 BPM quarter notes
        def clicks(shift):
            x = [0.0] * TOTAL
            for k in range(0, TOTAL // period + 1):
                at = k * period + (shift if k * period >= EDIT else 0)
                if at < TOTAL:
                    for j in range(48):
                        if at + j < TOTAL:
                            x[at + j] = 0.8 * (1 - j / 48)
            return x
        self.assertEqual(m.time_slip_clock_ms(clicks(0), RATE, EDIT, 0.1), 0.0)
        self.assertAlmostEqual(m.time_slip_clock_ms(clicks(GAP), RATE, EDIT, 0.1), 16.0)
        self.assertAlmostEqual(m.time_slip_clock_ms(clicks(-480), RATE, EDIT, 0.1), -10.0)


class Jump(unittest.TestCase):
    def test_clean_sine_ratio_is_one(self):
        self.assertAlmostEqual(m.jump_ratio(sine(), RATE, EDIT), 1.0, delta=1e-3)

    def test_step(self):
        x = sine()
        for i in range(EDIT, TOTAL):
            x[i] += 0.3
        w = 2 * math.pi * FREQ / RATE
        steady_step = max(abs(x[i + 1] - x[i]) for i in range(RATE // 2, EDIT - 4800))
        expected = (0.3 + abs(AMP * (math.sin(w * EDIT) - math.sin(w * (EDIT - 1))))) / steady_step
        self.assertAlmostEqual(m.jump_ratio(x, RATE, EDIT), expected, delta=0.05)
        self.assertGreater(m.jump_ratio(x, RATE, EDIT), 3.0)

    def test_phase_jump(self):
        # A pi jump at a crest (a quarter period after the edit) is a step of about 1.0, against a
        # steady step of 0.5 * 2*pi*1000/48000 = 0.065; at a zero crossing it would be a slope flip only.
        x = sine(math.pi, EDIT + 12)
        self.assertAlmostEqual(m.jump_ratio(x, RATE, EDIT), 1.0 / (0.5 * 2 * math.pi * FREQ / RATE), delta=0.1)
        self.assertAlmostEqual(m.jump_ratio(sine(math.pi, EDIT), RATE, EDIT), 1.0, delta=1e-3)


class Disturbed(unittest.TestCase):
    def test_clean_sine_against_fitted_continuation(self):
        x = sine()
        self.assertEqual(m.disturbed_ms(x, m.sine_continuation(x, RATE, EDIT, FREQ), RATE, EDIT), 0.0)

    def test_gap_disturbs_its_own_length_plus_one_frame(self):
        x = gapped()
        span = m.disturbed_ms(x, sine(), RATE, EDIT)
        # The gap starts on a zero crossing, so its first sample does not differ.
        self.assertAlmostEqual(span, 16.0, delta=2 * 1000 / RATE)

    def test_phase_jump_disturbs_to_the_end_of_the_window(self):
        x = sine(math.pi / 2, EDIT)
        span = m.disturbed_ms(x, m.sine_continuation(x, RATE, EDIT, FREQ), RATE, EDIT)
        self.assertAlmostEqual(span, 1000.0, delta=1.0)

    def test_step_against_no_edit_capture(self):
        x = sine()
        for i in range(EDIT, EDIT + BLOCK):
            x[i] += 0.3
        self.assertAlmostEqual(m.disturbed_ms(x, sine(), RATE, EDIT), 1000 * BLOCK / RATE, delta=1e-9)


class Restarted(unittest.TestCase):
    def test_continuing_subject_did_not_restart(self):
        # 110 Hz completes whole cycles at 1.0 s, so the start-of-load waveform recurs exactly at the
        # edit; a continuing subject must still not count as restarted.
        x = sine(freq=110.0)
        self.assertEqual(m.restarted(x, x, x, RATE, EDIT), (False, None))

    def test_reset_phase_is_found_at_the_edit(self):
        f = 110.3  # not whole cycles at 1.0 s, so restart and continuation differ
        start = sine(freq=f)
        x = start[:EDIT] + start[:TOTAL - EDIT]  # oscillator restarted from phase 0 at the edit
        self.assertEqual(m.restarted(x, start, sine(freq=f), RATE, EDIT), (True, EDIT))

    def test_restart_one_block_late_is_found(self):
        f = 110.3  # not whole cycles at 1.0 s, so restart and continuation differ
        start = sine(freq=f)
        x = start[:EDIT + BLOCK] + start[:TOTAL - EDIT - BLOCK]
        self.assertEqual(m.restarted(x, start, sine(freq=f), RATE, EDIT), (True, EDIT + BLOCK))

    def test_gap_is_not_a_restart(self):
        f = 110.0
        x = sine(freq=f)
        for i in range(EDIT, EDIT + GAP):
            x[i] = 0.0
        self.assertEqual(m.restarted(x, sine(freq=f), sine(freq=f), RATE, EDIT)[0], False)


class Window(unittest.TestCase):
    def test_window_outside_capture_is_refused(self):
        with self.assertRaises(ValueError):
            m.silence_ms(sine(n=RATE), RATE, RATE - 10)

    def test_silent_steady_region_is_refused(self):
        with self.assertRaises(ValueError):
            m.dip_db([0.0] * TOTAL, RATE, EDIT)


class CaptureReader(unittest.TestCase):
    def segment(self, index, blocks, channels=3):
        data = [[(c + 1) * 0.001 * i for i in range(blocks * BLOCK)] for c in range(channels)]
        return capture.Segment(index, RATE, channels, BLOCK, True, data)

    def test_round_trip_two_segments(self):
        segs = [self.segment(0, 4), self.segment(1, 2)]
        back = capture.parse(capture.encode(segs))
        self.assertEqual([s.blocks for s in back], [4, 2])
        self.assertEqual((back[0].rate, back[0].channels, back[0].block), (RATE, 3, BLOCK))
        for a, b in zip(segs, back):
            for ca, cb in zip(a.data, b.data):
                self.assertEqual(len(ca), len(cb))
                for u, v in zip(ca, cb):
                    self.assertAlmostEqual(u, v, places=5)

    def test_open_last_segment_reads_complete_blocks_only(self):
        raw = capture.encode([self.segment(0, 3)], leave_last_open=True) + b'\0' * 7
        back = capture.parse(raw)
        self.assertFalse(back[0].closed)
        self.assertEqual(back[0].blocks, 3)

    def test_bad_magic_and_short_segment_are_refused(self):
        raw = bytearray(capture.encode([self.segment(0, 2)]))
        with self.assertRaises(ValueError):
            capture.parse(b'X' + bytes(raw[1:]))
        with self.assertRaises(ValueError):
            capture.parse(bytes(raw[:-4]))


if __name__ == '__main__':
    unittest.main()
