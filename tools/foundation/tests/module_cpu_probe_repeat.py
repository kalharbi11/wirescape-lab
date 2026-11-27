# SPDX-License-Identifier: GPL-3.0-only
"""A120 repeat witness: five independent two-length Callgrind pairs per row.

Run on a Linux host with Valgrind and the Release module probe built.
This is a diagnostic, not a replacement for the paired gate.
"""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from bench.gate.instructions import binary, difference, RATE, FRAMES, COUNTS


def main():
    valgrind = shutil.which("valgrind")
    if not valgrind:
        raise RuntimeError("Valgrind is required")
    probe = binary(ROOT / "build/native", "abi2_module_cpu_probe")
    stable = True
    for ident, voices in (("osc.out", 8), ("essentials.output", 1)):
        def command(n):
            return [probe, "--module", ident, "--rate", RATE,
                    "--block", FRAMES, "--channels", voices,
                    "--instances", 1, "--seconds", n * FRAMES / RATE]

        pairs = [difference(command, valgrind, lengths=COUNTS, module_probe={
            "module": ident, "channels": voices, "instances": 1,
            "sample_rate": RATE, "block": FRAMES}) for _ in range(5)]
        # Compare integer deltas, not rounded floating point displays.
        deltas = [row["totals"][1] - row["totals"][0] for row in pairs]
        identical = len(set(deltas)) == 1
        print(json.dumps({"row": f"module/{ident}/voices{voices}",
                          "lengths": COUNTS, "pairs": pairs,
                          "deltas": deltas, "identical": identical}), flush=True)
        stable &= identical
    return 0 if stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
