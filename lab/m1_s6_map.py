# SPDX-License-Identifier: GPL-3.0-only
"""M1 S6 read-only source-layout preflight; no source mutation.

Pre-window draft for #294.  Based on B4's signed #199 map #7020815710.
This file is NOT the completed S6 replay script: the ordered move/reference
substitutions and exact tree replay must be added and reviewed at the window.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

EXPECTED = {
    "engine2": 21, "control": 13, "voice": 7, "linear_ramp": 1,
    "sdk": 23, "public_sdk": 2, "modules2": 230, "sidecar": 25,
    "document": 16, "io": 30, "cli": 4, "examples": 7,
    "portaudio": 2, "output_policy": 1, "tests2": 25,
    "tests": 24, "web": 5, "render": 7, "capture": 1,
    "native_entry": 2,
}
EXPECTED_TOTAL = 446

# Specific files precede directory rules. All values are repo-root relative.
FILES = {
    "native/include/wirescape/linear_ramp.h": ("engine/include/wirescape/linear_ramp.h", "linear_ramp"),
    "native/include/wirescape/module2.h": ("sdk/include/wirescape/module2.h", "public_sdk"),
    "native/include/wirescape/MODULE2_LICENSE.txt": ("sdk/include/wirescape/MODULE2_LICENSE.txt", "public_sdk"),
    "native/include/wirescape/output_policy.h": ("host/include/wirescape/output_policy.h", "output_policy"),
    "native/CMakeLists.txt": ("native/CMakeLists.txt", "native_entry"),
    "native/README.md": ("native/README.md", "native_entry"),
}
PREFIXES = (
    ("native/engine2/", "engine/", "engine2"),
    ("native/control/", "engine/control/", "control"),
    ("native/voice/", "engine/voice/", "voice"),
    ("native/sdk/", "sdk/", "sdk"),
    ("native/modules2/", "modules/", "modules2"),
    ("native/sidecar/", "host/sidecar/", "sidecar"),
    ("native/document/", "host/document/", "document"),
    ("native/io/audio/", "host/audio/", "io"),
    ("native/io/midi/", "host/midi/", "io"),
    ("native/io/osc/", "host/osc/", "io"),
    ("native/io/net/", "host/net/", "io"),
    ("native/cli/", "host/cli/", "cli"),
    ("native/examples/", "host/examples/", "examples"),
    ("native/third_party/portaudio/", "host/third_party/portaudio/", "portaudio"),
    ("native/tests2/", "tests/native/abi2/", "tests2"),
    ("native/tests/", "tests/native/compat/", "tests"),
    ("native/web/", "targets/web/", "web"),
    ("native/tools/render/", "tools/render/", "render"),
    ("native/tools/capture/", "tools/capture/", "capture"),
)


def target(source: str) -> tuple[str, str]:
    if source in FILES:
        return FILES[source]
    for old, new, group in PREFIXES:
        if source.startswith(old):
            return new + source[len(old):], group
    raise ValueError("UNMAPPED native source: " + source)


def plan(tracked: list[str], *, enforce_counts: bool = True) -> dict:
    original = sorted(p for p in tracked if p.startswith("native/"))
    mapping = {}
    count = Counter()
    errors = []
    for src in original:
        try:
            dst, group = target(src)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        mapping[src] = dst
        count[group] += 1

    if enforce_counts:
        if len(original) != EXPECTED_TOTAL:
            errors.append(f"native tracked count {len(original)} != {EXPECTED_TOTAL}")
        for group, expected in EXPECTED.items():
            if count[group] != expected:
                errors.append(f"group {group}: {count[group]} != {expected}")

    # Compare with all non-moved tracked files, including unrelated root tools.
    moved = {src for src, dst in mapping.items() if src != dst}
    remaining = set(tracked) - moved
    used = {}
    remaining_folded = {p.casefold() for p in remaining}
    for src, dst in mapping.items():
        key = dst.casefold()
        previous = used.get(key)
        if previous is not None:
            errors.append(f"duplicate/case-fold destination: {previous} and {src} -> {dst}")
        used[key] = src
        if dst != src and key in remaining_folded:
            errors.append(f"destination overwrites tracked file: {src} -> {dst}")
        if dst != src:
            components = PurePosixPath(dst).parts
            for i in range(1, len(components)):
                parent = "/".join(components[:i])
                if parent.casefold() in remaining_folded:
                    errors.append(f"destination parent is a tracked file: {parent} for {dst}")
            if any(path.casefold().startswith(key + "/") for path in remaining):
                errors.append(f"destination is ancestor of tracked path: {dst}")

    return {
        "ok": not errors, "native_sources": len(original),
        "moved": len(moved), "retained": len(mapping) - len(moved),
        "groups": dict(sorted(count.items())), "errors": sorted(set(errors)),
        "mapping": dict(sorted(mapping.items())),
    }


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def repository_plan(root: Path) -> dict:
    if git(root, "status", "--porcelain", "--untracked-files=no").strip():
        raise RuntimeError("STOP: tracked working tree has modifications")
    tracked = [v.decode("utf-8") for v in git(root, "ls-files", "-z").split(bytes([0])) if v]
    result = plan(tracked)
    if result["ok"]:
        for src, dst in result["mapping"].items():
            source = root / src
            dest = root / dst
            if source.is_symlink() or not source.is_file():
                result["errors"].append(f"source not a regular tracked file: {src}")
            if src != dst and (dest.exists() or dest.is_symlink()):
                result["errors"].append(f"destination already present: {dst}")
            for parent in dest.parents:
                if parent == root:
                    break
                if parent.is_file() or parent.is_symlink():
                    result["errors"].append(f"destination parent not a directory: {parent.relative_to(root)}")
    result["ok"] = not result["errors"]
    result["head"] = git(root, "rev-parse", "HEAD").decode().strip()
    return result


def self_test() -> None:
    assert target("native/io/midi/libremidi_backend.cpp")[0] == "host/midi/libremidi_backend.cpp"
    assert target("native/tests/fixtures/abi2/f.json")[0] == "tests/native/compat/fixtures/abi2/f.json"
    assert target("native/engine2/tests/header_c99.c")[0] == "engine/tests/header_c99.c"
    assert target("native/include/wirescape/module2.h")[0] == "sdk/include/wirescape/module2.h"
    assert target("native/CMakeLists.txt")[0] == "native/CMakeLists.txt"
    assert plan(["native/sdk/foo.h"], enforce_counts=False)["ok"]
    assert not plan(["native/sdk/foo.h", "sdk/foo.h"], enforce_counts=False)["ok"]
    assert not plan(["native/sdk/foo.h", "SDK/foo.h"], enforce_counts=False)["ok"]
    assert not plan(["native/sdk/foo.h", "sdk/foo.h/inner"], enforce_counts=False)["ok"]
    assert not plan(["native/unknown.cpp"], enforce_counts=False)["ok"]
    print("M1 S6 map pure self-test PASS (synthetic only; not full-repository evidence)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--full-map", action="store_true", help="print every source/destination mapping")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        root = Path(git(args.root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        result = repository_plan(root)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 2
    if not args.full_map:
        result.pop("mapping")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
