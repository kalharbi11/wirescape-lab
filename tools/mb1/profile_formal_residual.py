# SPDX-License-Identifier: GPL-3.0-only
"""A119 diagnostic only: same runner, build and exact collector arguments as M1."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from profile_wrapper_codegen import ROOT, run, costs, delta_rows
from check_wrapper_isolation import wrapper_cost

PROBES = (("essentials.output", 1), ("essentials.output", 8),
          ("sequencing.groove", 1), ("sequencing.groove", 8))

# Execute in each pinned worktree: import its own unmodified formal collector.
COLLECT = """
import sys
from pathlib import Path
from bench.gate.instructions import RATE, FRAMES, COUNTS, binary, callgrind
ident, voices, length, output, vg = sys.argv[1:]
voices, length = int(voices), int(length)
assert (RATE, FRAMES, COUNTS) == (48000, 128, (12, 24))
duration = length * FRAMES / RATE
probe = binary(Path("build/native"), "abi2_module_cpu_probe")
expected = dict(module=ident, channels=voices, instances=1, sample_rate=RATE,
                block=FRAMES, blocks=length, seconds=duration)
print(callgrind([probe, "--module", ident, "--rate", RATE, "--block", FRAMES,
                 "--channels", voices, "--instances", 1, "--seconds", duration],
                Path(output), vg, expected_probe=expected))
"""


def measure(root, folder, ident, voices, vg):
    samples = []
    for n in (12, 24):
        raw = folder / f"{ident}-{voices}-{n}.callgrind"
        official = int(run([sys.executable, "-c", COLLECT, ident, voices, n, raw, vg],
                           root, capture=True, timeout=100).stdout.strip())
        total, functions, lines = costs(raw, root)
        name, wrapper = wrapper_cost(raw, n)
        if total != official or total != sum(functions.values()) or total != sum(lines.values()):
            raise ValueError(f"unattributed Ir: {ident}/{voices}/{n} formal={official} "
                             f"summary={total} function={sum(functions.values())} line={sum(lines.values())}")
        samples.append((total, functions, lines, name, wrapper))
        raw.unlink()
    a, b = samples
    if a[3] != b[3] or b[0] <= a[0]:
        raise ValueError("invalid length pair")
    b[1].subtract(a[1])
    b[2].subtract(a[2])
    return b[0] - a[0], b[1], b[2], b[4] - a[4], [a[0], b[0]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true" or sys.platform != "linux":
        parser.error("requires paired Linux Actions runner")
    if any(os.environ.get(k) != "-g" for k in ("CFLAGS", "CXXFLAGS")):
        parser.error("wrong paired compiler flags")
    if os.environ.get("CMAKE_BUILD_PARALLEL_LEVEL") != "2":
        parser.error("wrong paired build parallelism")
    output = args.output.resolve()
    if run(["git", "rev-parse", "HEAD"], ROOT, capture=True).stdout.strip() != args.head:
        raise ValueError("head pin mismatch")
    vg = shutil.which("valgrind")
    if not vg:
        raise ValueError("valgrind missing")
    provenance = {name: run(command, capture=True).stdout.splitlines()[0]
                  for name, command in (("compiler", ["c++", "--version"]),
                                        ("cmake", ["cmake", "--version"]),
                                        ("valgrind", [vg, "--version"]))}
    report = dict(base=args.base, head=args.head, machine=os.environ.get("MACHINE"),
                  provenance=provenance, method="formal exact collector self Ir", rows=[])
    with tempfile.TemporaryDirectory(prefix="ws-a119-") as tmp:
        folder = Path(tmp)
        base = folder / "base"
        run(["git", "worktree", "add", "--detach", base, args.base], ROOT)
        try:
            if run(["git", "rev-parse", "HEAD"], base, capture=True).stdout.strip() != args.base:
                raise ValueError("base pin mismatch")
            query = base / "build/native/.cmake/api/v1/query/codemodel-v2"
            query.parent.mkdir(parents=True, exist_ok=True)
            query.touch()
            run([sys.executable, "tools/dev.py", "build", "--headless", "--config", "Release"],
                base, timeout=1500)
            # Head was already built by the A114 job, before any dummy mutation.
            for ident, voices in PROBES:
                a, af, al, aw, at = measure(base, folder, ident, voices, vg)
                b, bf, bl, bw, bt = measure(ROOT, folder, ident, voices, vg)
                row = dict(module=ident, voices=voices, base_ir=a/12, head_ir=b/12,
                           percent=100*(b-a)/a, base_totals=at, head_totals=bt,
                           base_wrapper_ir=aw/12, head_wrapper_ir=bw/12,
                           function_delta=delta_rows(af, bf, limit=len(af)+len(bf)),
                           source_line_delta=delta_rows(al, bl, limit=len(al)+len(bl)))
                report["rows"].append(row)
                output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
                print("A119_FORMAL " + json.dumps({**row,
                    "function_delta": row["function_delta"][:12],
                    "source_line_delta": row["source_line_delta"][:12]}, sort_keys=True), flush=True)
        finally:
            run(["git", "worktree", "remove", "--force", base], ROOT)


if __name__ == "__main__":
    main()
