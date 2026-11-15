#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail Windows facts CI when required hosted measurements are only placeholders."""
import argparse
import json
from pathlib import Path


def document(folder, area, name):
    source = Path(folder) / area / "ci-windows-x64" / (name + ".json")
    if not source.is_file():
        raise ValueError("missing Windows fact file: " + str(source))
    return json.loads(source.read_text(encoding="utf-8"))["measurements"]


def verify(folder):
    tests = document(folder, "tests", "tests")
    for suite in ("ctest", "playwright_desktop"):
        result = tests["suites"][suite]["run"]
        if result.get("status") != "passed" or result.get("exit_code") != 0:
            raise ValueError(suite + " not passed: " + str(result.get("failure_output_lines", [])))
    memory = document(folder, "app", "memory")
    if not memory.get("engine_idle_rss_kib", 0) > 0:
        raise ValueError("Windows sidecar idle RSS absent")
    loaded = memory.get("largest_bundled_patch") or {}
    if not loaded.get("rss_kib", 0) > 0:
        raise ValueError("Windows sidecar loaded RSS absent")
    startup = document(folder, "app", "startup")
    if startup["summary"]["first_paint"]["n"] != 10:
        raise ValueError("Windows Electron first-paint sample count incomplete")
    if len(startup.get("runs", [])) != 10 or any(
        not (row.get("electron_idle", {}).get("rss_kib") or 0) > 0
        for row in startup["runs"]
    ):
        raise ValueError("Windows Electron RSS sample missing")
    dsp = document(folder, "dsp", "oscillators")
    if not any(r.get("status") == "measured" for r in dsp["rows"]):
        raise ValueError("Windows DSP oscillator measurements unavailable")
    cpu = document(folder, "perf", "module_cpu")
    if not any(r.get("status") == "measured" for r in cpu["rows"]):
        raise ValueError("Windows module CPU measurements unavailable")
    engine = document(folder, "perf", "engine_cpu")
    blocks = {r.get("block_frames") for r in engine["rows"]
              if r.get("status") == "measured"}
    if blocks != {64, 128, 256}:
        raise ValueError("Windows benchmark block-size measurements incomplete")
    return {"ctest": "passed", "playwright_desktop": "passed",
            "electron_startup_runs": len(startup["runs"]),
            "engine_rss_kib": memory["engine_idle_rss_kib"],
            "measured_dsp_rows": sum(r.get("status") == "measured" for r in dsp["rows"]),
            "measured_cpu_rows": sum(r.get("status") == "measured" for r in cpu["rows"]),
            "engine_blocks": sorted(blocks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.facts), sort_keys=True))


if __name__ == "__main__":
    main()
