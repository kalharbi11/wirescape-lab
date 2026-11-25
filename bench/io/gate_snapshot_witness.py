# SPDX-License-Identifier: GPL-3.0-only
"""Bounded SC interleavings of one OSC Out gate row (#475).

This is a synthetic source-order model, NOT a native product reproducer,
latency measurement, or attribution of a historical failure. It needs no
sockets, devices, threads, randomized timing, or third-party libraries.
"""
import argparse
import json
import subprocess
from itertools import combinations
from pathlib import Path

PRODUCER = ("P.value", "P.rises", "P.blocks")
CONSUMER = ("C.blocks", "C.rises", "C.falls", "C.value")
WITNESS = ("P.value", *CONSUMER, "P.rises", "P.blocks")
SOURCE_BLOBS = {
    "modules/osc_out/dsp.h": "f340756af70f66bd35535f2ccd576ff421bf957b",
    "engine/control/osc_out_host.cpp": "f21720ef17f3f198db712b7f03e5999b5d4eceb4",
    "engine/control/osc_out_host.h": "7c8e165fd1f8fdafdb33f0155530c97af09ad2f3",
    "host/osc/out_bus.h": "8ae9355f62afe234ce4f54ae2c1751c9c83a365e",
}
HISTORICAL_HEAD = "d85c076b060c07a3e02fbc4ba3fe048638ea82fd"
SOURCE_BASE = "a8b34237b252d9fcfedfa3810732ba8feacae560"


def run_schedule(schedule):
    """Execute a single producer/consumer interleaving; return a full trace.

    Initial row is a completely published low block (blocks=1).
    The consumer cursor first sends that baseline. One rising block is
    interleaved with a poll; then two quiescent polls follow, then a
    completely published falling block and one final poll.
    All sends succeed and the real 64-message poll budget cannot bind.
    Only 0 or 1 counter delta is reachable here; overflow/wrap are excluded.
    """
    schedule = tuple(schedule)
    if (tuple(op for op in schedule if op.startswith("P.")) != PRODUCER
            or tuple(op for op in schedule if op.startswith("C.")) != CONSUMER
            or len(schedule) != len(PRODUCER) + len(CONSUMER)):
        raise ValueError("not an order-preserving merge of the two operation lists")
    row = {"blocks": 1, "rises": 0, "falls": 0, "value": 0}
    cursor = {"rises": 0, "falls": 0, "initialized": False, "gate_high": False}
    trace, snapshots, emitted = [], [], []
    drops = 0

    def record(operation, snapshot=None, sent=None):
        trace.append({"operation": operation, "bus": dict(row),
                      "snapshot": None if snapshot is None else dict(snapshot),
                      "cursor": dict(cursor), "sent": list(sent or []),
                      "drops": drops})

    def consume(snapshot, label):
        nonlocal drops
        snapshots.append(dict(snapshot))
        sent = []
        if not snapshot["blocks"]:
            record(label, snapshot)
            return
        rises, falls = snapshot["rises"], snapshot["falls"]
        edges = ((rises - cursor["rises"]) & 0xffffffff) + (
            (falls - cursor["falls"]) & 0xffffffff)
        high = snapshot["value"] >= 0.5
        # Source-order translation of OutHost::loop's gate branch,
        # restricted to the bounded, successful-send path.
        assert 0 <= edges <= 1
        if not cursor["initialized"] and not edges:
            sent.append(int(high))
            cursor["gate_high"] = high
            cursor["initialized"] = True
        if edges:
            for _ in range(edges):
                cursor["gate_high"] = not cursor["gate_high"]
                sent.append(int(cursor["gate_high"]))
            cursor["rises"], cursor["falls"] = rises, falls
            cursor["initialized"] = True
        elif cursor["initialized"] and cursor["gate_high"] != high:
            sent.append(int(high))
            cursor["gate_high"] = high
        assert len(sent) <= 64
        emitted.extend(sent)
        record(label, snapshot, sent)

    consume(dict(row), "baseline complete poll")
    snapshot = {}
    for op in schedule:
        owner, field = op.split(".")
        if owner == "P":
            if field == "value":
                row[field] = 1
            else:
                row[field] += 1
            record(op, snapshot)
        else:
            snapshot[field] = row[field]
            record(op, snapshot)
            if field == "value":
                consume(snapshot, "interleaved poll: gate decision")
    consume(dict(row), "first post-rise complete poll")
    consume(dict(row), "second post-rise complete poll")
    row["value"] = 0
    record("fall.value")
    row["falls"] += 1
    record("fall.falls")
    row["blocks"] += 1
    record("fall.blocks")
    consume(dict(row), "post-fall complete poll")
    return {"schedule": list(schedule), "expected": [0, 1, 0],
            "emitted": emitted, "drops": drops, "snapshots": snapshots,
            "trace": trace}


def enumerate_schedules():
    """All 7-choose-3 source-order merges, not a C++ memory-model simulator."""
    size = len(PRODUCER) + len(CONSUMER)
    for slots in combinations(range(size), len(PRODUCER)):
        producer, consumer = iter(PRODUCER), iter(CONSUMER)
        yield run_schedule(tuple(next(producer) if i in slots else next(consumer)
                                 for i in range(size)))


def source_identity():
    root = Path(__file__).resolve().parents[2]

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args],
                                       text=True).strip()

    head = git("rev-parse", "HEAD")
    blobs = {path: git("rev-parse", f"HEAD:{path}") for path in SOURCE_BLOBS}
    if blobs != SOURCE_BLOBS:
        raise ValueError("model source changed; revalidate translation before reporting")
    return {"head": head, "source_base": SOURCE_BASE,
            "historical_head": HISTORICAL_HEAD, "source_blobs": blobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = list(enumerate_schedules())
    different = sum(row["emitted"] != row["expected"] for row in rows)
    report = {
        "classification": "synthetic SC witness; historical cause unresolved",
        "source": source_identity(),
        "schedule_count": len(rows),
        "different_count": different,
        "matching_count": len(rows) - different,
        "note": "Schedule counts are exhaustive for this bound, not probabilities.",
        "witness": run_schedule(WITNESS),
        "schedules": [{key: row[key] for key in
                       ("schedule", "expected", "emitted", "drops")} for row in rows],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
