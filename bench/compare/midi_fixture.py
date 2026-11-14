# SPDX-License-Identifier: GPL-3.0-only
"""Generate the same 60-second MIDI chord fixture for each tool; devices off."""
import argparse
import struct
from pathlib import Path

NOTES = (48, 52, 55, 60, 64, 67, 71, 72)
TICKS_PER_QUARTER = 480
TICKS_PER_SECOND = 960  # 120 beats/minute


def variable_length(value):
    if value < 0:
        raise ValueError("MIDI delta must be nonnegative")
    result = [value & 127]
    value >>= 7
    while value:
        result.insert(0, (value & 127) | 128)
        value >>= 7
    return bytes(result)


def fixture_bytes():
    # 15 repeated two-second chords, two seconds of silence between them.
    # Events are tick-addressed, without OS MIDI driver or device timers.
    events = [(0, -1, b"\xff\x51\x03\x07\xa1\x20")]  # 500000 us/quarter
    for cycle in range(15):
        start = cycle * 4 * TICKS_PER_SECOND
        end = start + 2 * TICKS_PER_SECOND
        for note in NOTES:
            events.append((start, 0, bytes((0x90, note, 100))))
            events.append((end, 1, bytes((0x80, note, 0))))
    events.append((60 * TICKS_PER_SECOND, 2, b"\xff\x2f\x00"))
    events.sort(key=lambda e: (e[0], e[1]))
    track = bytearray()
    last = 0
    for tick, _, data in events:
        track.extend(variable_length(tick - last))
        track.extend(data)
        last = tick
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_PER_QUARTER)
    return header + b"MTrk" + struct.pack(">I", len(track)) + track


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(fixture_bytes())
    print(args.out)


if __name__ == "__main__":
    main()
