# SPDX-License-Identifier: GPL-3.0-only
"""M1 S6 (T1.4) guarded migration: moves plus exact line substitutions.

Reads one manifest (`lab/m1_s6_manifest.json`) and the move map from
`lab/m1_s6_map.py`, checked against the base commit the manifest names.

  python3 lab/m1_s6_apply.py               # build the tree from HEAD in an isolated index, print its id
  python3 lab/m1_s6_apply.py --audit       # also list path references left unresolved
  python3 lab/m1_s6_apply.py --apply       # check out that tree in this (clean, base) checkout

Evidence 6 (0006): at the script commit (main_base plus lab/ only), `python3 lab/m1_s6_apply.py`
prints the tree id of the PR head commit.
The script only moves files (mode and blob preserved) and replaces whole lines whose exact
before-text and source blob id the manifest records. No other byte changes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "m1_s6_manifest.json"


def git(root: Path, *args: str, data: bytes | None = None, env=None) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], input=data, env=env)


def entries(root: Path, ref: str) -> dict[str, tuple[bytes, bytes]]:
    out = {}
    for rec in git(root, "ls-tree", "-r", "-z", ref).split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            mode, _kind, oid = meta.split(b" ")
            out[path.decode("utf-8")] = (mode, oid)
    return out


def load_map_module():
    spec = importlib.util.spec_from_file_location("m1_s6_map", HERE / "m1_s6_map.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def manifest_digest(text: bytes) -> str:
    return hashlib.sha256(text.replace(b"\r\n", b"\n")).hexdigest()


def check_base(root: Path, main_base: str, base: str) -> None:
    """The base is main_base itself, or main_base plus commits that touch only lab/."""
    try:
        git(root, "merge-base", "--is-ancestor", main_base, base)
    except subprocess.CalledProcessError:
        raise SystemExit(f"{main_base} is not an ancestor of {base}")
    extra = git(root, "diff", "--name-only", "--no-renames", main_base, base).decode().split()
    outside = [p for p in extra if not p.startswith("lab/")]
    if outside:
        raise SystemExit("base differs from main_base outside lab/: " + ", ".join(outside[:10]))


def build(root: Path, manifest: dict, base: str) -> tuple[str, dict, dict]:
    """Return (tree id, destination entries, move map). Writes only Git objects."""
    source = entries(root, base)
    mapped = load_map_module().plan(sorted(source))
    if not mapped["ok"]:
        raise SystemExit("m1_s6_map errors: " + "; ".join(mapped["errors"]))
    moves = {s: d for s, d in mapped["mapping"].items() if s != d}
    digest = hashlib.sha256(json.dumps(sorted(moves.items())).encode()).hexdigest()
    if digest != manifest["move_map_sha256"] or len(moves) != manifest["moves"]:
        raise SystemExit(f"move map differs from the manifest ({len(moves)} moves, {digest})")
    if moves.keys() - source.keys():
        raise SystemExit("move map names a path missing at base")
    dest = {moves.get(p, p): info for p, info in source.items()}
    if len(dest) != len(source) or len({p.casefold() for p in dest}) != len(dest):
        raise SystemExit("moves would overwrite a path")
    for p in dest:
        parent = p.rpartition("/")[0]
        while parent:
            if parent in dest:
                raise SystemExit(f"file/directory collision at {parent}")
            parent = parent.rpartition("/")[0]

    seen_files = set()
    for edit in manifest["edits"]:
        src = edit["source"]
        if src in seen_files or src not in source:
            raise SystemExit(f"duplicate or missing edit source {src}")
        seen_files.add(src)
        mode, oid = source[src]
        if oid.decode() != edit["blob"]:
            raise SystemExit(f"source blob changed since the manifest was written: {src}")
        data = git(root, "cat-file", "blob", oid.decode())
        lines = data.decode("utf-8").splitlines(keepends=True)
        done = set()
        for rep in edit["lines"]:
            i = rep["line"] - 1
            if i in done or not 0 <= i < len(lines):
                raise SystemExit(f"bad line {i + 1} in {src}")
            body = lines[i].rstrip("\r\n")
            if body != rep["before"]:
                raise SystemExit(f"anchor mismatch {src}:{i + 1}")
            lines[i] = rep["after"] + lines[i][len(body):]
            done.add(i)
        new_oid = git(root, "hash-object", "-w", "--stdin", data="".join(lines).encode("utf-8")).strip()
        dest[moves.get(src, src)] = (mode, new_oid)

    records = b"".join(m + b" " + o + b"\t" + p.encode() + b"\0" for p, (m, o) in sorted(dest.items()))
    with TemporaryDirectory(prefix="s6-index-") as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        git(root, "update-index", "-z", "--index-info", data=records, env=env)
        tree = git(root, "write-tree", env=env).decode().strip()
    if entries(root, tree) != dest:
        raise SystemExit("generated tree differs from the plan")
    return tree, dest, moves


def audit(root: Path, manifest: dict, tree: str, dest: dict, moves: dict) -> list[str]:
    """Every old-root reference left in the tree must match a classification rule."""
    pattern = re.compile("|".join(manifest["audit_tokens"]))
    rules = [(re.compile(c["path"]), re.compile(c.get("line", ".*")), c["class"])
             for c in manifest["classified"]]
    unresolved = []
    for path, (mode, oid) in sorted(dest.items()):
        if mode == b"160000":
            continue
        data = git(root, "cat-file", "blob", oid.decode())
        if b"\0" in data[:8000]:
            continue
        for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            if not pattern.search(line):
                continue
            if not any(pr.search(path) and lr.search(line) for pr, lr, _ in rules):
                unresolved.append(f"{path}:{n}: {line.strip()[:160]}")
    return unresolved


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=HERE.parent)
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--base", help="commit to build from (default: HEAD)")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--apply", action="store_true", help="check the tree out in --root")
    args = ap.parse_args()
    raw = args.manifest.read_bytes()
    manifest = json.loads(raw)
    root = args.root.resolve()
    base = git(root, "rev-parse", f"{args.base or 'HEAD'}^{{commit}}").decode().strip()
    check_base(root, manifest["main_base"], base)
    tree, dest, moves = build(root, manifest, base)
    report = {"base": base, "main_base": manifest["main_base"], "tree": tree, "moves": len(moves),
              "files_edited": len(manifest["edits"]),
              "lines_edited": sum(len(e["lines"]) for e in manifest["edits"]),
              "manifest_sha256": manifest_digest(raw)}
    if args.audit:
        left = audit(root, manifest, tree, dest, moves)
        report["unresolved"] = len(left)
        for row in left:
            print(row, file=sys.stderr)
    if args.apply:
        if git(root, "rev-parse", "HEAD").decode().strip() != base:
            raise SystemExit("--apply builds from HEAD only")
        if git(root, "status", "--porcelain=v1", "--untracked-files=no"):
            raise SystemExit("--apply needs a clean checkout")
        git(root, "read-tree", "-m", "-u", "HEAD", tree)
        report["applied"] = True
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report.get("unresolved") else 0


if __name__ == "__main__":
    sys.exit(main())
