# SPDX-License-Identifier: GPL-3.0-only
"""Replay just the approved S6 moves in an isolated Git index."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


def git(root, *args, input_data=None, env=None):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], input=input_data, env=env
    )


def entries(root, ref):
    result = {}
    for record in git(root, "ls-tree", "-r", "-z", ref).split(bytes([0])):
        if record:
            meta, path = record.split(b"\t", 1)
            mode, _, oid = meta.split(b" ")
            result[path.decode("utf-8")] = mode, oid
    return result


def replay(root, manifest, entry_plan=None):
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if head != manifest["head"] or git(root, "status", "--porcelain=v1"):
        raise ValueError("Replay requires the exact clean source checkout.")
    source = entries(root, head)
    moves = {row["from"]: row["to"] for row in manifest["move_map"]}
    if len(moves) != manifest["moves"] or moves.keys() - source.keys():
        raise ValueError("Move map contains a duplicate or missing source.")
    dest = {moves.get(path, path): info for path, info in source.items()}
    if len(dest) != len(source) or len({path.casefold() for path in dest}) != len(dest):
        raise ValueError("Replay would overwrite a path.")
    for path in dest:
        parent = path.rpartition("/")[0]
        while parent:
            if parent in dest:
                raise ValueError(f"Ancestor-file collision at {parent}")
            parent = parent.rpartition("/")[0]

    rewritten = []
    if entry_plan is not None:
        if entry_plan["head"] != head:
            raise ValueError("Entry-point plan is for a different head.")
        for row in entry_plan["entry_point_edits"]:
            old, new = row["source"], row["destination"]
            if moves.get(old, old) != new or new in rewritten:
                raise ValueError(f"Unexpected rewrite destination {new}")
            mode, object_id = source[old]
            original = git(root, "cat-file", "blob", object_id.decode())
            if hashlib.sha256(original).hexdigest() != row["source_sha256"]:
                raise ValueError(f"Edited source blob changed since planning: {old}")
            lines = original.decode().splitlines(keepends=True)
            seen = set()
            for replacement in row["replacements"]:
                index = replacement["line"] - 1
                if index in seen or not 0 <= index < len(lines):
                    raise ValueError(f"Duplicate or invalid line in {old}: {index + 1}")
                line = lines[index]
                content = line.rstrip("\r\n")
                if content != replacement["before"]:
                    raise ValueError(f"Git blob anchor changed in {old}: {index + 1}")
                lines[index] = replacement["after"] + line[len(content):]
                seen.add(index)
            edited_blob = "".join(lines).encode()
            new_id = git(root, "hash-object", "-w", "--stdin", input_data=edited_blob).strip()
            dest[new] = mode, new_id
            rewritten.append(new)

    index_records = b"".join(
        mode + b" " + oid + b"\t" + path.encode() + bytes([0])
        for path, (mode, oid) in sorted(dest.items())
    )
    with TemporaryDirectory(prefix="s6-index-", dir=root.parent) as temp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / "index"))
        git(root, "update-index", "-z", "--index-info", input_data=index_records, env=env)
        tree = git(root, "write-tree", env=env).decode().strip()
    if entries(root, tree) != dest or git(root, "status", "--porcelain=v1"):
        raise ValueError("Generated tree or checkout differs from the planned state.")
    return {
        "classification": "PARTIAL_ENTRY_REHEARSAL" if rewritten else "STRUCTURAL_REHEARSAL_ONLY",
        "head": head,
        "tree": tree,
        "moves": len(moves),
        "unchanged_mode_and_blob": len(source) - len(rewritten),
        "retained_native": sorted(path for path in dest if path.startswith("native/")),
        "entry_points_rewritten": rewritten,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--entry-plan", type=Path)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entry_plan = json.loads(args.entry_plan.read_text(encoding="utf-8")) if args.entry_plan else None
    print(json.dumps(replay(args.root, manifest, entry_plan), indent=2, sort_keys=True))
