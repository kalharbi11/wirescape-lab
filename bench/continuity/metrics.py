# SPDX-License-Identifier: GPL-3.0-only
"""The six edit-continuity metrics of proposals/0005 section 4, on one witness channel.

Every function takes the witness samples `x` (floats), the sample rate and `edit`, the sample
index where the edit was located (from the reply `gen` change and status stream; never assumed).
The analysis window is [edit - 100 ms, edit + 1 s). "Steady" quantities come from the 500 ms
before that window, [edit - 600 ms, edit - 100 ms), when the patch has settled after load.

Choices the section leaves open are named here and in DESIGN.md, not hidden:
- silence_ms counts consecutive samples with |x| below -80 dBFS (sample level, not RMS).
- dip_db uses a sliding 1 ms RMS (hop of one sample), relative to the steady RMS.
- time_slip_ms (tone) fits a sine of the known frequency over the 50 ms ending at the window
  start and over the last 50 ms of the window, and reports the phase difference from the
  extrapolated pre-edit fit as time, wrapped to half a period. Positive: the witness is late.
- time_slip_ms (clock) sets the grid from onsets before the edit and reports the largest-magnitude
  signed offset of the onsets inside the window after the edit.
- disturbed_ms is the span from the first to the last sample whose absolute difference from the
  continuation exceeds -60 dB relative to the steady RMS (sample level, so no frame smearing).
- restarted: the subject repeats its own start-of-load samples near the edit AND differs there
  from its no-edit continuation. A free-running periodic subject repeats its start every period,
  so a start match alone cannot distinguish a restart from continuing.
These functions report numbers only; nothing here decides pass or fail.
"""
from __future__ import annotations

import math
from typing import Sequence

PRE_MS = 100.0
POST_MS = 1000.0
STEADY_MS = 500.0
SILENCE_DBFS = -80.0
DISTURB_DB = -60.0


def _ms(n: int, rate: int) -> float:
    return 1000.0 * n / rate


def _n(ms: float, rate: int) -> int:
    return int(round(ms * rate / 1000.0))


def window(x: Sequence[float], rate: int, edit: int) -> tuple[int, int]:
    lo, hi = edit - _n(PRE_MS, rate), edit + _n(POST_MS, rate)
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
def silence_ms(x: Sequence[float], rate: int, edit: int) -> float:
    lo, hi = window(x, rate, edit)
    floor = 10.0 ** (SILENCE_DBFS / 20.0)
    best = run = 0
    for v in x[lo:hi]:
        run = run + 1 if abs(v) < floor else 0
        best = max(best, run)
    return _ms(best, rate)


# 2. dip_db
def dip_db(x: Sequence[float], rate: int, edit: int) -> float:
    lo, hi = window(x, rate, edit)
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


def time_slip_tone_ms(x: Sequence[float], rate: int, edit: int, freq: float) -> float:
    lo, hi = window(x, rate, edit)
    span = _n(50.0, rate)
    _, before = fit_sine(x[lo - span:lo], lo - span, freq, rate)
    _, after = fit_sine(x[hi - span:hi], hi - span, freq, rate)
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


def time_slip_clock_ms(x: Sequence[float], rate: int, edit: int, threshold: float) -> float:
    lo, hi = window(x, rate, edit)
    found = onsets(x[:hi], rate, threshold)
    before = [i for i in found if i < lo]
    after = [i for i in found if edit <= i < hi]
    if len(before) < 3:
        raise ValueError('fewer than three onsets before the window to set a grid')
    if not after:
        raise ValueError('no onsets after the edit inside the window')
    gaps = sorted(b - a for a, b in zip(before, before[1:]))
    period = gaps[len(gaps) // 2]
    anchor = before[-1]
    worst = 0.0
    for i in after:
        k = round((i - anchor) / period)
        off = i - (anchor + k * period)
        if abs(off) > abs(worst):
            worst = off
    return _ms(worst, rate) if worst >= 0 else -_ms(-worst, rate)


# 4. jump_ratio
def _max_step(x: Sequence[float]) -> float:
    return max((abs(b - a) for a, b in zip(x, x[1:])), default=0.0)


def jump_ratio(x: Sequence[float], rate: int, edit: int) -> float:
    lo, hi = window(x, rate, edit)
    s_lo, s_hi = steady(x, rate, edit)
    ref = _max_step(x[s_lo:s_hi])
    if ref == 0:
        raise ValueError('witness has no steady-state steps')
    return _max_step(x[lo:hi]) / ref


# 5. disturbed_ms
def disturbed_ms(x: Sequence[float], continuation: Sequence[float], rate: int, edit: int) -> float:
    """`continuation` is the same witness without the edit, sample-aligned with x (the fitted sine
    for the tone; a no-edit capture for tail and held note)."""
    lo, hi = window(x, rate, edit)
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
def restarted(x: Sequence[float], start: Sequence[float], continuation: Sequence[float], rate: int,
              edit: int, search_ms: float = 30.0, match_ms: float = 20.0) -> tuple[bool, int | None]:
    """Whether the subject, at some point within search_ms either side of the edit, repeats its own
    start-of-load samples `start` (the reset phase/envelope) to within -60 dB of their RMS over
    match_ms, while differing there from `continuation` (its sample-aligned no-edit continuation)
    by more than that. Returns (restarted, sample index of the restart or None)."""
    n = _n(match_ms, rate)
    ref = list(start[:n])
    if len(ref) < n:
        raise ValueError('start-of-load reference shorter than match_ms')
    level = rms(ref)
    if level == 0:
        raise ValueError('subject start-of-load reference is silent')
    limit = level * 10.0 ** (DISTURB_DB / 20.0)
    reach = _n(search_ms, rate)
    for at in range(max(0, edit - reach), min(len(x) - n, edit + reach) + 1):
        seg = x[at:at + n]
        if rms([a - b for a, b in zip(seg, ref)]) <= limit and \
                rms([a - b for a, b in zip(seg, continuation[at:at + n])]) > limit:
            return True, at
    return False, None
