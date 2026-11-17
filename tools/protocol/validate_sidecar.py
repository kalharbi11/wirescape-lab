# SPDX-License-Identifier: GPL-3.0-only
"""Validate all actual sidecar protocol-test stdout lines without editing existing tests.

Usage: python tools/protocol/validate_sidecar.py PATH-TO-ENGINE native/examples
Only the existing tests' device-free/null-sink and loopback test harness runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from validate import read_schema, validate

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "native" / "sidecar" / "protocol_tests.py"
STDOUT_ANCHOR = "self.messages.put(json.loads(line, object_pairs_hook=strict_object))"
REQUEST_ANCHOR = "command = dict(v=0, id=request_id, type=method, **payload)"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    args = sys.argv[1:]
    code = TARGET.read_text(encoding="utf-8")
    if code.count(STDOUT_ANCHOR) != 1 or code.count(REQUEST_ANCHOR) != 1:
        raise SystemExit("Sidecar corpus parser changed; validation instrumentation must be reviewed")
    code = code.replace(
        STDOUT_ANCHOR,
        "self.messages.put(validate_stdout(json.loads(line, object_pairs_hook=strict_object)))",
    ).replace(
        REQUEST_ANCHOR,
        "command = validate_request(dict(v=0, id=request_id, type=method, **payload), expected)",
    )
    schema = read_schema()
    counters = {"emitted": 0, "accepted_requests": 0, "expected_refusals": 0}

    def validate_stdout(wire):
        if not validate(wire, schema):
            raise AssertionError(f"Actual sidecar stdout does not match v0 schema: {json.dumps(wire)[:600]}")
        counters["emitted"] += 1
        return wire

    def validate_request(wire, expected):
        # Expected-refusal fixtures intentionally include invalid envelopes and
        # semantically rejected but shape-valid requests; do not falsify their oracle.
        if expected:
            if not validate(wire, schema):
                raise AssertionError(f"Expected-accepted request outside v0 schema: {wire!r}")
            counters["accepted_requests"] += 1
        else:
            counters["expected_refusals"] += 1
        return wire

    saved_argv = sys.argv
    try:
        sys.argv = [str(TARGET), *args]
        context = {
            "__name__": "__main__", "__file__": str(TARGET),
            "validate_stdout": validate_stdout, "validate_request": validate_request,
        }
        exec(compile(code, str(TARGET), "exec"), context)
    finally:
        sys.argv = saved_argv
    if counters["emitted"] == 0 or counters["accepted_requests"] == 0:
        raise SystemExit("Sidecar corpus validation did not observe both outputs and commands")
    print("PV1 observed sidecar protocol-test lines:", counters)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
