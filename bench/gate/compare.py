#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compare architecture-matched Callgrind instruction counts (Ir per audio block)."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from bench.golden.inventory import EXPERIMENTAL, golden_ids  # noqa: E402

def experimental_row_ids():
    return {f"module/{m}/voices{voices}" for m in EXPERIMENTAL for voices in (1, 8)}


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


def expected_ids(root=None):
    """Only the 96 frozen Golden/canonical rows, never experimental heads."""
    root = Path(root) if root is not None else ROOT
    modules = golden_ids(root)
    patches = sorted((root / "apps/studio/patches").glob("*.json"))
    if len(modules) != 34 or len(patches) != 24:
        raise ValueError(f"unexpected Golden coverage: {len(modules)} modules, {len(patches)} patches")
    modes = ("abi2_mono", "abi2_modulated", "abi2_poly8", "abi2_quad_vca_lpg8")
    return ({f"fixed/{m}" for m in modes}
            | {f"bundled/{p.name}" for p in patches}
            | {f"module/{m}/voices{v}" for m in modules for v in (1, 8)})


def valid_measured_row(row, verify_totals):
    ir = row.get("ir_per_block")
    if (not isinstance(ir, (int, float)) or isinstance(ir, bool)
            or not math.isfinite(ir) or ir <= 0):
        return False
    if verify_totals:
        totals = row.get("totals")
        if (not isinstance(totals, list) or len(totals) != 2
                or any(not isinstance(t, int) or isinstance(t, bool) or t < 0
                       for t in totals) or totals[1] <= totals[0]):
            return False
        blocks = 20 if row["id"].startswith("fixed/") else 12
        if not math.isclose(ir, (totals[1] - totals[0]) / blocks,
                            rel_tol=1e-12, abs_tol=0):
            return False
    return True


def compare(baseline, current, threshold=3.0, required_ids=None,
            verify_totals=False):
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be finite and nonnegative")
    if baseline.get("schema") != 1 or current.get("schema") != 1:
        raise ValueError("unsupported instruction baseline schema")
    if baseline.get("machine") != current.get("machine"):
        raise ValueError("architecture/machine mismatch")
    if baseline.get("method") != current.get("method"):
        raise ValueError("measurement method mismatch")
    if (baseline.get("valgrind_version") or current.get("valgrind_version")) and (
            baseline.get("valgrind_version") != current.get("valgrind_version")):
        raise ValueError("Valgrind version mismatch")
    before, after = indexed(baseline), indexed(current)
    changes = []
    failures = []
    # Exactly one historic base row is retired by S4; all surviving 96 IDs
    # still compare normally. Retired is a disclosed status, never a pass/zero.
    retired = "fixed/abi1_mono"
    if required_ids is not None and retired not in required_ids:
        old = before.pop(retired, None)
        new = after.pop(retired, None)
        if old is not None:
            if old.get("status") != "measured" or not valid_measured_row(old, verify_totals):
                failures.append(f"{retired}: invalid historic retired measurement")
            changes.append({"id": retired, "percent": None, "status": "retired"})
        if new is not None:
            failures.append(f"{retired}: retired metric must not appear in current evidence")
    experimental = experimental_row_ids() if required_ids is not None else set()
    required = set(required_ids) if required_ids is not None else set()
    for key in sorted(before.keys() | after.keys() | required):
        old, new = before.get(key), after.get(key)
        if key in experimental and key not in required and old is None and new is not None:
            # Validated head-only measurements cannot be compared to a nonexistent base.
            if new.get("status") == "measured" and valid_measured_row(new, verify_totals):
                changes.append({"id": key, "percent": None, "status": "new", "current_ir": new["ir_per_block"]})
            elif new.get("status") == "unavailable":
                changes.append({"id": key, "percent": None, "status": "new",
                                "measurement_status": "unavailable", "reason": new.get("reason", "no numeric Ir")})
            else:
                failures.append(f"{key}: invalid new experimental instruction evidence")
            continue
        if old is None or new is None:
            failures.append(f"{key}: missing {'baseline' if old is None else 'current'} row")
            continue
        if old.get("status") != "measured":
            # Incomplete baseline coverage is a gate failure, even if the
            # current probe is still unavailable or has newly recovered.
            # Do not silently treat missing measurements as zero regression.
            failures.append(f"{key}: baseline {old.get('status')} "
                            f"({old.get('reason', 'no numeric Ir baseline')})")
            if new.get("status") == "measured":
                if valid_measured_row(new, verify_totals):
                    changes.append({"id": key, "percent": None, "status": "newly_measured"})
                else:
                    changes.append({"id": key, "percent": None, "status": "invalid_measurement"})
                    failures.append(f"{key}: invalid current Ir or Callgrind totals")
            else:
                changes.append({"id": key, "percent": None, "status": "unavailable"})
                failures.append(f"{key}: current {new.get('status')} "
                                f"({new.get('reason', 'no numeric Ir measurement')})")
            continue
        if new.get("status") != "measured":
            failures.append(f"{key}: measurement regressed to {new.get('status')} "
                            f"({new.get('reason', 'no numeric Ir measurement')})")
            continue
        a, b = old.get("ir_per_block"), new.get("ir_per_block")
        if not valid_measured_row(old, verify_totals):
            failures.append(f"{key}: invalid baseline Ir or Callgrind totals")
            continue
        if not valid_measured_row(new, verify_totals):
            failures.append(f"{key}: invalid current Ir or Callgrind totals")
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
        changes, failures = compare(baseline, current, args.threshold,
                                    required_ids=expected_ids(), verify_totals=True)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Callgrind gate: {exc}", file=sys.stderr)
        return 2
    print(render(changes, failures, args.threshold, markdown=args.markdown))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
