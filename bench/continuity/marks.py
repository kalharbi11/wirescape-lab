# SPDX-License-Identifier: GPL-3.0-only
"""Locating a command in a null-sink capture from its marks (ruling R7, QUESTIONS Q10/Q11).

With `--capture-null-sink <file>` the sidecar writes `<file>.marks`: one JSON line per handled
command with exactly the keys
  re (request id, string), type (string), ok (bool), gen (decimal string, gen after the command),
  b0, b1 (integers: the capture's TOTAL appended block count, over all segments, read just before
  the command is applied and just after its reply is built).
The command took effect no earlier than block b0 and no later than block b1 + 1.

Conventions chosen here (DESIGN.md "Locating the edit"):
- An effect lands on a block boundary, so in samples it lies in [start(b0), start(b1 + 1)].
  `edit` = start(b0) and `late` = start(b1 + 1) are the bracket edges passed to metrics.py.
- Bracket width is reported as `b1 + 1 - b0` blocks: the number of block boundaries after the
  earliest possible one at which the effect may have landed. It is at least 1.
- Window = [start(b0) - 100 ms, start(b1 + 1) + 1 s), the ruling's window.
- A total block index maps to (segment, sample offset in that segment) by walking the segments'
  `blocks` and `block`. Samples are counted on the concatenation of all segments. All segments
  must share one sample rate; ms are converted with it.
- First divergence from the no-edit capture is inside the bracket when it falls in blocks b0 to
  b1 + 1, i.e. samples [start(b0), start(b1 + 2)). Inside, it narrows the latest possible
  boundary to the start of the block holding it. Outside, it is a finding and is never used as
  the edit position.
- Two captures are aligned on one shared earlier command's marks (same request id in both
  scripts). Each mark is a bracket, so the block offset between the captures is known only to
  lie in [b0_a - (b1_b + 1), (b1_a + 1) - b0_b]; the reported offset is b0_a - b0_b and the
  uncertainty is that interval's width, width_a + width_b blocks.
Nothing here uses wall-clock time.
"""
from __future__ import annotations

import json
import math
from typing import NamedTuple, Sequence

KEYS = frozenset({'re', 'type', 'ok', 'gen', 'b0', 'b1'})
PRE_MS = 100.0
POST_MS = 1000.0


class Mark(NamedTuple):
    re: str | None    # None only on a refused request without a valid id
    type: str | None  # None only on a refused request without a valid type
    ok: bool
    gen: str
    b0: int
    b1: int

    @property
    def width(self) -> int:
        """Bracket width in blocks: b1 + 1 - b0."""
        return self.b1 + 1 - self.b0


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def parse(text: str) -> list[Mark]:
    """Parse and validate marks NDJSON. Refuses (ValueError) any line that is not a JSON object
    with exactly KEYS and their types, b0 > b1, negative counts, b0 decreasing in file order and
    a request id seen twice. A final newline is allowed; blank lines elsewhere are refused."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    out: list[Mark] = []
    seen: set[str] = set()
    for n, line in enumerate(lines, 1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f'line {n}: not JSON ({e.msg})') from None
        if not isinstance(obj, dict):
            raise ValueError(f'line {n}: not a JSON object')
        if set(obj) != KEYS:
            raise ValueError(f'line {n}: keys {sorted(obj)} are not exactly {sorted(KEYS)}')
        # The sidecar writes null re/type for a refused request that lacked a valid one.
        if not all(obj[k] is None or isinstance(obj[k], str) for k in ('re', 'type')):
            raise ValueError(f'line {n}: re and type must be strings or null')
        if obj['ok'] is True and (obj['re'] is None or obj['type'] is None):
            raise ValueError(f'line {n}: an accepted command must carry re and type')
        if not isinstance(obj['ok'], bool):
            raise ValueError(f'line {n}: ok must be a bool')
        gen = obj['gen']
        if not isinstance(gen, str) or not gen.isascii() or not gen.isdigit():
            raise ValueError(f'line {n}: gen must be a decimal string')
        b0, b1 = obj['b0'], obj['b1']
        if not _is_int(b0) or not _is_int(b1) or b0 < 0 or b1 < 0:
            raise ValueError(f'line {n}: b0 and b1 must be non-negative integers')
        if b0 > b1:
            raise ValueError(f'line {n}: b0 {b0} > b1 {b1}')
        if out and b0 < out[-1].b0:
            raise ValueError(f'line {n}: b0 {b0} before previous b0 {out[-1].b0}')
        if obj['re'] is not None:
            if obj['re'] in seen:
                raise ValueError(f'line {n}: request id {obj["re"]!r} repeated')
            seen.add(obj['re'])
        out.append(Mark(obj['re'], obj['type'], obj['ok'], gen, b0, b1))
    return out


def read(path) -> list[Mark]:
    with open(path, encoding='utf-8') as f:
        return parse(f.read())


def locate(marks: Sequence[Mark], re: str) -> Mark:
    """The mark (bracket) of request id `re`; KeyError if the command has no mark."""
    for mk in marks:
        if mk.re == re:
            return mk
    raise KeyError(f'no mark for request id {re!r}')


class Geometry(NamedTuple):
    """Per-segment (blocks, block) and the common rate; built from capture.Segment objects."""
    segments: tuple[tuple[int, int], ...]
    rate: int

    @classmethod
    def of(cls, segments) -> 'Geometry':
        if not segments:
            raise ValueError('capture has no segments')
        rates = {s.rate for s in segments}
        if len(rates) != 1:
            raise ValueError(f'segments have different rates {sorted(rates)}')
        return cls(tuple((s.blocks, s.block) for s in segments), rates.pop())

    @property
    def total_blocks(self) -> int:
        return sum(b for b, _ in self.segments)

    @property
    def total_samples(self) -> int:
        return sum(b * n for b, n in self.segments)


def block_position(geo: Geometry, total_block: int) -> tuple[int, int]:
    """(segment index, sample offset in that segment) of the start of total block `total_block`.
    The index one past the last block maps to the end of the last segment."""
    if total_block < 0 or total_block > geo.total_blocks:
        raise ValueError(f'block {total_block} outside capture of {geo.total_blocks} blocks')
    left = total_block
    for i, (blocks, block) in enumerate(geo.segments):
        if left < blocks:
            return i, left * block
        left -= blocks
    last = len(geo.segments) - 1
    return last, geo.segments[last][0] * geo.segments[last][1]


def block_sample(geo: Geometry, total_block: int) -> int:
    """Sample index, on the concatenation of all segments, where total block `total_block` starts."""
    seg, off = block_position(geo, total_block)
    return sum(b * n for b, n in geo.segments[:seg]) + off


def sample_block(geo: Geometry, sample: int) -> int:
    """Total block index holding concatenated sample `sample`."""
    if sample < 0 or sample >= geo.total_samples:
        raise ValueError(f'sample {sample} outside capture of {geo.total_samples} samples')
    blocks_before = 0
    for blocks, block in geo.segments:
        if sample < blocks * block:
            return blocks_before + sample // block
        sample -= blocks * block
        blocks_before += blocks
    raise AssertionError('unreachable')


class Window(NamedTuple):
    lo: int          # start(b0) - 100 ms
    hi: int          # start(b1 + 1) + 1 s, exclusive
    edit: int        # start(b0): earliest possible effect sample
    late: int        # start(b1 + 1): latest possible effect sample
    width_blocks: int


def edit_window(geo: Geometry, mark: Mark) -> Window:
    """The ruling's metric window for one mark, in concatenated samples. Refused (ValueError)
    when it does not fit inside the capture."""
    if mark.b1 + 1 > geo.total_blocks:
        raise ValueError(f'mark {mark.re!r} ends after the capture ({geo.total_blocks} blocks)')
    edit = block_sample(geo, mark.b0)
    late = block_sample(geo, mark.b1 + 1)
    lo = edit - int(round(PRE_MS * geo.rate / 1000.0))
    hi = late + int(round(POST_MS * geo.rate / 1000.0))
    if lo < 0 or hi > geo.total_samples:
        raise ValueError(f'window [{lo}, {hi}) outside capture of {geo.total_samples} samples')
    return Window(lo, hi, edit, late, mark.width)


def first_divergence(x: Sequence[float], ref: Sequence[float], lo: int, hi: int,
                     limit: float) -> int | None:
    """First sample index in [lo, hi) where |x - ref| > limit, or None. x and ref are aligned.
    A NaN in ref (padding from shift()) inside the range is refused: the captures do not overlap."""
    if lo < 0 or hi > len(x) or hi > len(ref):
        raise ValueError(f'range [{lo}, {hi}) outside the compared captures')
    for i in range(lo, hi):
        if ref[i] != ref[i]:
            raise ValueError(f'reference has no aligned sample at {i}')
        if abs(x[i] - ref[i]) > limit:
            return i
    return None


class Divergence(NamedTuple):
    sample: int | None      # first divergence, or None if x never left ref in the window
    inside: bool | None     # None when there is no divergence
    narrowed: tuple[int, int] | None  # (b0, block holding the divergence) when inside
    finding: str | None     # set when the divergence is outside the bracket


def place_divergence(geo: Geometry, mark: Mark, sample: int | None) -> Divergence:
    """Classify a first divergence against the mark's bracket (blocks b0 .. b1 + 1)."""
    if sample is None:
        return Divergence(None, None, None, None)
    blk = sample_block(geo, sample)
    if mark.b0 <= blk <= mark.b1 + 1:
        return Divergence(sample, True, (mark.b0, blk), None)
    where = 'before' if blk < mark.b0 else 'after'
    return Divergence(sample, False, None,
                      f'first divergence in block {blk}, {where} bracket [{mark.b0}, {mark.b1 + 1}] '
                      f'of {mark.re!r}; not used as the edit position')


class Alignment(NamedTuple):
    offset: int        # b0_a - b0_b: block k in B corresponds to block k + offset in A
    lo: int            # smallest offset the two brackets allow
    hi: int            # largest offset the two brackets allow
    uncertainty: int   # hi - lo, in blocks (= width_a + width_b)


def align_offset(marks_a: Sequence[Mark], marks_b: Sequence[Mark], shared_re: str) -> Alignment:
    """Block offset between captures A and B from one shared command's marks."""
    a, b = locate(marks_a, shared_re), locate(marks_b, shared_re)
    if a.type != b.type:
        raise ValueError(f'shared request {shared_re!r} is {a.type!r} in A, {b.type!r} in B')
    lo = a.b0 - (b.b1 + 1)
    hi = (a.b1 + 1) - b.b0
    return Alignment(a.b0 - b.b0, lo, hi, hi - lo)


def shift(ref: Sequence[float], by: int, fill: float = math.nan) -> list[float]:
    """ref moved later by `by` samples (earlier if negative), same length, padded with `fill`:
    with by = offset * block (both captures in one block size up to the window), sample i of the
    result lines up with sample i of capture A."""
    n = len(ref)
    if by >= 0:
        return [fill] * min(by, n) + list(ref[:max(0, n - by)])
    return list(ref[-by:]) + [fill] * min(-by, n)
