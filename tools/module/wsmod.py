# SPDX-License-Identifier: GPL-3.0-only
"""Standalone module check/test/render entry point (no downloads or devices)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wsmod", description=__doc__)
    parser.add_argument("command", choices=("check", "test", "render"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--keep-build", type=Path, default=None, metavar="DIR")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    layout = json.loads(Path(__file__).with_name("layout.json").read_text(encoding="utf-8"))
    messages = json.loads(Path(__file__).with_name("messages.json").read_text(encoding="utf-8"))
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                  text=True, capture_output=True, check=False, timeout=5)
        tool_commit = revision.stdout.strip() if revision.returncode == 0 else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        tool_commit = "unknown"
    folder = args.folder.resolve()
    try:
        folder_name = folder.relative_to(root).as_posix()
    except ValueError:
        folder_name = folder.name
    report = {"schema": "wsmod/1", "tool_commit": tool_commit, "abi": "ws2",
              "module": {"id": None, "folder": folder_name},
              "platform": platform.system().lower() + "-" + platform.machine().lower(),
              "mode": "full" if args.full else "quick", "results": [],
              "summary": {"pass": 0, "fail": 0, "warn": 0, "skip": 0}, "exit_code": 0}
    if not folder.is_dir() or not (folder / "module.cpp").is_file():
        m = messages["USAGE"]
        report["results"] = [{"test": "USAGE", "status": "fail", "what": m["what"],
                              "where": {"folder": folder_name}, "fix": m["fix"], "metrics": {}}]
        code = 2
    else:
        if args.command == "check":
            from check import run
        elif args.command == "test":
            from matrix import run
        else:
            from render import run
        code = run(root, folder, layout, messages, args, report)
    report["exit_code"] = code
    for result in report["results"]:
        report["summary"][result["status"]] += 1
    if args.as_json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    else:
        for r in report["results"]:
            where = ", ".join(f"{k}={v}" for k, v in sorted(r["where"].items()))
            print(f"{r['test']} {r['status'].upper()}: {r['what']} | WHERE {where} | FIX {r['fix']}")
        print(f"summary {report['summary']} exit={code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
