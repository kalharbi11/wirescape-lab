# SPDX-License-Identifier: GPL-3.0-only
"""Verify and plan explicit relative includes using exact tracked file endpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re


INCLUDE = re.compile(r'^(\s*#\s*include\s*")([^"\n]+)(".*)$')
PUBLIC_HEADER = "native/include/wirescape/module2.h"


def plan(root, audit):
    move_map = {item["from"]: item["to"] for item in audit["move_map"]}
    records = []
    for source_entry in audit["unverified_preview_candidates"]:
        source = source_entry["source"]
        candidates = [ref for ref in source_entry["references"]
                      if ref["kind"] == "relative-include"]
        if not candidates:
            continue
        if source == PUBLIC_HEADER:
            raise ValueError("Public ABI header bytes must stay unchanged.")
        destination = move_map.get(source, source)
        raw = (root / source).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != source_entry["source_sha256"] or destination != source_entry["destination"]:
            raise ValueError(f"Preview source or destination drift: {source}")
        lines = raw.decode().splitlines()
        replacements = []
        for ref in candidates:
            number, literal = ref["line"], ref["old"]
            original = lines[number - 1]
            match = INCLUDE.fullmatch(original)
            if not match or match[2] != literal or ref["why"] != "file":
                raise ValueError(f"Not a verified explicit relative include: {source}:{number}")
            target = posixpath.normpath(posixpath.join(posixpath.dirname(source), literal))
            moved = move_map[target]
            if not (root / target).is_file():
                raise ValueError(f"Missing original include target: {target}")
            repaired = posixpath.relpath(moved, start=posixpath.dirname(destination) or ".")
            if repaired != ref["new"]:
                raise ValueError(f"Computed include disagrees with preview: {source}:{number}")
            replacements.append({"line": number, "before": original,
                                 "after": match[1] + repaired + match[3]})
        records.append({"source": source, "destination": destination,
                        "source_sha256": digest, "replacements": replacements})
    return {"head": audit["head"], "ready_for_apply": False, "entry_point_edits": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("audit", type=Path)
    args = parser.parse_args()
    print(json.dumps(plan(args.root, json.loads(args.audit.read_text(encoding="utf-8"))),
                     indent=2, sort_keys=True))
