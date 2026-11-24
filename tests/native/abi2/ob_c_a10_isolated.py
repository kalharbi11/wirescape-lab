#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""A10/OB-c isolated SR8 execution adapter: no shared CMake or product edits.

Commands:
  build --build build/native --out build_reports/ob_c_a10
  extract --playwright-log build_reports/ob_c_a10/playwright.log --out build_reports/ob_c_a10/studio-trace.json
  execute --out build_reports/ob_c_a10

Uses production CMake compile/link commands for EXISTING fixture targets and
replaces only the isolated main test source and object/output. If original
targets or arguments are ambiguous, fail closed, never invent link flags.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve()
TASKS = {
    "ob_c_a10_audio_runner": {
        "target": "runtime_patch_tests",
        "original": "host/document/runtime_patch_tests.cpp",
        "source": "tests/native/abi2/ob_c_a10_audio_runner.cpp",
    },
    "ob_c_a10_groove": {
        "target": "abi2_host_keyboard_tests",
        "original": "modules/host_keyboard/tests.cpp",
        "source": "tests/native/abi2/ob_c_a10_groove.cpp",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(args: list[str], *, cwd: Path = ROOT, timeout: int = 180,
         required: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args, cwd=cwd, input="", capture_output=True, text=True,
        timeout=timeout, check=False)
    if required and result.returncode:
        raise RuntimeError("%s exited %d; stderr/stdout:\n%s" %
                           (args[0], result.returncode,
                            (result.stderr + result.stdout)[-7000:]))
    return result


def argv_of(row: dict) -> list[str]:
    if "arguments" in row:
        return list(row["arguments"])
    if "command" in row:
        return shlex.split(row["command"])
    raise ValueError("original CMake compile command is missing")


def link_argv(build: Path, target: str, original: str) -> list[str]:
    files = list(build.rglob("CMakeFiles/" + target + ".dir/link.txt"))
    if len(files) == 1:
        return shlex.split(files[0].read_text(encoding="utf-8"))
    if files or not (build / "build.ninja").is_file():
        raise ValueError("original production target Makefile/Ninja link is ambiguous")
    generated = call(["ninja", "-C", str(build), "-t", "commands", target])
    candidates = []
    for line in generated.stdout.splitlines():
        if original.rsplit("/", 1)[-1] + ".o" not in line:
            continue
        tokens = shlex.split(line)
        if tokens[:2] == [":", "&&"] and tokens[-2:] == ["&&", ":"]:
            tokens = tokens[2:-2]  # CMake's no-op wrappers, not link args.
        if tokens.count("-o") != 1:
            continue
        name = Path(tokens[tokens.index("-o") + 1]).name
        if name == target and not any(
                t in ("&&", "||", "|", ";") for t in tokens):
            candidates.append(tokens)
    if len(candidates) != 1:
        raise ValueError("expected exactly one CMake generated original link "
                         "for %s; got %d" % (target, len(candidates)))
    return candidates[0]


def build_fixture(build: Path, out: Path, task: str, records: list[dict]) -> dict:
    details = TASKS[task]
    original = details["original"]
    matches = [x for x in records if
               x["file"].replace("\\", "/").endswith("/" + original)]
    if len(matches) != 1:
        raise ValueError("expected one real production compile row for " + original)
    item = matches[0]
    compile_args = argv_of(item)
    source_matches = [i for i, value in enumerate(compile_args)
                      if value.replace("\\", "/").endswith("/" + original)]
    if len(source_matches) != 1 or compile_args.count("-o") != 1:
        raise ValueError("original compile source/object ambiguous: " + original)
    test_source = ROOT / details["source"]
    if not test_source.is_file():
        raise FileNotFoundError(str(test_source))
    obj = out / (task + ".cpp.o")
    compile_args[source_matches[0]] = str(test_source)
    compile_args[compile_args.index("-o") + 1] = str(obj)
    call(compile_args, cwd=Path(item["directory"]), timeout=240)
    if not obj.is_file():
        raise RuntimeError("compiled test object absent: " + task)
    link_args = link_argv(build, details["target"], original)
    old_basename = original.rsplit("/", 1)[-1] + ".o"
    original_objects = [i for i, value in enumerate(link_args)
                        if value.replace("\\", "/").endswith(old_basename)]
    if len(original_objects) != 1 or link_args.count("-o") != 1:
        raise ValueError("original production link source/object ambiguous: " + task)
    exe = out / task
    link_args[original_objects[0]] = str(obj)
    link_args[link_args.index("-o") + 1] = str(exe)
    call(link_args, cwd=build, timeout=240)
    if not exe.is_file():
        raise RuntimeError("original-library-linked executable missing: " + task)
    return {
        "exe": str(exe), "source": details["source"],
        "source_sha256": digest(test_source),
        "original_link_target": details["target"],
        "compiled_object_sha256": digest(obj),
        "executable_sha256": digest(exe),
        "compiler_invocation_sha256": hashlib.sha256(
            json.dumps(compile_args).encode()).hexdigest(),
        "link_invocation_sha256": hashlib.sha256(
            json.dumps(link_args).encode()).hexdigest(),
    }


def do_build(build: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    db = build / "compile_commands.json"
    if not db.is_file():
        raise FileNotFoundError("INFRA_A10: CMake compiler database absent")
    data = json.loads(db.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("INFRA_A10: invalid compiler database")
    result = {"source_sha": call(["git", "rev-parse", "HEAD"]).stdout.strip(),
              "build": str(build), "runners": {}}
    for task in TASKS:
        try:
            result["runners"][task] = build_fixture(build, out, task, data)
        except Exception as exc:
            result["runners"][task] = {"error": type(exc).__name__ + ": " + str(exc)}
            (out / "build-provenance.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n")
            raise
    (out / "build-provenance.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("OB-C-A10 ORIGINAL PRODUCTION FIXTURE BUILD " + json.dumps(
        result, sort_keys=True), flush=True)


def extract(log: Path, target: Path) -> None:
    text = log.read_text(encoding="utf-8", errors="replace")
    marker = "OB-C-A10-CADENCE-FACT "
    matches = [s.split(marker, 1)[1] for s in text.splitlines() if marker in s]
    if len(matches) != 1:
        raise ValueError("INFRA_A10: expected one actual Playwright gesture "
                         "trace, found %d" % len(matches))
    decoder = json.JSONDecoder()
    result, length = decoder.raw_decode(matches[0])
    gestures = result.get("gestures")
    if (result.get("real_sidecar_or_audio") is not False or
            result.get("delay_module_id") != 6 or
            not isinstance(gestures, list) or len(gestures) != 8):
        raise ValueError("INFRA_A10: invalid real Studio gesture output")
    ids = set()
    for gesture in gestures:
        key = (gesture["knob"], gesture["duration_nominal_ms"])
        ids.add(key)
        events = gesture["events"]
        if len(events) < 3 or any(
                e["moduleId"] != 6 or e["paramId"] != key[0] for e in events):
            raise ValueError("INFRA_A10: missing real matched setParam events")
        stamps = [e["t_ms"] for e in events]
        if min(stamps) < 0 or stamps != sorted(stamps):
            raise ValueError("INFRA_A10: nonmonotonic Studio gesture events")
    if ids != {(p, t) for p in ("time", "feedback", "tone", "mix")
               for t in (100, 1000)}:
        raise ValueError("INFRA_A10: missing duration/knob combinations")
    if "mode_division_record_only" not in result:
        raise ValueError("INFRA_A10: omitted record-only mode/division")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print("OB-C-A10-PLAYWRIGHT-TRACE " + json.dumps({
        "sha256": digest(target), "gestures": len(gestures),
        "events_total": sum(len(g["events"]) for g in gestures),
        "source": result.get("source"), "path": str(target),
        "remaining_log_suffix_chars": len(matches[0]) - length,
    }, sort_keys=True), flush=True)


def execute(out: Path) -> int:
    provenance = json.loads((out / "build-provenance.json").read_text())
    trace = out / "studio-trace.json"
    if not trace.is_file():
        raise FileNotFoundError("INFRA_A10: real Playwright gesture trace absent")
    sidecar = ROOT / "build/native/wirescape-engine"
    if not sidecar.is_file():
        raise FileNotFoundError("INFRA_A10: actual production sidecar missing")
    binaries = provenance["runners"]
    for name in TASKS:
        if not Path(binaries[name]["exe"]).is_file():
            raise FileNotFoundError("INFRA_A10: missing original linked " + name)
    env = os.environ.copy()
    env["WIRESCAPE_OB_C_SIDECAR"] = str(sidecar)
    env["WIRESCAPE_OB_C_AUDIO_RUNNER"] = binaries["ob_c_a10_audio_runner"]["exe"]
    env["WIRESCAPE_OB_C_STUDIO_TRACE"] = str(trace)
    env["WIRESCAPE_OB_C_PANIC_EVIDENCE"] = str(out / "panic")
    cases = [
        ("null-sink-panic-buffer-basics04",
         [sys.executable, "-m", "unittest", "discover", "-s", "tests/native/abi2",
          "-p", "ob_c_a10_capture_tests.py", "-v"]),
        ("exact-frame-scene-and-Studio-Echo",
         [sys.executable, "-m", "unittest", "discover", "-s", "tests/native/abi2",
          "-p", "ob_c_a10_click_tests.py", "-v"]),
        ("groove-internal",
         [binaries["ob_c_a10_groove"]["exe"], "internal"]),
        ("groove-external",
         [binaries["ob_c_a10_groove"]["exe"], "external"]),
        ("historical-MIDI-production-CTest",
         ["ctest", "--test-dir", str(ROOT / "build/native"),
          "-C", "Release", "-R", "^ob_c_midi_to_cv_audio$",
          "--output-on-failure"]),
    ]
    results = []
    for name, args in cases:
        print("OB-C-A10 CASE START " + name, flush=True)
        try:
            p = subprocess.run(args, cwd=ROOT, env=env, input="", text=True,
                               capture_output=True, timeout=900, check=False)
            merged = p.stdout + "\nSTDERR\n" + p.stderr
            code = p.returncode
        except Exception as exc:
            merged = "INFRA_A10 EXECUTION: " + type(exc).__name__ + ": " + str(exc)
            code = 255
        log = out / (name + ".log")
        log.write_text(merged, encoding="utf-8")
        print("OB-C-A10 CASE END name=%s exit=%d log=%s" %
              (name, code, log), flush=True)
        print(merged[-10000:], flush=True)
        xfail_marker = "OB-C-A10-STRICT-XFAIL P1_STARTUP_MASTER_FADE_VS_UNITY_PANIC "
        xfail_count = sum(line.startswith(xfail_marker) for line in merged.splitlines())
        strict_xfail = (name == "null-sink-panic-buffer-basics04" and
                        code == 0 and xfail_count == 1)
        if xfail_count and not strict_xfail and code == 0:
            code = 1  # Unexpected marker cannot turn another case green.
        results.append({"name": name, "exit_code": code,
                        "log": log.name, "log_sha256": digest(log),
                        "classification": ("strict-xfail" if strict_xfail else
                                           "pass" if code == 0 else "failure"),
                        "strict_xfail_applied": strict_xfail,
                        "strict_xfail_cause": ("P1_STARTUP_MASTER_FADE_VS_UNITY_PANIC"
                                               if strict_xfail else None)})
    summary = {"schema": "wirescape/ob-c-a10/sr8/1",
               "source_sha": provenance["source_sha"],
               "sidecar_sha256": digest(sidecar),
               "trace_sha256": digest(trace),
               "cases": results, "all_pass": all(r["exit_code"] == 0 for r in results),
               "buffer_wall_clock_ms": None,
               "buffer_wall_clock_reason": "null-sink b0/b1 are block counts, not independent wall time",
               "strict_xfail_applied": any(r["strict_xfail_applied"] for r in results)}
    (out / "execution-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return 0 if summary["all_pass"] else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--build", type=Path, default=ROOT / "build/native")
    b.add_argument("--out", type=Path, required=True)
    e = sub.add_parser("extract")
    e.add_argument("--playwright-log", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    x = sub.add_parser("execute")
    x.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.command == "build":
            do_build(args.build.resolve(), args.out.resolve())
        elif args.command == "extract":
            extract(args.playwright_log.resolve(), args.out.resolve())
        elif args.command == "execute":
            return execute(args.out.resolve())
        return 0
    except Exception as exc:
        print("INFRA_A10 isolated SR8 runner: %s: %s" %
              (type(exc).__name__, exc), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
