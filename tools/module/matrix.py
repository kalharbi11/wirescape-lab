# SPDX-License-Identifier: GPL-3.0-only
"""MT2 deterministic matrix driver: runner emits neutral JSON lines, Python words diagnostics."""
from __future__ import annotations

import json
import subprocess

from build import build, run_command

TESTS = tuple(f"T{i}" for i in range(1, 14))
REPORT_ONLY = frozenset(("T10", "T13"))


def emit(report, messages, code, status, where, detail="", metrics=None):
    template = messages[code]
    report["results"].append({
        "test": code, "status": status,
        "what": template["what"] + (": " + detail if detail else ""),
        "where": where, "fix": template["fix"],
        "metrics": metrics if metrics is not None else {},
    })


def run(root, folder, layout, messages, args, report):
    state = build(root, folder, layout, args.keep_build)
    where = {"file": "module.cpp"}
    if state["state"] == "unsupported":
        emit(report, messages, "BUILD", "skip", where, "build_unsupported: " + state["detail"])
        for test in TESTS:
            emit(report, messages, test, "skip", {"reason": "build_unsupported"})
        return 0
    if state["state"] in ("environment", "build"):
        code = "ENV" if state["state"] == "environment" else "BUILD"
        emit(report, messages, code, "fail", where, state["detail"])
        return 4 if code == "ENV" else 3
    try:
        description = run_command([str(state["runner"]), "describe"], timeout=30)
        descriptor = json.loads(description.stdout)
        if not isinstance(descriptor, dict) or not isinstance(descriptor.get("id"), str):
            raise ValueError("describe payload invalid")
        report["module"]["id"] = descriptor["id"]
        command = [str(state["runner"]), "matrix"]
        if args.full:
            command.append("--full")
        try:
            stock_key = folder.relative_to(root).as_posix()
        except ValueError:
            stock_key = ""
        configuration = layout.get("stock", {}).get(stock_key, {}).get("config_bytes", [])
        if configuration:
            command.extend(("--config", ",".join(str(v) for v in configuration)))
        completed = run_command(command, timeout=240)
    except (OSError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError) as exc:
        emit(report, messages, "BUILD", "fail", where,
             "matrix or describe invocation failed: " + type(exc).__name__)
        return 3
    if completed.returncode != 0:
        emit(report, messages, "BUILD", "fail", where,
             "matrix runner returned " + str(completed.returncode))
        return 3
    try:
        records = [json.loads(line) for line in completed.stdout.splitlines()]
        if not records:
            raise ValueError("matrix produced no test results")
        seen = set()
        for record in records:
            code = record["test"]
            status = record["status"]
            context = record["where"]
            metrics = record["metrics"]
            detail = record["detail"]
            if (code not in TESTS or status not in ("pass", "fail", "warn", "skip")
                    or not isinstance(context, dict) or not context
                    or not isinstance(metrics, dict) or not isinstance(detail, str)
                    or not isinstance(code, str)):
                raise ValueError("malformed matrix record")
            if code in REPORT_ONLY and status == "fail":
                raise ValueError("report-only matrix test cannot fail")
            if status in ("fail", "warn") and not detail:
                raise ValueError("matrix diagnostic is empty")
            seen.add(code)
            emit(report, messages, code, status, context, detail, metrics)
        if "T1" not in seen:
            raise ValueError("required matrix tests absent")
        # Quick must include T1-T9 and T11, full must include every test.
        required = set(TESTS) if args.full else set(TESTS) - {"T10", "T12", "T13"}
        if not required.issubset(seen):
            # A malformed descriptor legitimately prevents further execution.
            if not any(r["test"] == "T1" and r["status"] == "fail" for r in records):
                raise ValueError("matrix truncated")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        report["results"].clear()
        emit(report, messages, "BUILD", "fail", where,
             "invalid matrix JSON: " + type(exc).__name__)
        return 3
    if any(r["status"] == "fail" and r["test"] not in REPORT_ONLY
           for r in report["results"]):
        return 1
    if args.strict and any(r["status"] == "warn" and r["test"] not in REPORT_ONLY
                           for r in report["results"]):
        return 1
    return 0
