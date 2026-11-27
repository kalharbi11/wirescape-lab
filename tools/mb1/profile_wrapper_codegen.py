# SPDX-License-Identifier: GPL-3.0-only
"""MB2 diagnostic: attribute the existing 12/24-block probe to function/source lines.

No gate changes. Exact pins in disposable hosted worktrees. Self costs exclude
call-edge costs; inlined source lines are also aggregated independently.
This is diagnostic output, not a replacement for the paired gate.
"""
from collections import Counter
from check_wrapper_isolation import wrapper_cost
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
RATE, FRAMES, LENGTHS = 48000, 128, (12, 24)
PROBES = (("essentials.vca", 1), ("essentials.vca", 8),
          ("essentials.lfo", 1), ("essentials.lfo", 8),
          ("essentials.function_envelope", 1), ("essentials.function_envelope", 8),
          ("midi.to_cv", 1), ("osc.out", 1))


def run(args, cwd=ROOT, env=None, capture=False, timeout=900):
    return subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True,
                          text=True, capture_output=capture, timeout=timeout)


def checkout(path, sha):
    if not re.fullmatch("[0-9a-f]{40}", sha):
        raise ValueError("full commit pin required")
    run(["git", "fetch", "--no-tags", "--depth=1", "origin", sha])
    run(["git", "worktree", "add", "--detach", path, sha])
    actual = run(["git", "rev-parse", "HEAD"], path, capture=True).stdout.strip()
    if actual != sha:
        raise ValueError("wrong checkout pin")


def build(path):
    env = dict(os.environ, CFLAGS="-g", CXXFLAGS="-g")
    out = path / "build/native"
    run(["cmake", "-S", path / "native", "-B", out, "-G", "Ninja",
         "-DCMAKE_BUILD_TYPE=Release"], path, env)
    run(["cmake", "--build", out, "--config", "Release", "--parallel", "2",
         "--target", "abi2_module_cpu_probe"], path, env)
    for binary in (out / "abi2_module_cpu_probe", out / "engine2/abi2_module_cpu_probe"):
        if binary.is_file():
            return binary
    raise FileNotFoundError("probe executable missing")


def source_name(path, root):
    # Strip the ephemeral checkout path. Do not publish host-specific paths.
    prefix = str(root) + "/"
    if path.startswith(prefix):
        return path[len(prefix):]
    if path.startswith("/"):
        return Path(path).name
    return path


def costs(path, root):
    functions, lines = Counter(), Counter()
    function = file = original = "unknown"
    edge = False
    total = None
    position = 0
    names = {"fn": {}, "fl": {}}

    def decode(value, kind):
        # A literal name can begin with "(anonymous namespace)" or
        # "(below main)"; only a numeric parenthesis is a string reference.
        m = re.fullmatch(r"\((\d+)\)(?: (.*))?", value)
        if not m:
            return value
        index, label = m.groups()
        if label is not None:
            names[kind][index] = label
        if index not in names[kind]:
            raise ValueError(f"undefined Callgrind {kind} reference {index}")
        return names[kind][index]
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("positions:") and raw.split()[1:] != ["line"]:
            raise ValueError("unexpected Callgrind positions")
        if raw.startswith("events:") and raw.split()[1:] != ["Ir"]:
            raise ValueError("unexpected Callgrind events")
        if raw.startswith("summary:"):
            total = int(raw.split()[1])
        elif raw.startswith(("fn=", "cfn=")):
            key, value = raw.split("=", 1)
            label = decode(value, "fn")
            if key == "fn":
                function = label
        elif raw.startswith(("fl=", "fi=", "fe=", "cfl=", "cfi=")):
            key, value = raw.split("=", 1)
            label = source_name(decode(value, "fl"), root) if value else original
            if key == "fl":
                original = file = label
            elif key in ("fi", "fe"):
                file = label
        elif raw.startswith("calls="):
            edge = True
        elif re.fullmatch(r"(?:\d+|[+-]\d+|\*)(?:\s+\d+)?", raw):
            fields = raw.split()
            token = fields[0]
            if token.startswith(("+", "-")):
                position += int(token)
            elif token != "*":
                position = int(token)
            ir = int(fields[1]) if len(fields) == 2 else 0
            if edge:
                edge = False
                continue
            functions[function] += ir
            lines[(file, position)] += ir
    if total is None or not functions:
        raise ValueError("missing Callgrind self costs/summary")
    return total, functions, lines


def measure(binary, root, folder, module, voices):
    totals, functions, lines, wrapper = [], [], [], []
    for n in LENGTHS:
        output = folder / f"{module}-{voices}-{n}.callgrind"
        duration = n * FRAMES / RATE
        p = run(["valgrind", "--quiet", "--tool=callgrind", "--error-exitcode=77",
                 "--compress-strings=no", "--compress-pos=no", "--dump-instr=no",
                 "--callgrind-out-file=" + str(output), binary,
                 "--module", module, "--rate", RATE, "--block", FRAMES,
                 "--channels", voices, "--instances", 1, "--seconds", duration],
                root, capture=True, timeout=120)
        prefix = "module_cpu_probe "
        if not p.stdout.strip().startswith(prefix):
            raise ValueError("missing probe record")
        row = json.loads(p.stdout.strip()[len(prefix):])
        expected = dict(module=module, channels=voices, instances=1, block=FRAMES,
                        sample_rate=RATE, blocks=n, faults=0, input_mode="normal",
                        params="", alternate="")
        if any(row.get(k) != v for k, v in expected.items()):
            raise ValueError(f"unexpected probe workload {row}")
        if abs(row["seconds"] - duration) > 1e-6:
            raise ValueError("unexpected duration")
        total, fn, line = costs(output, root)
        callback, ir = wrapper_cost(output, n)
        wrapper.append((callback, ir))
        totals.append(total)
        functions.append(fn)
        lines.append(line)
        output.unlink()
    functions[1].subtract(functions[0])
    lines[1].subtract(lines[0])
    if wrapper[0][0] != wrapper[1][0]:
        raise ValueError("wrapper callback identity changed between lengths")
    wrapper_ir = wrapper[1][1] - wrapper[0][1]
    if not 0 < wrapper_ir <= totals[1] - totals[0]:
        raise ValueError("wrapper inclusive Ir outside probe cost")
    return totals[1] - totals[0], functions[1], lines[1], wrapper_ir


def delta_rows(before, after, limit=12):
    changes = after.copy()
    changes.subtract(before)
    return [{"key": key, "before": before[key] / 12, "after": after[key] / 12,
             "delta": value / 12}
            for key, value in sorted(changes.items(), key=lambda kv: -abs(kv[1]))[:limit]
            if value]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--scratch-finite-noinline", action="store_true",
                        help="diagnostic only: change a single compiler attribute in disposable worktree")
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true" or sys.platform != "linux":
        parser.error("requires ephemeral Linux hosted runner")
    if not shutil.which("valgrind"):
        parser.error("Valgrind absent")
    print("MB2_PROFILE_PINS", args.base, args.head, flush=True)
    print(run(["c++", "--version"], capture=True).stdout.splitlines()[0], flush=True)
    print(run(["valgrind", "--version"], capture=True).stdout.strip(), flush=True)
    with tempfile.TemporaryDirectory(prefix="ws-mb2-profile-") as directory:
        scratch = Path(directory)
        base, head = scratch / "base", scratch / "head"
        worktrees = []
        try:
            for path, sha in ((base, args.base), (head, args.head)):
                checkout(path, sha)
                worktrees.append(path)
            baseline, subject = build(base), build(head)
            before, after = {}, {}
            for module, voices in PROBES:
                key = (module, voices)
                a, af, al, aw = before[key] = measure(baseline, base, scratch, module, voices)
                b, bf, bl, bw = after[key] = measure(subject, head, scratch, module, voices)
                report = dict(module=module, voices=voices, base_ir=a/12, head_ir=b/12,
                              percent=100*(b-a)/a, function_delta=delta_rows(af, bf),
                              source_line_delta=delta_rows(al, bl),
                              base_wrapper_ir=aw/12, head_wrapper_ir=bw/12,
                              base_unattributed_ir=(a-sum(af.values()))/12,
                              head_unattributed_ir=(b-sum(bf.values()))/12)
                print("MB2_PROFILE " + json.dumps(report, sort_keys=True), flush=True)
            if args.scratch_finite_noinline:
                header = head / "sdk/wirescape_sdk.h"
                original = header.read_bytes()
                declaration = b"inline bool finite_samples("
                if original.count(declaration) != 1:
                    raise ValueError("unexpected finite_samples declaration")
                try:
                    header.write_bytes(original.replace(
                        declaration, b"[[gnu::noinline]] " + declaration))
                    print("MB2_SCRATCH_TRIAL finite_samples GNU noinline attribute only; no committed SDK edit",
                          flush=True)
                    trial = build(head)
                    for (module, voices), (a, af, al, aw) in before.items():
                        b, bf, bl, bw = after[(module, voices)]
                        c, cf, cl, cw = measure(trial, head, scratch, module, voices)
                        report = dict(module=module, voices=voices,
                                      base_ir=a/12, fallback_ir=b/12, trial_ir=c/12,
                                      trial_vs_base_pct=100*(c-a)/a,
                                      trial_vs_fallback_pct=100*(c-b)/b,
                                      base_wrapper_ir=aw/12, fallback_wrapper_ir=bw/12,
                                      trial_wrapper_ir=cw/12,
                                      function_delta=delta_rows(af, cf),
                                      source_line_delta=delta_rows(al, cl),
                                      trial_unattributed_ir=(c-sum(cf.values()))/12)
                        print("MB2_FINITE_TRIAL " + json.dumps(report, sort_keys=True), flush=True)
                finally:
                    header.write_bytes(original)
        finally:
            for path in reversed(worktrees):
                run(["git", "worktree", "remove", "--force", path])


if __name__ == "__main__":
    main()
