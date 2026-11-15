#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compare architecture-matched Callgrind instruction counts (Ir per audio block)."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def indexed(document):
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("missing rows array")
    found = {}
    for row in rows:
        key = row.get("id")
        if not isinstance(key, str) or not key or key in found:
            raise ValueError("missing or duplicate row id")
        found[key] = row
    if not found:
        raise ValueError("no instruction rows")
    return found


def compare(baseline, current, threshold=3.0):
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be finite and nonnegative")
    if baseline.get("schema") != 1 or current.get("schema") != 1:
        raise ValueError("unsupported instruction baseline schema")
    if baseline.get("machine") != current.get("machine"):
        raise ValueError("architecture/machine mismatch")
    if baseline.get("method") != current.get("method"):
        raise ValueError("measurement method mismatch")
    before, after = indexed(baseline), indexed(current)
    changes = []
    failures = []
    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key), after.get(key)
        if old is None or new is None:
            failures.append(f"{key}: missing {'baseline' if old is None else 'current'} row")
            continue
        if old.get("status") != "measured":
            # Previously unavailable cases are explicitly tracked, not synthesized.
            if new.get("status") == "measured":
                changes.append({"id": key, "percent": None, "status": "newly_measured"})
            else:
                changes.append({"id": key, "percent": None, "status": "unavailable"})
            continue
        if new.get("status") != "measured":
            failures.append(f"{key}: measurement regressed to {new.get('status')}")
            continue
        a, b = old.get("ir_per_block"), new.get("ir_per_block")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   and math.isfinite(v) and v > 0 for v in (a, b)):
            failures.append(f"{key}: nonpositive or nonfinite Ir value")
            continue
        percent = (b / a - 1.0) * 100.0
        changes.append({"id": key, "percent": percent, "status": "measured",
                        "baseline_ir": a, "current_ir": b})
        if percent - threshold > 1e-9:
            failures.append(f"{key}: +{percent:.2f}% > +{threshold:.2f}%")
    changes.sort(key=lambda r: abs(r["percent"]) if r["percent"] is not None else -1,
                 reverse=True)
    return changes, failures


def render(changes, failures, threshold, markdown=False):
    measured = sum(r["percent"] is not None for r in changes)
    if markdown:
        lines = [f"### Callgrind gate — threshold +{threshold:g}%",
                 f"Measured comparisons: {measured}; failures: {len(failures)}",
                 "| Graph | Δ Ir/block | Baseline Ir | Current Ir |",
                 "|---|---:|---:|---:|"]
        for r in changes[:10]:
            diff = "n/a" if r["percent"] is None else f"{r['percent']:+.2f}%"
            a = f"{r['baseline_ir']:.2f}" if "baseline_ir" in r else "—"
            b = f"{r['current_ir']:.2f}" if "current_ir" in r else "—"
            lines.append(f"| {r['id']} | {diff} | {a} | {b} |")
        if failures:
            lines.extend(["", "**Exceeded threshold / missing evidence:**"] +
                         ["- " + message for message in failures])
        return "\n".join(lines)
    lines = [f"Callgrind delta: {measured} measured rows; threshold +{threshold:g}%",
             "Ten largest absolute percentage changes:"]
    for r in changes[:10]:
        diff = "n/a" if r["percent"] is None else f"{r['percent']:+.2f}%"
        lines.append(f"  {r['id']}: {diff} ({r['status']})")
    lines.extend(f"FAIL: {message}" for message in failures)
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("current", type=Path)
    p.add_argument("--threshold", type=float, default=3.0)
    p.add_argument("--markdown", action="store_true")
    args = p.parse_args(argv)
    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        current = json.loads(args.current.read_text(encoding="utf-8"))
        changes, failures = compare(baseline, current, args.threshold)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Callgrind gate: {exc}", file=sys.stderr)
        return 2
    print(render(changes, failures, args.threshold, markdown=args.markdown))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
