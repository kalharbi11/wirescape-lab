# SPDX-License-Identifier: GPL-3.0-only
"""A69 synthetic native capture oracle; device off, no fabricated subject tone metrics."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture
import marks
import metrics

RATE = 48000
BLOCK = 256
REPEATS = 3
CASES = {"adopt": None, "ring": 960, "decline": 336, "cap": 24000}


def digest(path):
    return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read(path):
    segments = capture.read(path)
    assert len(segments) == 1, "one closed native segment required"
    s = segments[0]
    assert (s.rate, s.block, s.channels, s.closed) == (RATE, BLOCK, 3, True)
    assert all(math.isfinite(v) for ch in s.data for v in ch)
    mark_path = Path(str(path) + ".marks")
    return s, marks.read(mark_path), {"raw": digest(path), "marks": digest(mark_path)}


def oracle(case, path, ref_path):
    s, ms, raw = read(path)
    ref, ref_ms, raw_ref = read(ref_path)
    assert s.blocks == ref.blocks
    assert marks.locate(ms, "note").b0 == marks.locate(ref_ms, "note").b0 == 0
    assert not any(m.re == "edit" for m in ref_ms)
    mark = marks.locate(ms, "edit")
    assert mark.ok and mark.type == "replan"
    win = marks.edit_window(marks.Geometry.of([s]), mark)
    assert mark.b0 >= 200
    # Bus 1 is held/attack count for adopt, .75 witness for ring-out.
    # Bus 2 is an independent untouched Voice in both graphs.
    expected_witness = 1.0 if case == "adopt" else .75
    witness_rows = []
    for ch, expected in ((1, expected_witness), (2, .75)):
        a, b = metrics.paired_window(s.data[ch], ref.data[ch], RATE, win.edit, win.late)
        assert all(v == expected for v in a) and a == b, (case, ch)
        row = metrics.paired_levels(a, b, RATE)
        assert row["silence_ms"] == 0
        witness_rows.append({"channel": ch, "silence_ms": row["silence_ms"],
                             "paired_dip_db": row["dip_db"],
                             "paired_jump_ratio": metrics.paired_steps(a, b),
                             "identical": True})
    x, y = s.data[0], ref.data[0]
    _, hi = metrics.window(x, RATE, win.edit, win.late)
    if case == "adopt":
        residual = max(abs(v - (i+1)/65536.0) for i, v in enumerate(x[:hi]))
        assert residual < 2e-7 and x[:hi] == y[:hi], (case, residual)
        first = None
    else:
        assert all(v == .75 for v in y[:hi])
        first = next(i for i, v in enumerate(x[:hi]) if v != .75)
        assert win.edit <= first < win.late + BLOCK and first % BLOCK == 0
        fade = CASES[case]
        assert hi - first > fade
        residual = max(abs(x[i] - (.375 + 1.125*min(i-first+1, fade)/fade))
                       for i in range(first, hi))
        assert residual < 2e-6, (case, residual)
        assert all(v == .75 for v in x[:first])
    release = marks.locate(ms, "release")
    release_index = release.b0 * BLOCK
    assert release.ok and release_index >= hi
    if case == "adopt":
        assert all(v == 0 for v in s.data[1][release_index:])
    else:
        assert all(v == .375 for v in x[release_index:])
    return {"synthetic": True, "case": case, "mark": mark._asdict(),
            "witnesses": witness_rows, "subject_oracle_max_abs_error": residual,
            "first_divergent_sample": first, "fade_frames": CASES[case],
            "raw": raw, "control": raw_ref}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in CASES:
        for repeat in range(1, REPEATS + 1):
            pair = args.out / f"{case}-{repeat}"
            pair.mkdir(exist_ok=True)
            edited, control = pair / "edited.f32", pair / "control.f32"
            for kind, path in (("edited", edited), ("control", control)):
                subprocess.run([str(args.exe), case, kind, str(path)], check=True, timeout=30)
            rows.append(oracle(case, edited, control) | {"repeat": repeat})
    report = {"descriptor": "synthetic test descriptor (tests/native/abi2), not a stock module",
              "rate": RATE, "block": BLOCK, "repeats": REPEATS,
              "binary": digest(args.exe), "rows": rows}
    (args.out / "synthetic.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(f"verified {len(rows)} A69 synthetic capture pairs")


if __name__ == "__main__":
    main()
