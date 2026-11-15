#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-off, architecture-specific Callgrind Ir per audio block.

Profiles five existing ABI2 cost modes, every bundled golden-render patch,
and each catalogued module at 1 and 8 probe voices (channels). Two lengths
are subtracted to remove fixed startup, patch-loading and module-init cost.
Audio devices, MIDI devices and LAN sockets are never opened.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
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
    if safe and not any(c in safe for c in ("/", "\\", ":\\", "/home/", "D:")):
        safe = safe[:120]
    else:
        safe = "probe did not complete"
    return f"exit {code}: {safe}"


def callgrind(command, output, valgrind, timeout=75):
    args = [valgrind, "--quiet", "--tool=callgrind", "--error-exitcode=77",
            "--callgrind-out-file=" + str(output), *map(str, command)]
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                timeout=timeout, stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(type(exc).__name__) from exc
    if result.returncode:
        raise RuntimeError(clean_reason(result.stderr, result.returncode))
    return read_ir(output)


def difference(command_for_length, valgrind, lengths=COUNTS):
    with tempfile.TemporaryDirectory(prefix="ws-ir-") as temp:
        totals = []
        for index, n in enumerate(lengths):
            out = Path(temp) / f"{index}.callgrind"
            totals.append(callgrind(command_for_length(n), out, valgrind))
    delta = totals[1] - totals[0]
    if delta <= 0:
        raise ValueError("nonpositive instruction difference")
    return {"ir_per_block": delta / (lengths[1] - lengths[0]), "totals": totals}


def modules():
    return sorted(line.strip() for line in MODULE_IDS.read_text(encoding="utf-8").splitlines()
                  if line.strip() and not line.startswith("#"))


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
                script.write_text(json.dumps(events, sort_keys=True), encoding="utf-8")
                seed = 37  # matches bench/golden/render.py
                def command(n):
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
                metrics = difference(command, valgrind)
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
    if len([r for r in rows if r["id"].startswith("fixed/")]) != 5:
        raise RuntimeError("five fixed cost modes required")
    if len([r for r in rows if r["id"].startswith("bundled/")]) < 24:
        raise RuntimeError("all 24 bundled golden patches required")
    if len([r for r in rows if r["id"].startswith("module/")]) != 2 * len(modules()):
        raise RuntimeError("one- and eight-voice rows required for every module")
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
