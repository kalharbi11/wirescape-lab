# SPDX-License-Identifier: GPL-3.0-only
"""Retain actual Callgrind dumps and report only the two authorized A69a rows."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

from profile_blocks import dump_role, parse_dump, summarize


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
    render_threads = set()
    all_files = {}
    for path in sorted(dest.glob("callgrind.out*")):
        raw = path.read_text()
        role, thread = dump_role(path.name, raw)
        all_files[path.name] = {"role": role, "thread": thread, "sha256": digest(path)}
        if role != "block":
            continue
        render_threads.add(thread)
        row = parse_dump(raw)
        if row["block"] in profiles:
            raise ValueError("duplicate block dump")
        rows.append(row)
        profiles[row["block"]] = path
    if len(render_threads) != 1:
        raise ValueError("labelled blocks must come from one render owner")
    expected = list(range(metadata["warmup_blocks"], metadata["completed_blocks"]))
    if sorted(profiles) != expected:
        raise ValueError("profiled block count differs from actual render calls")
    collected = re.findall(r"Collected\s*:\s*([0-9,]+)", (dest / "stderr.txt").read_text())
    if len(collected) != 1 or sum(r["ir"] for r in rows) != int(collected[0].replace(",", "")):
        raise ValueError("sum of per-block Ir differs from actual Callgrind collection")
    if metadata["fade_frames"] != (960 if kind == "dual" else 0):
        raise ValueError("unexpected fade")
    table = summarize(rows, kind, metadata["fade_frames"],
                      request_block=metadata["request_block"] if kind == "dual" else None)
    if kind == "dual":
        if not (table["adoption_block"] <= metadata["ack_completed_blocks"] < metadata["housekeeping_request"] <= table["housekeeping_block"]):
            raise ValueError("observed adoption / acknowledged request / housekeeping ordering mismatch")
        if metadata["housekeeping_request"] < table["last_fade_block"] + 1:
            raise ValueError("housekeeping requested before fade completion")
    else:
        # Inclusive annotation at the actual max block. Module attribution is
        # a separate reviewable fact, never an estimated share from rank data.
        max_block = max(rows, key=lambda row: row["ir"])["block"]
        annotated = command("callgrind_annotate", "--inclusive=yes", "--threshold=100",
                            profiles[max_block], capture_output=True, timeout=60).stdout
        (dest / "max-block-inclusive.txt").write_text(annotated)
        table["max_block"] = max_block
        table["module_attribution"] = "see retained inclusive annotation; no unverified share"
    return {"patch_sha256": digest(patch), "metadata": metadata, "table": table, "render_thread": next(iter(render_threads)),
            "all_dump_files": all_files,
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
