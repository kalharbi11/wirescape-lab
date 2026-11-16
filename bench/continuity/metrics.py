# SPDX-License-Identifier: GPL-3.0-only
"""The six edit-continuity metrics of proposals/0005 section 4, on one witness channel.

Every function takes the witness samples `x` (floats), the sample rate, `edit` and optionally
`late`. They are the edges of the command's marks bracket in samples (ruling R7, QUESTIONS Q10;
see marks.py): the effect landed on a block boundary no earlier than `edit` (start of block b0)
and no later than `late` (start of block b1 + 1). `late` defaults to `edit` (a bracket of zero
width, used by the synthetic tests). The analysis window is [edit - 100 ms, late + 1 s).
"Steady" quantities come from the 500 ms before that window, [edit - 600 ms, edit - 100 ms),
when the patch has settled after load. The tone slip fit runs over 50 ms before `edit` and 50 ms
from `late`, so neither fit straddles a possible effect position.

Choices the section leaves open are named here and in DESIGN.md, not hidden:
- silence_ms counts consecutive samples with |x| below -80 dBFS (sample level, not RMS).
- dip_db uses a sliding 1 ms RMS (hop of one sample), relative to the steady RMS.
- time_slip_ms (tone) fits a sine of the known frequency over the 50 ms before the edit and the
  50 ms after it, on one absolute time base, and reports the phase difference as time, wrapped to
  half a period. Positive: the witness is late. Dropout runs (>= 1 ms below -80 dBFS) are left out
  of each fit; a fit with under 5 ms of sounding samples is reported as unavailable (None).
- time_slip_ms (clock) sets the grid from onsets before the window. The expected events are the
  grid events from the first one at or after the edit; the observed events are the onsets after
  the midpoint between the last grid event before the edit and that one. The i-th observed onset
  is compared with the i-th expected event, so a missing next onset is never renumbered away: it
  shows as a late onset and is also listed in `missing`.
- disturbed_ms is the span from the first to the last sample whose absolute difference from the
  continuation exceeds -60 dB relative to the steady RMS (sample level, so no frame smearing).
- restarted: the subject repeats its own start-of-load samples near the edit, differs there from
  its no-edit continuation, AND the repeat begins where the subject leaves its continuation (only
  silence may lie between). A free-running periodic subject repeats its start every period, and a
  phase-displaced one reaches the start phase within a period, so a start match alone cannot tell
  a restart from continuing or from a displacement. A start-of-load reference that opens silent is
  matched with its silent lead; one that is silent throughout makes a reset to silence
  indistinguishable from a mute, and that is reported as unavailable (None) with the reason.
These functions report numbers only; nothing here decides pass or fail.
"""
from __future__ import annotations

import math
from typing import NamedTuple, Sequence

PRE_MS = 100.0
POST_MS = 1000.0
STEADY_MS = 500.0
SILENCE_DBFS = -80.0
DISTURB_DB = -60.0


def _ms(n: int, rate: int) -> float:
    return 1000.0 * n / rate


def _n(ms: float, rate: int) -> int:
    return int(round(ms * rate / 1000.0))


def window(x: Sequence[float], rate: int, edit: int, late: int | None = None) -> tuple[int, int]:
    late = edit if late is None else late
    if late < edit:
        raise ValueError(f'bracket end {late} before its start {edit}')
    lo, hi = edit - _n(PRE_MS, rate), late + _n(POST_MS, rate)
    if lo < 0 or hi > len(x):
        raise ValueError(f'window [{lo}, {hi}) outside capture of {len(x)} samples')
    return lo, hi


def steady(x: Sequence[float], rate: int, edit: int) -> tuple[int, int]:
    hi = edit - _n(PRE_MS, rate)
    lo = hi - _n(STEADY_MS, rate)
    if lo < 0:
        raise ValueError('not enough settled audio before the edit window')
    return lo, hi


def rms(x: Sequence[float]) -> float:
    return math.sqrt(sum(v * v for v in x) / len(x)) if len(x) else 0.0


def _db(ratio: float) -> float:
    return 20.0 * math.log10(ratio) if ratio > 0 else -math.inf


def _sliding_rms(x: Sequence[float], width: int) -> list[float]:
    """RMS of x[i:i+width] for every i, by running sums."""
    out, acc = [], 0.0
    for i, v in enumerate(x):
        acc += v * v
        if i >= width:
            acc -= x[i - width] * x[i - width]
        if i >= width - 1:
            out.append(math.sqrt(max(acc, 0.0) / width))
    return out


# 1. silence_ms
def silence_ms(x: Sequence[float], rate: int, edit: int, late: int | None = None) -> float:
    lo, hi = window(x, rate, edit, late)
    floor = 10.0 ** (SILENCE_DBFS / 20.0)
    best = run = 0
    for v in x[lo:hi]:
        run = run + 1 if abs(v) < floor else 0
        best = max(best, run)
    return _ms(best, rate)


# 2. dip_db
def dip_db(x: Sequence[float], rate: int, edit: int, late: int | None = None) -> float:
    lo, hi = window(x, rate, edit, late)
    s_lo, s_hi = steady(x, rate, edit)
    ref = rms(x[s_lo:s_hi])
    if ref == 0:
        raise ValueError('witness is silent in its steady region')
    lowest = min(_sliding_rms(x[lo:hi], max(1, _n(1.0, rate))))
    return _db(lowest / ref)


# 3a. time_slip_ms for the tone witness
def fit_sine(x: Sequence[float], start: int, freq: float, rate: int) -> tuple[float, float]:
    """Least-squares a*cos(wt)+b*sin(wt)+c with t = absolute sample index; returns (amplitude, phase)."""
    w = 2.0 * math.pi * freq / rate
    # Normal equations for [cos, sin, 1].
    s = [[0.0] * 3 for _ in range(3)]
    r = [0.0] * 3
    for k, v in enumerate(x):
        t = w * (start + k)
        basis = (math.cos(t), math.sin(t), 1.0)
        for i in range(3):
            r[i] += basis[i] * v
            for j in range(3):
                s[i][j] += basis[i] * basis[j]
    a, b, _ = _solve3(s, r)
    # a cos + b sin = A cos(wt - phase)
    return math.hypot(a, b), math.atan2(b, a)


def _solve3(m: list[list[float]], v: list[float]) -> list[float]:
    m = [row[:] + [v[i]] for i, row in enumerate(m)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        if abs(m[c][c]) < 1e-300:
            raise ValueError('singular sine fit')
        for r in range(3):
            if r != c:
                f = m[r][c] / m[c][c]
                for k in range(c, 4):
                    m[r][k] -= f * m[c][k]
    return [m[i][3] / m[i][i] for i in range(3)]


FIT_MS = 50.0
MIN_FIT_MS = 5.0


def _sounding(x: Sequence[float], start: int, rate: int) -> tuple[list[float], list[int]]:
    """Samples of x (absolute index start + k) outside dropout runs of >= 1 ms below -80 dBFS."""
    floor = 10.0 ** (SILENCE_DBFS / 20.0)
    run_min = max(1, _n(1.0, rate))
    quiet = [abs(v) < floor for v in x]
    keep = [True] * len(x)
    k = 0
    while k < len(x):
        if quiet[k]:
            j = k
            while j < len(x) and quiet[j]:
                j += 1
            if j - k >= run_min:
                for i in range(k, j):
                    keep[i] = False
            k = j
        else:
            k += 1
    return [v for v, ok in zip(x, keep) if ok], [start + i for i, ok in enumerate(keep) if ok]


def _fit_phase(x: Sequence[float], start: int, freq: float, rate: int) -> float | None:
    vals, idx = _sounding(x, start, rate)
    if len(vals) < _n(MIN_FIT_MS, rate):
        return None
    return fit_sine_at(vals, idx, freq, rate)[1]


def fit_sine_at(x: Sequence[float], idx: Sequence[int], freq: float, rate: int) -> tuple[float, float]:
    w = 2.0 * math.pi * freq / rate
    s = [[0.0] * 3 for _ in range(3)]
    r = [0.0] * 3
    for t_abs, v in zip(idx, x):
        t = w * t_abs
        basis = (math.cos(t), math.sin(t), 1.0)
        for i in range(3):
            r[i] += basis[i] * v
            for j in range(3):
                s[i][j] += basis[i] * basis[j]
    a, b, _ = _solve3(s, r)
    return math.hypot(a, b), math.atan2(b, a)


def time_slip_tone_ms(x: Sequence[float], rate: int, edit: int, freq: float,
                      late: int | None = None) -> float | None:
    """Phase of a sine fit over [edit - 50 ms, edit) and [late, late + 50 ms), as time.
    None when either side has under 5 ms of sounding samples (a muted tone has no phase)."""
    window(x, rate, edit, late)
    late = edit if late is None else late
    span = _n(FIT_MS, rate)
    before = _fit_phase(x[edit - span:edit], edit - span, freq, rate)
    after = _fit_phase(x[late:late + span], late, freq, rate)
    if before is None or after is None:
        return None
    # Same absolute time base: a pure continuation has equal phase. A later witness has a larger phase.
    d = (after - before + math.pi) % (2.0 * math.pi) - math.pi
    return 1000.0 * d / (2.0 * math.pi * freq)


# 3b. time_slip_ms for the clock witness
def onsets(x: Sequence[float], rate: int, threshold: float, hold_ms: float = 5.0) -> list[int]:
    """Indices where |x| rises to `threshold` after at least hold_ms below it."""
    hold = _n(hold_ms, rate)
    out, quiet = [], hold
    for i, v in enumerate(x):
        if abs(v) >= threshold:
            if quiet >= hold:
                out.append(i)
            quiet = 0
        else:
            quiet += 1
    return out


def clock_slip(x: Sequence[float], rate: int, edit: int, threshold: float,
               late: int | None = None) -> dict:
    """Offsets of the next onsets after the edit from the grid set before the window.
    Returns slip_ms (largest-magnitude signed offset over ordinal pairs, None when no onset follows
    the edit), next_offset_ms (the first expected event's), missing (expected grid sample indices
    with no onset within half a period) and extra (onsets not within half a period of the grid)."""
    lo, hi = window(x, rate, edit, late)
    found = onsets(x[:hi], rate, threshold)
    before = [i for i in found if i < lo]
    if len(before) < 3:
        raise ValueError('fewer than three onsets before the window to set a grid')
    gaps = sorted(b - a for a, b in zip(before, before[1:]))
    period = gaps[len(gaps) // 2]
    anchor = before[-1]
    k_next = -(-(edit - anchor) // period)  # first grid event at or after the edit
    g_next = anchor + k_next * period
    expected = list(range(g_next, hi, period))
    cut = g_next - period / 2.0
    observed = [i for i in found if cut <= i < hi]
    offsets = [o - g for o, g in zip(observed, expected)]
    near = lambda a, b: abs(a - b) <= period / 2.0
    missing = [g for g in expected if not any(near(o, g) for o in observed)]
    extra = [o for o in observed if not any(near(o, g) for g in expected)]
    signed = lambda d: _ms(d, rate) if d >= 0 else -_ms(-d, rate)
    worst = max(offsets, key=abs) if offsets else None
    return {
        'slip_ms': None if worst is None else signed(worst),
        'next_offset_ms': signed(offsets[0]) if offsets else None,
        'missing': missing,
        'extra': extra,
    }


def time_slip_clock_ms(x: Sequence[float], rate: int, edit: int, threshold: float,
                       late: int | None = None) -> float | None:
    return clock_slip(x, rate, edit, threshold, late)['slip_ms']


# 4. jump_ratio
def _max_step(x: Sequence[float]) -> float:
    return max((abs(b - a) for a, b in zip(x, x[1:])), default=0.0)


def jump_ratio(x: Sequence[float], rate: int, edit: int, late: int | None = None) -> float:
    lo, hi = window(x, rate, edit, late)
    s_lo, s_hi = steady(x, rate, edit)
    ref = _max_step(x[s_lo:s_hi])
    if ref == 0:
        raise ValueError('witness has no steady-state steps')
    return _max_step(x[lo:hi]) / ref


# 5. disturbed_ms
def disturbed_ms(x: Sequence[float], continuation: Sequence[float], rate: int, edit: int,
                 late: int | None = None) -> float:
    """`continuation` is the same witness without the edit, sample-aligned with x (the fitted sine
    for the tone; a no-edit capture for tail and held note)."""
    lo, hi = window(x, rate, edit, late)
    if len(continuation) < hi:
        raise ValueError('continuation shorter than the window')
    s_lo, s_hi = steady(x, rate, edit)
    ref = rms(x[s_lo:s_hi])
    if ref == 0:
        raise ValueError('witness is silent in its steady region')
    limit = ref * 10.0 ** (DISTURB_DB / 20.0)
    hit = [i for i, (a, b) in enumerate(zip(x[lo:hi], continuation[lo:hi])) if abs(a - b) > limit]
    return _ms(hit[-1] + 1 - hit[0], rate) if hit else 0.0


def sine_continuation(x: Sequence[float], rate: int, edit: int, freq: float) -> list[float]:
    """The tone witness's own continuation: a sine fitted over the steady region, over all of x."""
    s_lo, s_hi = steady(x, rate, edit)
    amp, phase = fit_sine(x[s_lo:s_hi], s_lo, freq, rate)
    w = 2.0 * math.pi * freq / rate
    mean = sum(x[s_lo:s_hi]) / (s_hi - s_lo)
    return [amp * math.cos(w * t - phase) + mean for t in range(len(x))]


# 6. restarted (subject only)
class Restart(NamedTuple):
    state: bool | None   # None: the signal cannot distinguish a restart (see note)
    at: int | None
    note: str


def restarted(x: Sequence[float], start: Sequence[float], continuation: Sequence[float], rate: int,
              edit: int, search_ms: float = 30.0, match_ms: float = 20.0,
              late: int | None = None) -> Restart:
    """Whether the subject returned to its reset value near the edit.

    `start` is the subject's own start-of-load output (the reset phase/envelope); `continuation`
    is its sample-aligned no-edit capture. A restart at `at` (from edit - search_ms to
    late + search_ms) needs x[at:] to repeat `start` (including any silent lead) to within -60 dB
    of the reference RMS over match_ms of sounding samples, to differ there from the continuation
    by more than that, and to begin where x first leaves the continuation, with only silence (< -80 dBFS)
    or a mute fade (|x| never above |continuation|) in between.
    """
    floor = 10.0 ** (SILENCE_DBFS / 20.0)
    n = _n(match_ms, rate)
    reach = _n(search_ms, rate)
    late = edit if late is None else late
    lead = next((i for i, v in enumerate(start) if abs(v) >= floor), None)
    if lead is not None and len(start) < lead + n:
        raise ValueError('start-of-load reference shorter than its silent lead plus match_ms')
    if lead is None and len(start) < n:
        raise ValueError('start-of-load reference shorter than match_ms')

    if lead is not None:
        level = rms(start[lead:lead + n])
    else:
        level = rms(continuation[max(0, edit - reach):late + reach])
        if level == 0:
            return Restart(None, None, 'start-of-load reference and continuation both silent')
    limit = level * 10.0 ** (DISTURB_DB / 20.0)

    span_hi = min(len(x), len(continuation), late + reach + n + (lead or 0))
    d = next((i for i in range(max(0, edit - reach), span_hi) if abs(x[i] - continuation[i]) > limit), None)
    if d is None:
        return Restart(False, None, 'no departure from the continuation near the edit')

    if lead is None:
        # The reset value is silence: only "went silent" is observable. A mute fade (never louder
        # than the continuation) may precede the silence, within the search reach.
        quiet = next((q for q in range(d, min(len(x) - n, d + reach) + 1)
                      if all(abs(v) < floor for v in x[q:q + n])), None)
        faded = quiet is not None and all(abs(v) < floor or abs(v) <= abs(c) + floor
                                          for v, c in zip(x[d:quiet], continuation[d:quiet]))
        if not faded:
            return Restart(False, None, 'departed without returning to the silent reset value')
        _, hi = window(x, rate, edit, late)
        if rms([a - b for a, b in zip(x[hi - n:hi], continuation[hi - n:hi])]) <= limit:
            return Restart(False, None, 'silent, then back on its continuation: not a reset')
        return Restart(None, d, 'silent reference: a reset to silence and a mute look the same')

    ref = list(start[:lead + n])
    m = len(ref)
    for at in range(max(0, edit - reach), min(len(x) - m, late + reach) + 1):
        # Between the departure and the repeat only silence or a mute fade (never louder than the
        # continuation) is allowed; anything else means later matches are displacements.
        if any(abs(v) >= floor and abs(v) > abs(c) + floor for v, c in zip(x[d:at], continuation[d:at])):
            break
        seg = x[at:at + m]
        if rms([a - b for a, b in zip(seg, ref)]) <= limit and \
                rms([a - b for a, b in zip(seg, continuation[at:at + m])]) > limit:
            return Restart(True, at, 'repeats start-of-load from where it leaves its continuation')
    return Restart(False, None, 'no start-of-load repeat beginning at the departure')
