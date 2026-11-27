# SPDX-License-Identifier: GPL-3.0-only
"""#747: note field validation, exact velocity and MIDI channel identity."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

RATE, FRAMES = 48000, 192


def note(frame, kind="noteOn", **fields):
    return dict(frame=frame, node=1, type=kind, key=60, **fields)


def main():
    render = Path(sys.argv[1]).resolve()
    baseline = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    patch = {
        "format": "wirescape.native.patch", "version": 2, "settings": {},
        "name": "Note field probe",
        "modules": [{"id": 1, "module": "host.keyboard", "version": 1,
                     "parameters": {"voices": 1}}],
        "connections": [],
        "outputs": [{"module": 1, "port": "gate", "bus_channel": 0},
                    {"module": 1, "port": "velocity", "bus_channel": 1}],
    }
    with tempfile.TemporaryDirectory(prefix="wirescape-note-fields-") as folder:
        root = Path(folder)
        patch_path, script_path, wav_path = (root / name for name in
                                             ("patch.json", "events.json", "out.wav"))

        def run(events, *, graph=patch, rate=RATE, block=32,
                seconds=FRAMES / RATE, seed=7, binary=render, error=None):
            patch_path.write_text(json.dumps(graph), encoding="utf-8")
            script_path.write_text(json.dumps(events), encoding="utf-8")
            wav_path.unlink(missing_ok=True)
            result = subprocess.run(
                [str(binary), "--patch", str(patch_path), "--script", str(script_path),
                 "--out", str(wav_path), "--rate", str(rate), "--block", str(block),
                 "--seconds", str(seconds), "--seed", str(seed)],
                capture_output=True, text=True, timeout=20)
            if error:
                assert result.returncode != 0, (events, "unexpected acceptance")
                assert error in result.stderr, (events, result.stderr)
                assert not wav_path.exists(), events
                return None
            assert result.returncode == 0, result.stderr
            return wav_path.read_bytes()

        def samples(data):
            assert len(data) == 44 + FRAMES * 8
            return list(struct.iter_unpack("<ff", data[44:]))

        # Record raw WAV digests before the red assertion, on both the
        # test-only and implementation heads, for an exact paired comparison.
        cases = sorted(Path(__file__).with_name("cases").glob("*.json"))
        assert cases, "missing render cases"
        for path in cases:
            case = json.loads(path.read_text(encoding="utf-8"))
            opts = dict(graph=case["patch"], rate=case["rate"], block=case["block"],
                        seconds=case["seconds"], seed=case["seed"])
            original = run(case["events"], **opts)
            print("baseline-wav", path.name, hashlib.sha256(original).hexdigest(), flush=True)
            explicit = [dict(e, velocity=1, channel=0)
                        if e["type"] in ("noteOn", "noteOff") else e
                        for e in case["events"]]
            assert original == run(explicit, **opts), path.name
            if baseline:
                assert original == run(case["events"], binary=baseline, **opts), path.name

        # Positive control: prove the existing production probe is loadable.
        default = samples(run([note(7), note(100, "noteOff")]))
        assert default[7] == (1.0, 1.0), default[7]
        assert default[100][0] == 0.0, default[100]

        # Every other channel sends a release of the same key and source.
        # Only channel 3 may close the note, proving exact channel identity
        # rather than merely agreement between the on and off mappings.
        events = [note(7, velocity=0.25, channel=3)]
        events += [note(10 + i * 4, "noteOff", channel=c, velocity=0.5)
                   for i, c in enumerate(ch for ch in range(16) if ch != 3)]
        events += [note(100, "noteOff", velocity=0.75, channel=3)]
        for block in (17, 32, 64):
            data = samples(run(events, block=block))
            for i, (gate, velocity) in enumerate(data):
                assert gate == float(7 <= i < 100), (i, gate, block)
                if 7 <= i < 100:
                    assert velocity == 0.25, (i, velocity, block)

        for kind in ("noteOn", "noteOff"):
            for value in (1.5, -0.01, "NaN", None, True, {}, [], "0.25"):
                run([note(7, kind, velocity=value)], error="velocity")
            for value in (16, -1, 2.5, 3.0, True, None, "3", {}, [], 2**64 - 1):
                run([note(7, kind, channel=value)], error="channel")
        for velocity in (0, 1):
            run([note(7, velocity=velocity, channel=15),
                 note(100, "noteOff", velocity=velocity, channel=15)])

    print("#747 exact note velocity/channel and validation passed")


if __name__ == "__main__":
    main()
