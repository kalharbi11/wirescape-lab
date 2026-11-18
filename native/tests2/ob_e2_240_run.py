#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""#240 isolated Linux Lab adapter: compile one new smoke TU with EXACT
production module_cpu_probe CMake compile/link flags. No shared CMake edit.
Require existing native Release build + compile_commands.json export.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ROOT / "apps/studio/public/wirescape_modules.json"
CENSUS = ROOT / "facts/code/module_census.md"
CATALOG = ROOT / "native/control/module_catalog.inc"
SOURCE = ROOT / "native/tests2/ob_e2_240_smoke.cpp"
RATES = (44100, 48000)
BLOCKS = (64, 256)
EXPECTED_COUNT = 34


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv, cwd: Path, timeout=180, required=True):
    p = subprocess.run(argv, cwd=cwd, text=True, input="", capture_output=True,
                       check=False, timeout=timeout)
    if required and p.returncode:
        raise RuntimeError("%s exited %d: %s" %
                           (argv[0], p.returncode, (p.stdout + p.stderr)[-2400:]))
    return p


def live_ids() -> list[str]:
    doc = json.loads(PALETTE.read_text(encoding="utf-8"))
    ids = [item["id"] for item in doc["modules"]]
    actual = re.findall(r"^\|\s*\x60([^\x60]+)\x60\s*\|",
                        CENSUS.read_text(encoding="utf-8"), re.MULTILINE)
    native = re.findall(r"^WS_APP_MODULE\(([^)]+)\)\s*$",
                        CATALOG.read_text(encoding="utf-8"), re.MULTILINE)
    added = sorted(set(ids) - set(actual))
    removed = sorted(set(actual) - set(ids))
    if (len(ids) != EXPECTED_COUNT or len(actual) != EXPECTED_COUNT or
            len(native) != EXPECTED_COUNT or len(set(ids)) != len(ids) or
            len(set(actual)) != len(actual) or len(set(native)) != len(native) or
            added or removed):
        raise ValueError("live palette/census native registration mismatch: "
                         "live=%s census=%s native=%s added=%s removed=%s" %
                         (len(ids), len(actual), len(native), added, removed))
    return ids


def build_test(build: Path, temporary: Path) -> Path:
    path = build / "compile_commands.json"
    if not path.is_file():
        raise FileNotFoundError("no CMake compile_commands.json in existing native "
                                "Release build. Lead registration needs "
                                "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON.")
    records = json.loads(path.read_text(encoding="utf-8"))
    matches = [x for x in records if x["file"].replace("\\", "/").endswith(
               "/native/engine2/tests/module_cpu_probe.cpp")]
    if len(matches) != 1:
        raise ValueError("expected exactly one original module_cpu_probe compile row")
    row = matches[0]
    args = list(row["arguments"]) if "arguments" in row else shlex.split(row["command"])
    src = [i for i, x in enumerate(args) if x.replace("\\", "/").endswith(
           "/native/engine2/tests/module_cpu_probe.cpp")]
    if len(src) != 1 or args.count("-o") != 1:
        raise ValueError("cannot isolate original CPU probe compile source/object")
    obj = temporary / "ob_e2_240_smoke.cpp.o"
    args[src[0]] = str(SOURCE)
    args[args.index("-o") + 1] = str(obj)
    command(args, Path(row["directory"]), timeout=240)
    if not obj.is_file():
        raise RuntimeError("OB-e2 isolated C++ object absent after original compiler")

    links = list(build.rglob("CMakeFiles/abi2_module_cpu_probe.dir/link.txt"))
    if len(links) != 1:
        raise FileNotFoundError("native Release CPU probe link command absent/ambiguous")
    link = shlex.split(links[0].read_text(encoding="utf-8"))
    objects = [i for i, x in enumerate(link) if
               x.replace("\\", "/").endswith("module_cpu_probe.cpp.o")]
    if len(objects) != 1 or link.count("-o") != 1:
        raise ValueError("cannot isolate real original CPU probe link object/output")
    exe = temporary / "ob_e2_240_smoke"
    link[objects[0]] = str(obj)
    link[link.index("-o") + 1] = str(exe)
    command(link, build, timeout=240)
    if not exe.is_file():
        raise RuntimeError("OB-e2 production-linked executable missing")
    return exe


def parse_rows(output: str, ids: list[str]):
    rows = [json.loads(s[len("OBE2_ROW "):])
            for s in output.splitlines() if s.startswith("OBE2_ROW ")]
    totals = [json.loads(s[len("OBE2_TOTAL "):])
              for s in output.splitlines() if s.startswith("OBE2_TOTAL ")]
    required = {(m, r, b) for m in ids for r in RATES for b in BLOCKS}
    observed = [(x["id"], x["rate_hz"], x["block"]) for x in rows]
    if len(totals) != 1 or len(observed) != len(required) or (
            len(set(observed)) != len(observed) or set(observed) != required):
        raise ValueError("incomplete/repeated actual case matrix: missing=%s extra=%s" %
                         (sorted(required - set(observed)),
                          sorted(set(observed) - required)))
    for x in rows:
        if x["status"] == "pass" and (
                x["frames"] != x["rate_hz"] * 2 or
                x["render_allocations"] != 0 or x["engine_faults"] != 0 or
                x["swept_params"] != x["params"]):
            raise ValueError("false PASS violates actual smoke invariant: %s" % x)
        if x["status"] not in ("pass", "fail"):
            raise ValueError("unknown result may not count as pass")
    t = totals[0]
    if (t["palette_ids"] != EXPECTED_COUNT or
            t["native_ids"] != EXPECTED_COUNT or
            t["expected_cases"] != EXPECTED_COUNT * 4 or
            t["pass"] + t["fail"] != EXPECTED_COUNT * 4):
        raise ValueError("native test total disagrees with full 34×4 matrix")
    return rows, t


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / "build/native")
    parser.add_argument("--report", type=Path, default=ROOT /
                        "build_reports/ob_e2_240/smoke.json")
    parser.add_argument("--preflight-only", action="store_true",
                        help="read-only ID reconciliation, no native run or acceptance")
    args = parser.parse_args(argv)
    target = args.report.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "wirescape/ob-e2-240/1",
        "state": "not_executed", "system": platform.system(),
        "machine": platform.machine(), "cases": [],
        "inputs": {str(path.relative_to(ROOT)): digest(path)
                   for path in (SOURCE, PALETTE, CENSUS, CATALOG)},
    }
    try:
        result["git_head"] = command(["git", "rev-parse", "HEAD"], ROOT).stdout.strip()
        ids = live_ids()
        result["live_palette_ids"] = ids
        result["expected_cases"] = EXPECTED_COUNT * 4
        result["palette_census_reconciled"] = True
        if args.preflight_only:
            result["state"] = "manifest_preflight_only"
            print("OB-e2 palette preflight: 34 live IDs; 32 native + 2 examples; "
                  "native smoke NOT executed")
        else:
            with tempfile.TemporaryDirectory(prefix="wlab-ob-e2-240-") as td:
                temp = Path(td)
                manifest = temp / "live_palette_ids.txt"
                manifest.write_text("\n".join(ids) + "\n", encoding="utf-8")
                exe = build_test(args.build.resolve(), temp)
                capture = command([str(exe), str(manifest)], ROOT,
                                  timeout=900, required=False)
                raw = target.parent / "smoke.raw.log"
                raw.write_text(capture.stdout + "\nSTDERR\n" + capture.stderr,
                               encoding="utf-8")
                result["raw_log_sha256"] = digest(raw)
                result["native_exit_code"] = capture.returncode
                rows, totals = parse_rows(capture.stdout, ids)
                result["cases"], result["totals"] = rows, totals
                result["failures"] = [x for x in rows if x["status"] == "fail"]
                result["state"] = ("pass" if capture.returncode == 0 and
                                   not result["failures"] and
                                   totals["catalogue_match"] else "fail")
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        result["state"] = "blocked"
        result["blocking_step"] = type(exc).__name__ + ": " + str(exc)
    target.write_text(json.dumps(result, indent=2, sort_keys=True,
                                 allow_nan=False) + "\n", encoding="utf-8")
    print("OB-e2 result:", result["state"], "; report:", target)
    if result["state"] == "blocked":
        print(result["blocking_step"], file=sys.stderr)
    return 0 if result["state"] in ("pass", "manifest_preflight_only") else 1


if __name__ == "__main__":
    raise SystemExit(main())
