# SPDX-License-Identifier: GPL-3.0-only
"""A120 repeat witness: five independent two-length Callgrind pairs per row.

Run on a Linux host with Valgrind and the Release module probe built.
This is a diagnostic, not a replacement for the paired gate.
Keep this harness stdlib-only: dev-run does not install Golden's NumPy stack.
"""
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.bench.abi2_cost import instructions  # noqa: E402

# Same workload as bench/gate/instructions.py module_rows; do not tune it.
RATE, FRAMES, COUNTS = 48000, 128, (12, 24)


def verify(stdout, ident, voices, blocks):
    prefix = "module_cpu_probe "
    lines = stdout.strip().splitlines()
    if len(lines) != 1 or not lines[0].startswith(prefix):
        raise RuntimeError("missing probe JSON")
    row = json.loads(lines[0][len(prefix):])
    expected = {"module": ident, "channels": voices, "blocks": blocks,
                "block": FRAMES, "sample_rate": RATE, "instances": 1,
                "input_mode": "normal", "params": "", "alternate": "",
                "faults": 0}
    for key, value in expected.items():
        if type(row.get(key)) is not type(value) or row[key] != value:
            raise RuntimeError(f"incorrect probe evidence: {key}")
    seconds = row["seconds"]
    if (type(seconds) not in (int, float) or not math.isclose(
            seconds, blocks * FRAMES / RATE, abs_tol=1e-6, rel_tol=0)):
        raise RuntimeError("incorrect seconds")
    for value in (row["allocations"], row["render_ns"]["max"],
                  row["render_ns"]["p99"]):
        if type(value) is not int or value < 0:
            raise RuntimeError("invalid allocation/timing evidence")
    for key in ("period_ns", "peak"):
        value = row[key]
        if (type(value) not in (int, float) or not math.isfinite(value)
                or value < 0 or (key == "period_ns" and value == 0)):
            raise RuntimeError(f"invalid probe evidence: {key}")
    return row


def pair(probe, valgrind, ident, voices):
    totals, evidence = [], []
    with tempfile.TemporaryDirectory(prefix="ws-ir-repeat-") as folder:
        for blocks in COUNTS:
            output = Path(folder) / f"{blocks}.callgrind"
            command = [valgrind, "--quiet", "--tool=callgrind",
                       "--error-exitcode=77", f"--callgrind-out-file={output}",
                       str(probe), "--module", ident, "--rate", str(RATE),
                       "--block", str(FRAMES), "--channels", str(voices),
                       "--instances", "1", "--seconds", str(blocks * FRAMES / RATE)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                    text=True, timeout=75, stdin=subprocess.DEVNULL)
            if result.returncode:
                raise RuntimeError(f"probe exit {result.returncode}: {result.stderr}")
            evidence.append(verify(result.stdout, ident, voices, blocks))
            totals.append(instructions(output))
    delta = totals[1] - totals[0]
    if delta <= 0:
        raise RuntimeError("nonpositive instruction difference")
    return {"totals": totals, "ir_per_block": delta / (COUNTS[1] - COUNTS[0]),
            "evidence": evidence}


def main():
    valgrind = shutil.which("valgrind")
    if not valgrind:
        raise RuntimeError("Valgrind is required")
    probe = ROOT / "build/native/abi2_module_cpu_probe"
    if not probe.is_file():
        raise FileNotFoundError("build the Release module CPU probe first")
    stable = True
    for ident, voices in (("osc.out", 8), ("essentials.output", 1)):
        pairs = [pair(probe, valgrind, ident, voices) for _ in range(5)]
        # Compare integer deltas, not rounded floating point displays.
        deltas = [row["totals"][1] - row["totals"][0] for row in pairs]
        identical = len(set(deltas)) == 1
        # The dev-run comment truncates long lines; keep the repeat table visible.
        print(json.dumps({"row": f"module/{ident}/voices{voices}",
                          "lengths": COUNTS, "deltas": deltas,
                          "identical": identical}), flush=True)
        print(json.dumps({"row": f"module/{ident}/voices{voices}",
                          "lengths": COUNTS, "pairs": pairs,
                          "deltas": deltas, "identical": identical}), flush=True)
        stable &= identical
    return 0 if stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
