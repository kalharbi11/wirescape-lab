# SPDX-License-Identifier: GPL-3.0-only
"""#722: device-free, frame-exact raw UMP renderer regression."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

RATE, FRAMES = 48000, 192
COUNTERS = ("faults", "late_events", "dropped_events", "ring_full_events",
            "stale_events", "arena_full_events")
WIDTHS = (1, 1, 1, 2, 2, 4, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4)


def midi(frame, *words, node=1):
    return {"frame": frame, "node": node, "type": "midi", "words": list(words)}


def verify_samples(wav):
    assert len(wav) == 44 + FRAMES * 8
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    assert struct.unpack_from("<HHI", wav, 20) == (3, 2, RATE)
    assert wav[36:40] == b"data"
    for frame, actual in enumerate(struct.iter_unpack("<ff", wav[44:])):
        gate = float(7 <= frame < 61 or 71 <= frame < 129)
        bend = 1.0 if 29 <= frame < 43 else -1.0 if 93 <= frame < 111 else 0.0
        assert actual == (gate, bend), (frame, actual, (gate, bend))


def main():
    render = Path(sys.argv[1]).resolve()
    patch = {
        "format": "wirescape.native.patch", "version": 2, "settings": {},
        "name": "UMP frame evidence",
        "modules": [{"id": 1, "module": "midi.to_cv", "version": 1,
                     "parameters": {"voice_count": 1}}],
        "connections": [],
        "outputs": [{"module": 1, "port": "gate", "bus_channel": 0},
                    {"module": 1, "port": "bend", "bus_channel": 1}],
    }
    events = [
        midi(7, 0x20903C64), midi(29, 0x20E07F7F), midi(43, 0x20E00040),
        midi(61, 0x20803C00), midi(71, 0x40903C00, 0xFFFF0000),
        midi(93, 0x40E00000, 0), midi(111, 0x40E00000, 0x80000000),
        midi(129, 0x40803C00, 0),
    ]
    with tempfile.TemporaryDirectory(prefix="wirescape-ump-") as folder:
        root = Path(folder)
        patch_path, script_path, wav_path = (root / name for name in
                                             ("patch.json", "events.json", "output.wav"))
        patch_path.write_text(json.dumps(patch), encoding="utf-8")

        def run(script, error=None, block=32):
            script_path.write_text(json.dumps(script), encoding="utf-8")
            wav_path.unlink(missing_ok=True)
            result = subprocess.run(
                [str(render), "--patch", str(patch_path), "--script", str(script_path),
                 "--out", str(wav_path), "--rate", str(RATE), "--block", str(block),
                 "--seconds", str(FRAMES / RATE), "--seed", "7"],
                capture_output=True, text=True, timeout=20)
            if error is not None:
                assert result.returncode != 0, (script, "unexpected acceptance")
                assert error in result.stderr, (script, result.stderr)
                assert not wav_path.exists(), script
                assert "render_metrics " not in result.stdout, script
                return None
            assert result.returncode == 0, result.stderr
            metrics = [json.loads(line[len("render_metrics "):])
                       for line in result.stdout.splitlines()
                       if line.startswith("render_metrics ")]
            assert metrics == [{key: 0 for key in COUNTERS}], metrics
            return wav_path.read_bytes()

        # Baseline proves the patch is loadable before the red-first MIDI assertion.
        silent = run([])
        assert all(sample == (0.0, 0.0)
                   for sample in struct.iter_unpack("<ff", silent[44:]))
        reference = run(events)
        verify_samples(reference)
        assert run(events) == reference
        for block in (17, 64):
            verify_samples(run(events, block=block))

        # The UMP type nibble determines the length, including reserved types.
        # This tests framing only; no DSP meaning is asserted for reserved types.
        run([midi(i, mt << 28, *([0] * (width - 1)))
             for i, (mt, width) in enumerate(enumerate(WIDTHS))])
        for mt, width in enumerate(WIDTHS):
            wrong = 2 if width == 1 else 1
            run([midi(0, mt << 28, *([0] * (wrong - 1)))], "UMP word count")
        for words in ([], [0] * 5, None, "0", {}):
            run([dict(midi(0), words=words)], "UMP words")
        for value in (True, 1.5, -1, 2**32, 2**64 - 1, "1"):
            run([midi(0, value)], "UMP word")
        run([{"frame": 0, "node": 1, "type": "midi"}], "UMP words")
        run([midi(FRAMES, 0x20903C64)], "within duration")
        run([midi(10, 0x20903C64), midi(9, 0x20803C00)], "sorted")
        run([midi(0, 0x20903C64, node=999)], "MIDI target")
    print("#722 UMP framing and exact gate/bend samples passed")


if __name__ == "__main__":
    main()
