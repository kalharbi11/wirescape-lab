# SPDX-License-Identifier: GPL-3.0-only
"""Reader for `--capture-null-sink` files (T0.13a, ENGINE_PROTOCOL section 9).

Layout (little-endian): one or more segments, each a 40-byte header
  magic "WSNSCAP1", u32 version=1, u32 header_bytes=40, u32 rate, u32 channels,
  u32 block, u32 segment index, u64 blocks (UINT64_MAX while still open)
followed by `blocks` blocks of block*channels float32, interleaved by frame.
A segment left open (engine killed) is read up to its last complete block.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

MAGIC = b'WSNSCAP1'
HEADER = struct.Struct('<8sIIIIIIQ')
OPEN_SEGMENT = 2**64 - 1


@dataclass
class Segment:
    index: int
    rate: int
    channels: int
    block: int
    closed: bool
    # One list of floats per bus channel, deinterleaved.
    data: list[list[float]] = field(default_factory=list)

    @property
    def blocks(self) -> int:
        return len(self.data[0]) // self.block if self.data and self.block else 0


def parse(raw: bytes) -> list[Segment]:
    segments: list[Segment] = []
    at = 0
    while at < len(raw):
        if len(raw) - at < HEADER.size:
            raise ValueError(f'truncated header at byte {at}')
        magic, version, header_bytes, rate, channels, block, index, blocks = HEADER.unpack_from(raw, at)
        if magic != MAGIC or version != 1 or header_bytes != HEADER.size:
            raise ValueError(f'bad segment header at byte {at}')
        if channels == 0 or block == 0 or rate == 0:
            raise ValueError(f'empty geometry at byte {at}')
        if index != len(segments):
            raise ValueError(f'segment index {index} out of order at byte {at}')
        at += header_bytes
        block_bytes = 4 * channels * block
        closed = blocks != OPEN_SEGMENT
        if closed:
            if len(raw) - at < blocks * block_bytes:
                raise ValueError(f'segment {index} shorter than its block count')
        else:
            blocks = (len(raw) - at) // block_bytes
        count = blocks * channels * block
        flat = struct.unpack_from(f'<{count}f', raw, at)
        at += blocks * block_bytes
        data = [list(flat[c::channels]) for c in range(channels)]
        segments.append(Segment(index, rate, channels, block, closed, data))
        if not closed:
            break  # an open segment is always the last one written
    return segments


def read(path: str | Path) -> list[Segment]:
    return parse(Path(path).read_bytes())


def encode(segments: list[Segment], leave_last_open: bool = False) -> bytes:
    """Test helper: the inverse of parse()."""
    out = bytearray()
    for n, seg in enumerate(segments):
        blocks = seg.blocks
        last_open = leave_last_open and n == len(segments) - 1
        out += HEADER.pack(MAGIC, 1, HEADER.size, seg.rate, seg.channels, seg.block, n,
                           OPEN_SEGMENT if last_open else blocks)
        frames = blocks * seg.block
        inter = [seg.data[c][i] for i in range(frames) for c in range(seg.channels)]
        out += struct.pack(f'<{len(inter)}f', *inter)
    return bytes(out)
