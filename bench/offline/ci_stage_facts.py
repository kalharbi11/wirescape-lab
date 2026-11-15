#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage device-free L2/L4 CI measurements as neutral, runner-scoped facts."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = {
    "repo": ("repo", "repo"),
    "tests": ("tests", "tests"),
    "protocol": ("protocol", "app"),
    "memory": ("memory", "app"),
    "ui": ("ui", "app"),
    "startup": ("startup", "app"),
}
DROP_KEYS = {"command", "stdout", "stderr", "stdout_tail", "stderr_tail",
             "log", "logs", "error", "cwd", "executable"}
BANNED_WORD = re.compile(r"\b(?:should|better|worse|good|bad)\b", re.I)
ABS_PATH = re.compile(r"(?<!\w)(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|opt|usr|var|mnt)/)[^\s\"']*")


def cpu_name():
    path = Path("/proc/cpuinfo")
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            if line.lower().startswith(("model name", "hardware", "cpu part")) and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or platform.machine()


def provenance(runner):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return {
        "commit": commit,
        "date_et": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine": {
            "runner": runner, "runner_os": os.getenv("RUNNER_OS", platform.system()),
            "runner_arch": os.getenv("RUNNER_ARCH", platform.machine()),
            "runner_image": os.getenv("ImageOS", "unavailable"),
            "runner_image_version": os.getenv("ImageVersion", "unavailable"),
            "cpu": cpu_name(), "os": platform.platform(),
            "audio_devices": "not accessed", "midi_devices": "not accessed",
            "lan_sockets": "not accessed"
        },
        "method": "GitHub Actions hosted runner; Python offline collectors"
    }


def clean(value):
    """Omit process logs and replace runner-specific absolute paths in facts."""
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in DROP_KEYS}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        result = value.replace(str(ROOT), "[checkout]")
        result = ABS_PATH.sub("[path]", result)
        return BANNED_WORD.sub("[word omitted]", result)
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def stage_collector(root, destination, name, section, meta, runner):
    source = root / name / "summary.json"
    path = destination / section / ("ci-" + runner) / (name + ".json")
    if source.is_file():
        try:
            doc = clean(json.loads(source.read_text(encoding="utf-8")))
            write_json(path, {"SPDX-License-Identifier": "GPL-3.0-only",
                              "provenance": meta, "source_collector": name, "measurements": doc})
            return "recorded"
        except (OSError, ValueError, TypeError) as exc:
            reason = type(exc).__name__
    else:
        reason = "collector output absent"
    write_json(path, {"SPDX-License-Identifier": "GPL-3.0-only",
                      "provenance": meta, "status": "unavailable", "reason": reason})
    return reason


def copy_tables(root, destination, runner, meta):
    source = root / "repo"
    dest = destination / "repo" / ("ci-" + runner)
    copied = []
    for pattern in ("*.csv", "cmake-targets.svg"):
        for original in sorted(source.glob(pattern)):
            # Tables are generated from tracked relative paths, not host paths.
            data = original.read_text(encoding="utf-8", errors="replace")
            if ABS_PATH.search(data) or BANNED_WORD.search(data):
                continue
            dest.mkdir(parents=True, exist_ok=True)
            (dest / original.name).write_text(data, encoding="utf-8")
            copied.append(original.name)
    write_json(dest / "table_inventory.json",
               {"SPDX-License-Identifier": "GPL-3.0-only", "provenance": meta,
                "copied_tables": copied, "source": "bench/offline/repo_facts.py"})


def stage_full(root, destination, runner, meta):
    copied = {}
    for section in ("perf", "dsp"):
        target = destination / section / ("ci-" + runner)
        files = list((root / section).glob("*.json"))
        for path in sorted(files):
            try:
                data = clean(json.loads(path.read_text(encoding="utf-8")))
                write_json(target / path.name, {"ci_provenance": meta, "measurements": data})
                copied[path.name] = "recorded"
            except (OSError, ValueError, TypeError) as exc:
                copied[path.name] = type(exc).__name__
        if not files:
            write_json(target / "unavailable.json",
                       {"SPDX-License-Identifier": "GPL-3.0-only", "provenance": meta,
                        "status": "unavailable",
                        "reason": "full benchmark output absent"})
    return copied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True, choices=["linux-x64", "linux-arm64", "windows-x64"])
    ap.add_argument("--input", type=Path, default=ROOT / "build_reports/l4")
    ap.add_argument("--output", type=Path, default=ROOT / ".facts-staged/facts")
    args = ap.parse_args()
    meta = provenance(args.runner)
    statuses = {}
    for name, (_, section) in SECTIONS.items():
        statuses[name] = stage_collector(args.input, args.output, name, section, meta, args.runner)
    copy_tables(args.input, args.output, args.runner, meta)
    statuses["l2"] = stage_full(args.input / "full", args.output, args.runner, meta)
    write_json(args.output / "tests" / ("ci-" + args.runner) / "run_manifest.json",
               {"SPDX-License-Identifier": "GPL-3.0-only", "provenance": meta,
                "sections": statuses})
    print(json.dumps(statuses, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
