#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-off, architecture-specific Callgrind Ir per audio block.

Profiles five existing ABI2 cost modes, every bundled golden-render patch,
and 34 frozen Golden IDs plus the explicit experimental tier at 1 and 8 voices. Two lengths
are subtracted to remove fixed startup, patch-loading and module-init cost.
Audio devices, MIDI devices and LAN sockets are never opened.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.golden.render import events_for_patch, sources  # noqa: E402
from bench.golden.inventory import EXPERIMENTAL, allowed_ids  # noqa: E402
from tools.bench.abi2_cost import MODES, instructions as read_ir  # noqa: E402

RATE = 48000
FRAMES = 128
COUNTS = (12, 24)
SECONDS = tuple(n * FRAMES / RATE for n in COUNTS)
METHOD = "callgrind-Ir-two-length-difference-v1"
MODULE_IDS = ROOT / "tools/foundation/fixtures/known_module_ids.txt"


def binary(build, name):
    for p in (build / name, build / "Release" / name,
              build / "native" / name, build / "native" / "Release" / name):
        if p.is_file():
            return p.resolve()
    raise FileNotFoundError(f"missing {name}; build native headless Release first")


def clean_reason(stderr, code):
    # No raw host paths, user names, build paths or full Callgrind stderr in facts.
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    safe = next((line for line in reversed(lines)
                 if "failed" in line.lower() or "error" in line.lower()), "")
    if "create/prepare failed" in safe:
        safe = "module_cpu_probe: create/prepare failed"
    elif safe and not any(c in safe for c in ("/", "\\", ":\\", "/home/", "D:")):
        safe = safe[:120]
    else:
        safe = "probe did not complete"
    return f"exit {code}: {safe}"


# The native probe may report process failures and invalid output through its
# JSON faults count while exiting zero. Callgrind Ir is not a valid observation
# unless each of the two length-specific probe invocations reports healthy work.
MAX_PROBE_STDOUT = 4096


def verify_module_probe(stdout, expected):
    """Reject incomplete, foreign, malformed or faulty native probe evidence."""
    if not isinstance(stdout, str) or not 0 < len(stdout) <= MAX_PROBE_STDOUT:
        raise RuntimeError("module_cpu_probe: missing or oversized JSON evidence")
    line = stdout.strip()
    prefix = "module_cpu_probe "
    if not line.startswith(prefix) or len(line.splitlines()) != 1:
        raise RuntimeError("module_cpu_probe: missing or malformed JSON evidence")
    def unique_fields(pairs):
        fields = {}
        for name, value in pairs:
            if name in fields:
                raise ValueError("duplicate probe JSON field")
            fields[name] = value
        return fields

    def reject_nonfinite(_value):
        raise ValueError("nonfinite probe JSON value")

    try:
        payload = json.loads(line[len(prefix):], object_pairs_hook=unique_fields,
                             parse_constant=reject_nonfinite)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("module_cpu_probe: malformed JSON evidence") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("module_cpu_probe: JSON evidence is not an object")

    for name in ("module", "input_mode", "params", "alternate"):
        target = {"module": expected["module"], "input_mode": "normal",
                  "params": "", "alternate": ""}[name]
        if payload.get(name) != target or not isinstance(payload.get(name), str):
            raise RuntimeError(f"module_cpu_probe: incorrect {name} evidence")
    for name in ("instances", "channels", "blocks", "block", "sample_rate"):
        value = payload.get(name)
        if type(value) is not int or value != expected[name]:
            raise RuntimeError(f"module_cpu_probe: incorrect {name} evidence")
    seconds = payload.get("seconds")
    if (type(seconds) not in (int, float) or not math.isfinite(seconds)
            or not math.isclose(seconds, expected["seconds"], rel_tol=0,
                                abs_tol=1e-6)):
        raise RuntimeError("module_cpu_probe: incorrect seconds evidence")

    faults = payload.get("faults")
    if type(faults) is not int or faults < 0:
        raise RuntimeError("module_cpu_probe: invalid faults evidence")
    if faults:
        raise RuntimeError(f"module_cpu_probe: faults={faults}")
    # Check that the reported work/timing is well-formed; do not treat an
    # empty or truncated object with only faults=0 as a successful measurement.
    allocations = payload.get("allocations")
    times = payload.get("render_ns")
    if type(allocations) is not int or allocations < 0:
        raise RuntimeError("module_cpu_probe: invalid allocations evidence")
    if (not isinstance(times, dict)
            or any(type(times.get(k)) is not int or times[k] < 0
                   for k in ("max", "p99"))):
        raise RuntimeError("module_cpu_probe: invalid render timing evidence")
    for name in ("period_ns", "peak"):
        value = payload.get(name)
        if (type(value) not in (int, float) or not math.isfinite(value)
                or value < 0 or (name == "period_ns" and value == 0)):
            raise RuntimeError(f"module_cpu_probe: invalid {name} evidence")


def callgrind(command, output, valgrind, timeout=75, expected_probe=None):
    args = [valgrind, "--quiet", "--tool=callgrind", "--error-exitcode=77",
            "--callgrind-out-file=" + str(output), *map(str, command)]
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                timeout=timeout, stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(type(exc).__name__) from exc
    if result.returncode:
        raise RuntimeError(clean_reason(result.stderr, result.returncode))
    if expected_probe is not None:
        verify_module_probe(result.stdout, expected_probe)
    return read_ir(output)


def difference(command_for_length, valgrind, lengths=COUNTS, module_probe=None):
    with tempfile.TemporaryDirectory(prefix="ws-ir-") as temp:
        totals = []
        for index, n in enumerate(lengths):
            out = Path(temp) / f"{index}.callgrind"
            expected = None
            if module_probe is not None:
                expected = {**module_probe, "blocks": n,
                            "seconds": n * module_probe["block"] / module_probe["sample_rate"]}
            totals.append(callgrind(command_for_length(n), out, valgrind,
                                    expected_probe=expected))
    delta = totals[1] - totals[0]
    if delta <= 0:
        raise ValueError("nonpositive instruction difference")
    return {"ir_per_block": delta / (lengths[1] - lengths[0]), "totals": totals}


def modules():
    # Generated compatibility fixture contains the entire registered catalogue.
    fixture = [line.strip() for line in MODULE_IDS.read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.startswith("#")]
    osc_id = json.loads((ROOT / "modules/osc_out/module.json").read_text(encoding="utf-8"))["id"]
    catalogue = ROOT / "engine/control/module_catalog.inc"
    entries = sum(line.strip().startswith("WS_APP_MODULE(")
                  for line in catalogue.read_text(encoding="utf-8").splitlines())
    ids = fixture
    if (len(ids) != len(set(ids)) or set(ids) != allowed_ids(ROOT)
            or entries != len(ids) or osc_id != "osc.out"):
        raise ValueError(f"catalogue coverage mismatch: fixture={len(fixture)}, "
                         f"union={len(set(ids))}, native={entries}, osc={osc_id}")
    return sorted(ids)


def fixed_modes(build, valgrind):
    probe = binary(build, "abi2_cost_probe")
    rows = []
    for mode in MODES:
        key = "fixed/" + mode
        try:
            metrics = difference(
                lambda n: [probe, probe.parent, mode, n], valgrind, (10, 30))
            rows.append({"id": key, "status": "measured", "block_frames": 256, **metrics})
        except (RuntimeError, ValueError) as exc:
            rows.append({"id": key, "status": "unavailable", "reason": str(exc)})
    return rows


def patch_rows(build, valgrind):
    renderer = binary(build, "wirescape_render")
    rows = []
    patches = [(scope, path) for scope, path in sources() if scope == "bundled"]
    with tempfile.TemporaryDirectory(prefix="ws-gate-patches-") as temp:
        for scope, patch_path in patches:
            key = f"{scope}/{patch_path.name}"
            try:
                document = json.loads(patch_path.read_text(encoding="utf-8"))
                events = events_for_patch(document)
                script = Path(temp) / "events.json"
                seed = 37  # matches bench/golden/render.py
                def command(n):
                    # Renderer rejects events beyond its duration. Retain only
                    # golden-script events inside both short measurement windows.
                    events_in_window = [event for event in events if event["frame"] < n * FRAMES]
                    script.write_text(json.dumps(events_in_window, sort_keys=True),
                                      encoding="utf-8")
                    return [renderer, "--patch", patch_path.resolve(),
                            "--script", script, "--out", Path(temp) / "render.wav",
                            "--rate", RATE, "--block", FRAMES,
                            "--seconds", n * FRAMES / RATE, "--seed", seed]
                metrics = difference(command, valgrind)
                rows.append({"id": key, "status": "measured", "block_frames": FRAMES,
                             "scripted_note_count": len(events), **metrics})
            except (OSError, ValueError, RuntimeError, KeyError) as exc:
                rows.append({"id": key, "status": "unavailable", "reason": str(exc)[:160]})
    return rows


def module_rows(build, valgrind):
    probe = binary(build, "abi2_module_cpu_probe")
    rows = []
    for ident in modules():
        for voices in (1, 8):
            key = f"module/{ident}/voices{voices}"
            def command(n):
                return [probe, "--module", ident, "--rate", RATE,
                        "--block", FRAMES, "--channels", voices,
                        "--instances", 1, "--seconds", n * FRAMES / RATE]
            try:
                metrics = difference(command, valgrind, module_probe={
                    "module": ident, "channels": voices, "instances": 1,
                    "sample_rate": RATE, "block": FRAMES})
                rows.append({"id": key, "status": "measured", "block_frames": FRAMES,
                             "module": ident, "voices": voices, **metrics})
            except (RuntimeError, ValueError) as exc:
                rows.append({"id": key, "status": "unavailable", "module": ident,
                             "voices": voices, "reason": str(exc)[:160]})
    return rows


def release_build(build):
    env = dict(os.environ)
    env["CXXFLAGS"] = (env.get("CXXFLAGS", "") + " -g").strip()
    env["CFLAGS"] = (env.get("CFLAGS", "") + " -g").strip()
    env.setdefault("CMAKE_BUILD_PARALLEL_LEVEL", "2")
    # Release retains its optimizer flags; -g adds debug information.
    subprocess.run([sys.executable, str(ROOT / "tools/dev.py"), "build",
                    "--headless", "--config", "Release"],
                   cwd=ROOT, env=env, timeout=600, check=True)
    if not build.exists():
        raise RuntimeError("Release build directory absent")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--machine", choices=("linux-x64", "linux-arm64"), required=True)
    p.add_argument("--build-dir", type=Path, default=ROOT / "build/native")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--skip-build", action="store_true")
    args = p.parse_args(argv)
    actual = platform.machine().lower()
    expected = {"linux-x64": ("x86_64", "amd64"),
                "linux-arm64": ("aarch64", "arm64")}
    if platform.system() != "Linux" or actual not in expected[args.machine]:
        p.error("machine label must match the Linux host architecture")
    valgrind = shutil.which("valgrind")
    if not valgrind:
        p.error("valgrind/Callgrind required; no synthetic instruction counts")
    if not args.skip_build:
        release_build(args.build_dir)
    version = subprocess.run([valgrind, "--version"], text=True, capture_output=True,
                             check=True, timeout=10).stdout.strip()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                            capture_output=True, check=True, timeout=10).stdout.strip()
    started = time.monotonic()
    rows = fixed_modes(args.build_dir.resolve(), valgrind)
    rows.extend(patch_rows(args.build_dir.resolve(), valgrind))
    rows.extend(module_rows(args.build_dir.resolve(), valgrind))
    keys = [r["id"] for r in rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate instruction row ID")
    if len([r for r in rows if r["id"].startswith("fixed/")]) != 4:
        raise RuntimeError("four surviving fixed cost modes required")
    if len([r for r in rows if r["id"].startswith("bundled/")]) < 24:
        raise RuntimeError("all 24 bundled golden patches required")
    if len([r for r in rows if r["id"].startswith("module/")]) != 2*len(modules()):
        raise RuntimeError("one- and eight-voice rows required for every registered module")
    record = {
        "SPDX-License-Identifier": "GPL-3.0-only", "schema": 1,
        "commit": commit, "date_et": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine": args.machine, "architecture": actual,
        "valgrind_version": version, "method": METHOD, "configuration": "Release plus -g",
        "sample_rate_hz": RATE, "measurement_block_frames": FRAMES,
        "lengths_blocks": list(COUNTS),
        "note_source": "bench/golden/render.py events_for_patch; C4 on frame 0, off frame 240000",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                       allow_nan=False) + "\n", encoding="utf-8")
    unavailable = sum(r["status"] != "measured" for r in rows)
    print(f"Callgrind {args.machine}: {len(rows)-unavailable}/{len(rows)} measured "
          f"({unavailable} unavailable); {record['elapsed_seconds']}s profiling",
          flush=True)
    if any(r["status"] != "measured" for r in rows if r["id"].startswith(("fixed/", "bundled/"))):
        print("Required fixed or golden-rendered patch measurement unavailable", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
