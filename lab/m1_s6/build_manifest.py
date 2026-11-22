# SPDX-License-Identifier: GPL-3.0-only
"""Regenerate lab/m1_s6_manifest.json from its reviewed inputs (deterministic).

Inputs: the B4 plan (lab/s6_handoff/s6-native-wiring-plan.json), the B4 gap file
(lab/s6_handoff/s6-active-consumer-gaps.json), extra_edits.py and classify.py here.
Every anchor is checked against the source blob at --main-base.
  python3 lab/m1_s6/build_manifest.py --main-base <sha> [--check]
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
import m1_s6_map  # noqa: E402

OUT = LAB / "m1_s6_manifest.json"


def git(*args):
    return subprocess.check_output(["git", "-C", str(LAB.parent), *args])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-base", required=True)
    ap.add_argument("--check", action="store_true", help="fail if the committed manifest differs")
    args = ap.parse_args()
    base = git("rev-parse", args.main_base + "^{commit}").decode().strip()
    blobs = {}
    for rec in git("ls-tree", "-r", "-z", base).split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            blobs[path.decode()] = meta.split(b" ")[2].decode()
    mapped = m1_s6_map.plan(sorted(blobs))
    if not mapped["ok"]:
        raise SystemExit(mapped["errors"])
    moves = {s: d for s, d in mapped["mapping"].items() if s != d}

    def text(path):
        return git("cat-file", "blob", blobs[path])

    edits = []
    plan = json.loads((LAB / "s6_handoff/s6-native-wiring-plan.json").read_text(encoding="utf-8"))
    for e in plan["entry_point_edits"]:
        if hashlib.sha256(text(e["source"])).hexdigest() != e["source_sha256"]:
            raise SystemExit("plan anchor blob changed: " + e["source"])
        edits.append({"source": e["source"], "blob": blobs[e["source"]], "origin": "s6-native-wiring-plan",
                      "lines": [{k: r[k] for k in ("line", "before", "after")} for r in e["replacements"]]})
    gaps = json.loads((LAB / "s6_handoff/s6-active-consumer-gaps.json").read_text(encoding="utf-8"))
    for e in gaps["entry_point_edits"]:
        if blobs[e["source"]] != e["blob_sha"]:
            raise SystemExit("gap anchor blob changed: " + e["source"])
        edits.append({"source": e["source"], "blob": blobs[e["source"]], "origin": "s6-active-consumer-gaps",
                      "lines": [{k: r[k] for k in ("line", "before", "after")} for r in e["replacements"]]})
    by_name = {e["source"]: e for e in edits}
    for path, line, old, new in runpy.run_path(str(Path(__file__).with_name("extra_edits.py")))["SUBS"]:
        lines = text(path).decode("utf-8").splitlines()
        if old not in lines[line - 1]:
            hits = [i + 1 for i, s in enumerate(lines) if old in s]
            if len(hits) != 1:
                raise SystemExit(f"anchor not unique or missing: {path}:{line} {old!r} {hits}")
            line = hits[0]
        e = by_name.get(path)
        if e is None:
            e = by_name[path] = {"source": path, "blob": blobs[path], "origin": "claude-builder1", "lines": []}
            edits.append(e)
        row = next((r for r in e["lines"] if r["line"] == line), None)
        if row is None:
            row = {"line": line, "before": lines[line - 1], "after": lines[line - 1]}
            e["lines"].append(row)
            e["lines"].sort(key=lambda r: r["line"])
        if old not in row["after"]:
            raise SystemExit(f"substring not in planned line: {path}:{line} {old!r}")
        row["after"] = row["after"].replace(old, new, 1)
    edits.sort(key=lambda e: e["source"])
    cls = runpy.run_path(str(Path(__file__).with_name("classify.py")))
    manifest = {"schema": "wlab-m1-s6-manifest/1", "main_base": base, "moves": len(moves),
                "move_map_sha256": hashlib.sha256(json.dumps(sorted(moves.items())).encode()).hexdigest(),
                "audit_tokens": cls["TOKENS"], "classified": cls["CLASSIFIED"], "edits": edits}
    data = json.dumps(manifest, indent=1) + "\n"
    if args.check:
        if OUT.read_text(encoding="utf-8").replace("\r\n", "\n") != data:
            raise SystemExit("committed manifest differs from regenerated manifest")
        print("manifest matches")
        return
    OUT.write_text(data, encoding="utf-8", newline="\n")
    print(json.dumps({"files": len(edits), "lines": sum(len(e["lines"]) for e in edits),
                      "sha256": hashlib.sha256(data.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
