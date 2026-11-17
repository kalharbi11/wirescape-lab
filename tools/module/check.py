# SPDX-License-Identifier: GPL-3.0-only
"""MT1 checks C1–C6; never downloads dependencies or opens devices."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from build import build, build_dir_for, clean_error, load_file, located, portable_symbols, run_command

SOURCE_SUFFIXES = frozenset((".h", ".hpp", ".hh", ".c", ".cc", ".cpp"))
REGISTRATION = re.compile(r"\bWS_REGISTER_MODULE\s*\(")
SPDX = re.compile(r"SPDX-License-Identifier:\s*(MIT|GPL-3\.0-only)\b")


def _no_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def emit(report: dict, messages: dict, code: str, status: str, where: dict,
         detail: str = "", metrics: dict | None = None) -> None:
    message = messages[code]
    report["results"].append({"test": code, "status": status,
                              "what": message["what"] + (": " + detail if detail else ""),
                              "where": where, "fix": message["fix"],
                              "metrics": metrics if metrics is not None else {}})


def _relative(folder: Path, path: Path) -> str:
    return path.relative_to(folder).as_posix()


def basic_checks(root: Path, folder: Path, layout: dict, messages: dict, report: dict) -> bool:
    source = (folder / "module.cpp").read_text(encoding="utf-8", errors="replace")
    n = len(REGISTRATION.findall(_no_comments(source)))
    if n != 1:
        emit(report, messages, "C1", "fail", {"file": "module.cpp"},
             f"found {n} registrations; exactly one is required")
    else:
        emit(report, messages, "C1", "pass", {"file": "module.cpp"})
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix in SOURCE_SUFFIXES)
    try:
        is_sdk = folder.is_relative_to(located(root, layout, "sdk"))
    except (OSError, ValueError):
        is_sdk = False
    required = "MIT" if is_sdk else "GPL-3.0-only"
    # External authors may use their own MIT or GPL license; tree-local files follow repository policy.
    in_tree = folder.is_relative_to(root)
    for file in files:
        snippet = "\n".join(file.read_text(encoding="utf-8", errors="replace").splitlines()[:8])
        match = SPDX.search(snippet)
        relative = _relative(folder, file)
        if not match or (in_tree and match.group(1) != required):
            emit(report, messages, "C2", "fail", {"file": relative},
                 "expected " + required if in_tree else "missing MIT or GPL-3.0-only SPDX comment")
        else:
            emit(report, messages, "C2", "pass", {"file": relative})
    if not files:
        emit(report, messages, "C2", "fail", {"file": "module.cpp"}, "no source files found")
    banned = load_file(located(root, layout, "banned_includes"), "wsmod_banned_includes")
    pattern = banned.PATTERN
    for file in files:
        if file.name == "tests.cpp":
            continue
        text = _no_comments(file.read_text(encoding="utf-8", errors="replace"))
        matches = list(pattern.finditer(text))
        for match in matches:
            emit(report, messages, "C3", "fail", {"file": _relative(folder, file),
                                                   "header": match.group(1)},
                 "banned include " + match.group(1))
    if not any(x["test"] == "C3" for x in report["results"]):
        emit(report, messages, "C3", "pass", {"folder": report["module"]["folder"]})
    return n == 1


def descriptor_check(root: Path, folder: Path, layout: dict, messages: dict,
                     args, report: dict) -> tuple[int | None, dict | None]:
    state = build(root, folder, layout, args.keep_build)
    where = {"file": "module.cpp"}
    if state["state"] == "unsupported":
        emit(report, messages, "BUILD", "skip", where, "build_unsupported: " + state["detail"])
        emit(report, messages, "C4", "skip", where, "descriptor not executed for unsupported build")
        return None, None
    if state["state"] in ("environment", "build"):
        kind = "ENV" if state["state"] == "environment" else "BUILD"
        emit(report, messages, kind, "fail", where, state["detail"])
        emit(report, messages, "C4", "skip", where, "cannot describe a module without a runner")
        return (4 if kind == "ENV" else 3), None
    try:
        output = run_command([str(state["runner"]), "describe"], timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        emit(report, messages, "C4", "fail", where, "describe invocation failed: " + type(exc).__name__)
        return 3, None
    if output.returncode not in (0, 1):
        emit(report, messages, "C4", "fail", where, "describe exited with code " + str(output.returncode))
        return 3, None
    try:
        payload = json.loads(output.stdout)
        if not isinstance(payload, dict):
            raise ValueError("describe output is not an object")
        if any(not isinstance(payload.get(key), expected) for key, expected in
               (("inputs", list), ("outputs", list), ("params", list), ("errors", list),
                ("id", str), ("name", str))):
            raise ValueError("describe payload lacks expected fields")
    except (json.JSONDecodeError, ValueError) as error:
        emit(report, messages, "C4", "fail", where, type(error).__name__ + " in describe JSON")
        return 3, None
    report["module"]["id"] = payload["id"]
    if payload["errors"] or output.returncode:
        emit(report, messages, "C4", "fail", {"descriptor": payload["id"]},
             "; ".join(str(e) for e in payload["errors"]) or "descriptor validation returned nonzero")
    else:
        emit(report, messages, "C4", "pass", {"descriptor": payload["id"]},
             metrics={"inputs": len(payload["inputs"]), "outputs": len(payload["outputs"]),
                      "params": len(payload["params"])})
    return None, payload


def metadata_check(folder: Path, messages: dict, report: dict, desc: dict | None) -> None:
    metadata = folder / "module.json"
    if not metadata.is_file():
        emit(report, messages, "C5", "skip", {"file": "module.json"},
             "optional transitional metadata absent")
        return
    try:
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("not an object")
    except (ValueError, OSError):
        emit(report, messages, "C5", "fail", {"file": "module.json"}, "malformed JSON object")
        return
    if desc is None:
        emit(report, messages, "C5", "skip", {"file": "module.json"},
             "descriptor unavailable; no unsafe equality claim")
        return
    differences = []
    for field in ("id", "name"):
        if payload.get(field) != desc[field]:
            differences.append(field)
    for field, descriptor_field in (("inputs", "inputs"), ("outputs", "outputs"),
                                     ("parameters", "params")):
        value = payload.get(field)
        expected = [p.get("id") for p in desc[descriptor_field]]
        if not isinstance(value, dict) or set(value) != set(expected):
            differences.append(field + " ids")
    if differences:
        emit(report, messages, "C5", "fail", {"file": "module.json"},
             "mismatching " + ", ".join(differences))
    else:
        emit(report, messages, "C5", "pass", {"file": "module.json"})


def advisory_check(root: Path, folder: Path, layout: dict, messages: dict,
                   args, report: dict) -> None:
    target = build_dir_for(root, folder, layout, args.keep_build) / "c6"
    metrics = portable_symbols(root, folder, layout, target)
    flags = metrics.get("symbols", {})
    symbol_count = sum(len(v) for v in flags.values())
    reasons = []
    if metrics["native"] != "compiled":
        reasons.append("native " + metrics["native"])
    if metrics["cross"] != "compiled":
        reasons.append("cross " + metrics["cross"])
    if symbol_count:
        reasons.append(str(symbol_count) + " classified undefined portable-tier symbols")
    emit(report, messages, "C6", "warn" if reasons else "pass",
         {"file": "module.cpp", "tier": "portable"},
         "; ".join(reasons), metrics)


def run(root: Path, folder: Path, layout: dict, messages: dict, args, report: dict) -> int:
    try:
        registration_ok = basic_checks(root, folder, layout, messages, report)
    except (OSError, ValueError, ImportError) as error:
        emit(report, messages, "ENV", "fail", {"file": "module.cpp"},
             "checker or source unavailable: " + type(error).__name__)
        return 4
    build_exit = None
    description = None
    if registration_ok:
        build_exit, description = descriptor_check(root, folder, layout, messages, args, report)
    else:
        emit(report, messages, "C4", "skip", {"file": "module.cpp"},
             "module registration invalid; cannot safely describe")
    metadata_check(folder, messages, report, description)
    advisory_check(root, folder, layout, messages, args, report)
    if build_exit is not None:
        return build_exit
    if any(r["status"] == "fail" for r in report["results"]):
        return 1
    # C6 is always advisory, even with --strict.
    if args.strict and any(r["status"] == "warn" and r["test"] != "C6"
                           for r in report["results"]):
        return 1
    return 0
