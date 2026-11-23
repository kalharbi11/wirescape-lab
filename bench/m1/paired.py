#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Strict, device-off M1 base/head evidence, including declared paired-unavailable Chord rows."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.gate.compare import expected_ids, experimental_row_ids, indexed, valid_measured_row

SHA = re.compile(r"[0-9a-f]{40}\Z")
RETIRED = "fixed/abi1_mono"  # exact S4 historical-only metric; never measured on head
CHORD = {"module/essentials.chord/voices1", "module/essentials.chord/voices8"}
REASON = "exit 2: module_cpu_probe: create/prepare failed"
FIELDS = ("schema", "machine", "architecture", "valgrind_version", "method",
          "configuration", "sample_rate_hz", "measurement_block_frames",
          "lengths_blocks", "note_source")


def compare_pair(base, head, base_sha, head_sha, machine):
    failures, exceptions, measured, retired, new = [], [], [], [], []
    if not all(SHA.fullmatch(x or "") for x in (base_sha, head_sha)):
        failures.append("both revision pins must be 40 lowercase hexadecimal characters")
    if base_sha == head_sha:
        failures.append("base and head commits must differ")
    for name, doc, pin in (("base", base, base_sha), ("head", head, head_sha)):
        if doc.get("commit") != pin:
            failures.append(f"{name}: actual collector commit does not equal requested pin")
        if doc.get("machine") != machine:
            failures.append(f"{name}: wrong requested machine")
        if doc.get("schema") != 1:
            failures.append(f"{name}: unsupported schema")
    for key in FIELDS:
        if base.get(key) != head.get(key):
            failures.append(f"mismatch in collector provenance: {key}")
    if machine not in ("linux-x64", "linux-arm64"):
        failures.append("unsupported instruction machine")
    if base.get("method") != "callgrind-Ir-two-length-difference-v1":
        failures.append("unrecognized method")
    if base.get("configuration") != "Release plus -g":
        failures.append("unrecognized configuration")
    if base.get("sample_rate_hz") != 48000 or base.get("measurement_block_frames") != 128:
        failures.append("unexpected sample rate or block size")
    if base.get("lengths_blocks") != [12, 24]:
        failures.append("unexpected module/patch measurement lengths")
    if not isinstance(base.get("valgrind_version"), str) or not base["valgrind_version"]:
        failures.append("missing Valgrind version")
    if not isinstance(base.get("architecture"), str) or not base["architecture"]:
        failures.append("missing architecture")
    try:
        before, after = indexed(base), indexed(head)
        required = expected_ids(ROOT)
        experimental = experimental_row_ids(ROOT)
    except (TypeError, ValueError, AttributeError, OSError) as error:
        return {"status": "failed", "failures": failures + [str(error)],
                "exceptions": exceptions, "measured": measured, "retired": retired, "new": new}
    # 0020 section 7: an experimental-module row present on both sides is compared
    # strictly like every other row; one present only at the head is reported as
    # new and not compared. Any other unilateral row still fails.
    required = required | (experimental & before.keys())
    for key in sorted((experimental & after.keys()) - before.keys()):
        row = after.pop(key)
        if row.get("status") == "measured" and valid_measured_row(row, True):
            new.append({"id": key, "head_ir": row["ir_per_block"], "head_totals": row["totals"],
                        "disposition": "new experimental module row; NOT compared"})
        else:
            failures.append(f"{key}: new experimental row is not a valid measurement")
    # The base may carry the genuine historic ABI1 measurement; the head may not.
    # Retired evidence is disclosed separately, excluded from both the 96-row
    # comparison and the measured/pass counts. Unknown extras still fail closed.
    if RETIRED in before:
        old = before.pop(RETIRED)
        if old.get("status") != "measured" or not valid_measured_row(old, True):
            failures.append("base: invalid historic retired ABI1 measurement")
        retired.append({"id": RETIRED, "disposition":
                        "retired: historical base only; NOT compared, measured, zero or passed"})
    if RETIRED in after:
        failures.append("head: retired ABI1 metric must not be collected")
    for name, rows in (("base", before), ("head", after)):
        missing = required - rows.keys()
        extra = rows.keys() - required
        if missing:
            failures.append(f"{name}: missing IDs: {', '.join(sorted(missing))}")
        if extra:
            failures.append(f"{name}: unexpected IDs: {', '.join(sorted(extra))}")
    for key in sorted(required & before.keys() & after.keys()):
        b, h = before[key], after[key]
        if b.get("status") == h.get("status") == "unavailable" and key in CHORD:
            b_reason, h_reason = b.get("reason"), h.get("reason")
            entry = {"id": key, "base_reason": b_reason, "head_reason": h_reason,
                     "disposition": "SR10 paired unavailable; NOT measured"}
            exceptions.append(entry)
            if b_reason != REASON or h_reason != REASON:
                failures.append(f"{key}: paired-unavailable reasons diverge from authorized evidence")
            continue
        if b.get("status") != "measured" or h.get("status") != "measured":
            failures.append(f"{key}: unexpected unavailable or unilateral measurement "
                            f"(base={b.get('status')}, head={h.get('status')})")
            continue
        if not valid_measured_row(b, True) or not valid_measured_row(h, True):
            failures.append(f"{key}: invalid/nonfinite/nonpositive Ir or two-length totals")
            continue
        # Both sides have the identical fixed-mode length rule (10/30) or
        # patch/module rule (12/24), validated by compare.valid_measured_row.
        change = (h["ir_per_block"] / b["ir_per_block"] - 1.0) * 100.0
        if not math.isfinite(change):
            failures.append(f"{key}: nonfinite delta")
            continue
        measured.append({"id": key, "base_ir": b["ir_per_block"],
                         "head_ir": h["ir_per_block"], "percent": change,
                         "base_totals": b["totals"], "head_totals": h["totals"]})
        if change > 1.0 + 1e-10:
            failures.append(f"{key}: +{change:.9f}% exceeds strict +1%")
    if len(measured) + len(exceptions) != len(required):
        failures.append("incomplete measured/exception inventory")
    return {"status": "failed" if failures else "passed", "base_sha": base_sha,
            "head_sha": head_sha, "machine": machine,
            "expected_count": len(required), "measured_count": len(measured),
            "paired_unavailable_count": len(exceptions), "retired_count": len(retired), "new_count": len(new),
            "failures": failures, "exceptions": exceptions, "measured": measured,
            "retired": retired, "new": new}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--head", type=Path, required=True)
    p.add_argument("--base-sha", required=True)
    p.add_argument("--head-sha", required=True)
    p.add_argument("--machine", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = compare_pair(json.loads(args.base.read_text()),
                              json.loads(args.head.read_text()),
                              args.base_sha, args.head_sha, args.machine)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = {"status": "failed", "failures": [str(exc)],
                  "exceptions": [], "measured": [], "retired": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"M1 strict paired result: {result['status']}; "
          f"measured={result.get('measured_count', 0)}; "
          f"paired-unavailable={len(result['exceptions'])}; "
          f"retired={len(result.get('retired', []))}; "
          f"new={len(result.get('new', []))}; "
          f"failures={len(result['failures'])}", flush=True)
    for err in result["failures"]:
        print("FAIL: " + err, file=sys.stderr)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
