# SPDX-License-Identifier: GPL-3.0-only
"""Retain actual Callgrind dumps and report only the two authorized A69a rows."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from profile_blocks import parse_dump, summarize


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, text=True, **kwargs)


def one(exe, source, out, kind, name):
    patch = source / "apps/studio/patches" / name
    dest = out / kind
    dest.mkdir(exist_ok=False)
    # Non-collected control thread; each client dump is from the render owner.
    with (dest / "stdout.json").open("w") as stdout, (dest / "stderr.txt").open("w") as stderr:
        command("valgrind", "--tool=callgrind", "--error-exitcode=77", "--fair-sched=yes",
                "--collect-atstart=no", "--separate-threads=yes", "--dump-line=no",
                "--compress-strings=no", "--callgrind-out-file=" + str(dest / "callgrind.out"),
                exe, kind, patch, stdout=stdout, stderr=stderr, timeout=600)
    metadata = json.loads((dest / "stdout.json").read_text())
    if (metadata["kind"], metadata["patch"], metadata["rate"], metadata["block"]) != (
            kind, name, 48000, 256):
        raise ValueError("foreign render metadata")
    if any(metadata[k] != 0 for k in ("faults", "late", "dropped", "ring_full", "stale", "arena_full")):
        raise ValueError("nonzero engine error counters")
    rows, profiles = [], {}
    for path in sorted(dest.glob("callgrind.out*")):
        raw = path.read_text()
        if "desc: Trigger: Client Request: block-" not in raw:
            # Only non-request termination dumps may be outside the scope.
            if "desc: Trigger: Program termination" not in raw:
                raise ValueError(f"unrecognized Callgrind dump {path.name}")
            continue
        row = parse_dump(raw)
        if row["block"] in profiles:
            raise ValueError("duplicate block dump")
        rows.append(row)
        profiles[row["block"]] = path
    expected = list(range(metadata["warmup_blocks"], metadata["completed_blocks"]))
    if sorted(profiles) != expected:
        raise ValueError("profiled block count differs from actual render calls")
    if metadata["fade_frames"] != (960 if kind == "dual" else 0):
        raise ValueError("unexpected fade")
    table = summarize(rows, kind, metadata["fade_frames"])
    if kind == "dual":
        if not (table["adoption_block"] <= metadata["ack_completed_blocks"] <= table["adoption_block"] + 2):
            raise ValueError("observed adoption outside control acknowledgement bracket")
        if table["housekeeping_block"] < metadata["housekeeping_request"]:
            raise ValueError("housekeeping before request")
    else:
        # Inclusive annotation at the actual max block. Module attribution is
        # a separate reviewable fact, never an estimated share from rank data.
        max_block = max(rows, key=lambda row: row["ir"])["block"]
        annotated = command("callgrind_annotate", "--inclusive=yes", "--threshold=100",
                            profiles[max_block], capture_output=True, timeout=60).stdout
        (dest / "max-block-inclusive.txt").write_text(annotated)
        table["max_block"] = max_block
        table["module_attribution"] = "see retained inclusive annotation; no unverified share"
    return {"patch_sha256": digest(patch), "metadata": metadata, "table": table,
            "dumps": {str(i): {"file": p.name, "sha256": digest(p)} for i, p in sorted(profiles.items())}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--engine-head", required=True)
    ap.add_argument("--harness-head", required=True)
    a = ap.parse_args()
    if command("git", "-C", a.source, "rev-parse", "HEAD",
               capture_output=True).stdout.strip() != a.engine_head:
        raise ValueError("source pin mismatch")
    a.out.mkdir(parents=True, exist_ok=True)
    report = {"engine": a.engine_head, "harness": a.harness_head,
              "binary_sha256": digest(a.exe), "method": "callgrind-client-dump-per-render-v1",
              "valgrind": command("valgrind", "--version", capture_output=True).stdout.strip(),
              "rows": []}
    for kind, name in (("single", "scene-03-black-ice-choir.json"),
                       ("dual", "basics-08-clocked-groove.json")):
        report["rows"].append(one(a.exe.resolve(), a.source.resolve(), a.out.resolve(), kind, name))
        (a.out / "cost.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print("Verified both A69a per-block cost rows")


if __name__ == "__main__":
    main()
