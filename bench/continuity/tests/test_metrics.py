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


PERIOD = 12000  # clock: 250 ms, i.e. 240 BPM quarter notes; EDIT is grid event 4


def clicks(shift, drop=()):
    x = [0.0] * TOTAL
    for k in range(0, TOTAL // PERIOD + 1):
        at = k * PERIOD + (shift if k * PERIOD >= EDIT else 0)
        if at < TOTAL and k * PERIOD not in drop:
            for j in range(48):
                if at + j < TOTAL:
                    x[at + j] = 0.8 * (1 - j / 48)
    return x


def slow(delay=0, start=None, end=None, f=10.0, mute=None):
    """10 Hz slip tone, delayed by `delay` samples over [start, end), zero over `mute`."""
    w = 2 * math.pi * f / RATE
    out = []
    for t in range(TOTAL):
        d = delay if start is not None and start <= t < (end if end is not None else TOTAL) else 0
        out.append(AMP * math.sin(w * (t - d)))
    if mute:
        for t in range(*mute):
            out[t] = 0.0
    return out


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
        self.assertEqual(m.time_slip_clock_ms(clicks(0), RATE, EDIT, 0.1), 0.0)
        self.assertAlmostEqual(m.time_slip_clock_ms(clicks(GAP), RATE, EDIT, 0.1), 16.0)
        self.assertAlmostEqual(m.time_slip_clock_ms(clicks(-480), RATE, EDIT, 0.1), -10.0)

    def test_missing_next_onset_keeps_its_identity(self):
        # The pulse due at the edit (grid event 4) never sounds; later pulses are on the grid.
        # Nearest-grid matching would renumber pulse 5 as "on time" and read 0 ms. The next
        # expected event is reported missing, and the next onset is one period late.
        r = m.clock_slip(clicks(0, drop=(EDIT,)), RATE, EDIT, 0.1)
        self.assertEqual(r['missing'], [EDIT])
        self.assertEqual(r['next_offset_ms'], 250.0)
        self.assertEqual(r['slip_ms'], 250.0)
        self.assertEqual(r['extra'], [])

    def test_clean_clock_reports_nothing_missing(self):
        r = m.clock_slip(clicks(0), RATE, EDIT, 0.1)
        self.assertEqual((r['slip_ms'], r['next_offset_ms'], r['missing'], r['extra']), (0.0, 0.0, [], []))

    def test_no_onset_after_the_edit_is_unavailable(self):
        x = clicks(0)
        for i in range(EDIT - 100, TOTAL):
            x[i] = 0.0
        r = m.clock_slip(x, RATE, EDIT, 0.1)
        self.assertIsNone(r['slip_ms'])
        self.assertEqual(len(r['missing']), 4)  # events at 1.0, 1.25, 1.5, 1.75 s inside the window

    def test_temporary_displacement_is_measured(self):
        # Delayed by 16 ms from the edit, recovered 300 ms later: a fit at the window's end would
        # read 0; the contracted 50 ms after the edit reads the displacement.
        x = slow(GAP, EDIT, EDIT + 300 * RATE // 1000)
        self.assertAlmostEqual(m.time_slip_tone_ms(x, RATE, EDIT, 10.0), 16.0, delta=1e-3)

    def test_muted_tone_has_no_phase(self):
        self.assertIsNone(m.time_slip_tone_ms(slow(mute=(EDIT, TOTAL)), RATE, EDIT, 10.0))

    def test_short_dropout_on_continuing_phase_is_no_slip(self):
        # A 3-block mute with the oscillator running underneath: phase kept, slip 0.
        x = slow(mute=(EDIT, EDIT + GAP))
        self.assertAlmostEqual(m.time_slip_tone_ms(x, RATE, EDIT, 10.0), 0.0, delta=1e-3)


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
        self.assertEqual(m.restarted(x, x, x, RATE, EDIT)[:2], (False, None))

    def test_reset_phase_is_found_at_the_edit(self):
        f = 110.3  # not whole cycles at 1.0 s, so restart and continuation differ
        start = sine(freq=f)
        x = start[:EDIT] + start[:TOTAL - EDIT]  # oscillator restarted from phase 0 at the edit
        self.assertEqual(m.restarted(x, start, sine(freq=f), RATE, EDIT)[:2], (True, EDIT))

    def test_restart_one_block_late_is_found(self):
        f = 110.3  # not whole cycles at 1.0 s, so restart and continuation differ
        start = sine(freq=f)
        x = start[:EDIT + BLOCK] + start[:TOTAL - EDIT - BLOCK]
        self.assertEqual(m.restarted(x, start, sine(freq=f), RATE, EDIT)[:2], (True, EDIT + BLOCK))

    def test_gap_is_not_a_restart(self):
        f = 110.0
        x = sine(freq=f)
        for i in range(EDIT, EDIT + GAP):
            x[i] = 0.0
        self.assertEqual(m.restarted(x, sine(freq=f), sine(freq=f), RATE, EDIT)[0], False)


    def test_phase_jump_without_reset_is_not_a_restart(self):
        # 100 Hz (480 samples a period), +pi/2 at the edit, no reset: the displaced sine reaches the
        # start-of-load phase 7.5 ms later, inside the search span. That is not a return to reset.
        f = 100.0
        x = sine(math.pi / 2, EDIT, freq=f)
        r = m.restarted(x, sine(freq=f), sine(freq=f), RATE, EDIT)
        self.assertEqual(r[:2], (False, None))

    def test_mute_then_reset_is_a_restart(self):
        f = 110.3
        start = sine(freq=f)
        x = start[:EDIT] + [0.0] * BLOCK + start[:TOTAL - EDIT - BLOCK]
        self.assertEqual(m.restarted(x, start, sine(freq=f), RATE, EDIT)[:2], (True, EDIT + BLOCK))

    def test_fade_out_then_reset_is_a_restart(self):
        # A loadGraph-style restart: a 10 ms linear fade-out, one block of silence, then the subject
        # repeats its start-of-load output. The fade is never louder than the continuation.
        f = 110.3
        start, cont = sine(freq=f), sine(freq=f)
        fade = 480
        x = start[:EDIT] + [cont[EDIT + i] * (1 - i / fade) for i in range(fade)] + [0.0] * BLOCK
        x += start[:TOTAL - len(x)]
        self.assertEqual(m.restarted(x, start, cont, RATE, EDIT)[:2], (True, EDIT + fade + BLOCK))

    def test_louder_departure_then_start_match_is_not_a_restart(self):
        # Same timing but the gap holds a displaced (phase-shifted) sine, not a fade: not a reset.
        f = 110.3
        start, cont = sine(freq=f), sine(freq=f)
        moved = sine(math.pi / 2, 0, freq=f)
        x = start[:EDIT] + moved[EDIT:EDIT + 480 + BLOCK]
        x += start[:TOTAL - len(x)]
        self.assertEqual(m.restarted(x, start, cont, RATE, EDIT)[0], False)

    def test_silent_start_envelope_reset(self):
        # Start-of-load output is 25 ms of silence, then a 10 ms attack of a 200 Hz carrier.
        # A reset at the edit repeats that silence and attack; the held note would have continued.
        w = 2 * math.pi * 200.0 / RATE
        def env(t):
            return 0.0 if t < 1200 else 0.5 * min(1.0, (t - 1200) / 480) * math.sin(w * (t - 1200))
        start = [env(t) for t in range(TOTAL)]
        x = start[:EDIT] + start[:TOTAL - EDIT]
        r = m.restarted(x, start, start, RATE, EDIT)
        self.assertEqual(r[:2], (True, EDIT))

    def test_silent_reference_mute_is_unobservable(self):
        # Subject silent at load (envelope idle); at the edit its held note goes silent and stays.
        # A reset to idle and a mute give the same output: reported as unavailable, not guessed.
        held = sine(freq=200.0)
        x = held[:EDIT] + [0.0] * (TOTAL - EDIT)
        r = m.restarted(x, [0.0] * RATE, held, RATE, EDIT)
        self.assertEqual(r[:2], (None, EDIT + 1))  # 200 Hz crosses zero at the edit sample

    def test_silent_reference_mute_that_resumes_is_not_a_restart(self):
        held = sine(freq=200.0)
        x = held[:EDIT] + [0.0] * GAP + held[EDIT + GAP:]
        r = m.restarted(x, [0.0] * RATE, held, RATE, EDIT)
        self.assertEqual(r[:2], (False, None))


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
