# SPDX-License-Identifier: GPL-3.0-only
"""Produce exact S6 edits for the native and standalone Web CMake entry points."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def replace_once(line, before, after):
    if line.count(before) != 1:
        raise ValueError(f"Expected one occurrence of {before!r} in {line!r}")
    return line.replace(before, after, 1)


def native_entry(lines, audit):
    path = "native/CMakeLists.txt"
    mapping = {"native/" + row["from"].removeprefix("native/"): row["to"]
               for row in audit["move_map"]}
    candidate, = (row for row in audit["unverified_preview_candidates"] if row["source"] == path)
    for row in candidate["references"]:
        if row["kind"] != "cmake-variable" or row["why"] not in {"directory", "file"}:
            raise ValueError("Unexpected native entry candidate.")
        index = row["line"] - 1
        lines[index] = replace_once(lines[index], row["old"], row["new"])
    for row in audit["reference_dispositions"]:
        if row["source"] != path:
            continue
        if row["disposition"] != "substitute":
            raise ValueError("Native entry contains an unresolved substitution.")
        index = row["line"] - 1
        lines[index] = replace_once(lines[index], row["literal"], row["replacement"])
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        lines[index] = re.sub(
            r"(?<![\w./-])(?:cli|sidecar|control|io|tests2)/[\w./-]+",
            lambda match: "../" + mapping["native/" + match[0]], line
        )
    # The relocated Session and document remain siblings. The generated S0
    # translation unit still uses the old include spelling as its match value.
    if not any('string(REPLACE "#include \\"../document/runtime_module_config.h\\""' in line for line in lines):
        raise ValueError("S0 source substitution seam drifted.")


def web_entry(lines):
    paths = {
        "modules2/macro_oscillator": "modules/macro_oscillator",
        "engine2/engine2.cpp": "engine/engine2.cpp",
        "engine2": "engine",
        "control/app_engine.cpp": "engine/control/app_engine.cpp",
        "control": "engine/control",
        "document/runtime_patch.cpp": "host/document/runtime_patch.cpp",
        "document": "host/document",
        "voice/allocator.cpp": "engine/voice/allocator.cpp",
        "voice": "engine/voice",
        "sdk": "sdk",
        "examples": "host/examples",
    }
    for index, line in enumerate(lines):
        if line == "set(native ${CMAKE_CURRENT_SOURCE_DIR}/..)":
            lines[index] = "set(native ${CMAKE_CURRENT_SOURCE_DIR}/../..)"
        elif "# Same pinned revisions" in line:
            lines[index] = replace_once(
                line, "native/document and native/modules2/macro_oscillator",
                "host/document and modules/macro_oscillator"
            )
        elif "${native}/" in line:
            def moved(match):
                if match[1] == "include":
                    return "${native}/sdk/include ${native}/engine/include ${native}/host/include"
                return "${native}/" + paths[match[1]]
            lines[index] = re.sub(r"\u0024\{native\}/([\w./-]+)", moved, line)


def plan(root, audit):
    result = []
    for source, destination, edit in (
        ("native/CMakeLists.txt", "native/CMakeLists.txt", lambda lines: native_entry(lines, audit)),
        ("native/web/CMakeLists.txt", "targets/web/CMakeLists.txt", web_entry),
    ):
        data = (root / source).read_bytes()
        before = data.decode().splitlines()
        after = before.copy()
        edit(after)
        result.append({"source": source, "destination": destination,
                       "source_sha256": hashlib.sha256(data).hexdigest(),
                       "replacements": [{"line": i, "before": old, "after": new}
                                        for i, (old, new) in enumerate(zip(before, after, strict=True), 1)
                                        if old != new]})
    return {"head": audit["head"], "ready_for_apply": False, "entry_point_edits": result}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("audit", type=Path)
    args = ap.parse_args()
    print(json.dumps(plan(args.root, json.loads(args.audit.read_text(encoding="utf-8"))),
                     sort_keys=True, indent=2))
