# SPDX-License-Identifier: GPL-3.0-only
"""Fail CI if a real-sidecar scenario or comparison report is absent/incomplete."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEVICE = ROOT / "bench" / "device" / "results"
COMPARE = ROOT / "bench" / "compare" / "results"
SCENARIOS = ("all", "basics", "chaos", "scene", "groove", "extreme", "endurance")


def latest(directory):
    candidates = sorted(directory.glob("*/manifest.json"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one manifest in {directory}; got {len(candidates)}")
    folder = candidates[0].parent
    for name in ("manifest.json", "analysis.json", "report.md"):
        if not (folder / name).is_file() or (folder / name).stat().st_size == 0:
            raise RuntimeError(f"missing/nonempty evidence: {folder / name}")
    return folder, json.loads((folder / "manifest.json").read_text(encoding="utf-8"))


def check():
    for scenario in SCENARIOS:
        folder, manifest = latest(DEVICE / f"ci-{scenario}")
        if manifest.get("engine_mode") != "null-audio" or not manifest.get("completed"):
            raise RuntimeError(f"{scenario}: no completed real null-sink run: {manifest}")
        events = [json.loads(line) for line in (folder / "events.ndjson").read_text(encoding="utf-8").splitlines()]
        if not any(e.get("direction") == "out" and
                   e.get("payload", {}).get("type") == "hello" and
                   e["payload"].get("session") for e in events):
            raise RuntimeError(f"{scenario}: missing real-engine hello")
        requests = {e["payload"]["id"] for e in events if e.get("direction") == "in"
                    and "id" in e.get("payload", {})}
        acks = {e["re"] for e in events if e.get("direction") == "ack" and e.get("re")}
        refused = [e for e in events if e.get("direction") == "out" and
                   e.get("payload", {}).get("ok") is False]
        if not requests or requests != acks or refused:
            raise RuntimeError(f"{scenario}: unmatched requests, missing ack or refused replies: "
                               f"requests={len(requests)} acks={len(acks)} refused={len(refused)}")
        if any(e.get("direction") == "engine-exit" and e.get("code") != 0 for e in events):
            raise RuntimeError(f"{scenario}: engine abnormal exit")
        print(f"{scenario}: {len(acks)} real engine replies; {folder / 'report.md'}")

    folder, manifest = latest(COMPARE / "ci-null")
    if (manifest.get("mode") != "null_sink_process" or not manifest.get("completed")
            or not manifest.get("engine_hello_validated")):
        raise RuntimeError("comparison run did not sample real null-sink engine")
    evidence = json.loads((folder / "analysis.json").read_text(encoding="utf-8"))
    if evidence.get("resources", {}).get("samples", 0) < 10:
        raise RuntimeError("comparison did not sample 10 Hz for 1.2s")
    print(f"comparison: real engine process; {folder / 'report.md'}")

    limits = list((DEVICE / "limits").glob("*/analysis.json"))
    if len(limits) != 1:
        raise RuntimeError("expected exactly one graph-capacity probe result")
    probes = json.loads(limits[0].read_text(encoding="utf-8"))
    if [x["response"].get("code") for x in probes.get("replies", [])] != ["limit", "limit"]:
        raise RuntimeError("graph-capacity refusal not verified")
    print("limits: N16 (96 modules) and 129 cables refused with code=limit")


if __name__ == "__main__":
    check()
