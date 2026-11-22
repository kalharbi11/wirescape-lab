# SPDX-License-Identifier: GPL-3.0-only
"""Plan path-only wiring for relocated CMake subprojects."""
import argparse
import hashlib
import json
from pathlib import Path
import re


ENGINE_RELATIVE = {
    "voice": "voice", "tests2": "../tests/native/abi2", "modules2": "../modules",
    "io": "../host", "control": "control", "cli": "../host/cli",
}
ENGINE_ARGUMENT = re.compile(r'(?<![\w./-])\.\./(' + "|".join(ENGINE_RELATIVE) + r')(?=/|[ )"\t])')
ENGINE_INCLUDE = "${CMAKE_CURRENT_SOURCE_DIR}/../include"
REWIRES = {
    "native/document/CMakeLists.txt": {
        "../tests2/": "../../tests/native/abi2/",
        "${PROJECT_SOURCE_DIR}/examples": "${PROJECT_SOURCE_DIR}/../host/examples",
        "${PROJECT_SOURCE_DIR}/cli/": "${PROJECT_SOURCE_DIR}/../host/cli/",
        "../tests/golden_render.cpp": "../../tests/native/compat/golden_render.cpp",
    },
    "native/io/midi/CMakeLists.txt": {
        "../../tests2/": "../../tests/native/abi2/",
        "../../modules2/": "../../modules/",
    },
    "native/tools/render/CMakeLists.txt": {
        "${CMAKE_CURRENT_SOURCE_DIR}/../../../apps/": "${CMAKE_CURRENT_SOURCE_DIR}/../../apps/",
    },
}


def engine(line):
    if "wirescape_sdk2 INTERFACE" in line and ENGINE_INCLUDE in line:
        return line.replace(ENGINE_INCLUDE, " ".join(
            "${CMAKE_CURRENT_SOURCE_DIR}/" + root
            for root in ("../sdk/include", "include", "../host/include")))
    if "abi2_header_c99 PRIVATE ../include" in line:
        return line.replace("../include", "../sdk/include")
    line = ENGINE_ARGUMENT.sub(lambda m: ENGINE_RELATIVE[m[1]], line)
    for old, new in (
        ("${CMAKE_CURRENT_SOURCE_DIR}/../../", "${CMAKE_CURRENT_SOURCE_DIR}/../"),
        ("${CMAKE_SOURCE_DIR}/tests/fixtures/abi2", "${CMAKE_SOURCE_DIR}/../tests/native/compat/fixtures/abi2"),
        ("${PROJECT_SOURCE_DIR}/examples/", "${PROJECT_SOURCE_DIR}/../host/examples/"),
    ):
        line = line.replace(old, new)
    return line


def transform(source, line):
    if line.lstrip().startswith("#"):
        return line
    if source == "native/engine2/CMakeLists.txt":
        return engine(line)
    for old, new in REWIRES.get(source, {"../../tests2/": "../../tests/native/abi2/"}).items():
        line = line.replace(old, new)
    return line


def make_plan(root, audit):
    records = []
    for item in audit["move_map"]:
        src, dst = item["from"], item["to"]
        if not (src in REWIRES or src == "native/engine2/CMakeLists.txt"
                or (src.startswith("native/modules2/") and src.endswith("/CMakeLists.txt"))):
            continue
        raw = (root / src).read_bytes()
        changes = []
        for number, original in enumerate(raw.decode().splitlines(), 1):
            updated = transform(src, original)
            if original != updated:
                changes.append({"line": number, "before": original, "after": updated})
        if changes:
            records.append({"source": src, "destination": dst,
                            "source_sha256": hashlib.sha256(raw).hexdigest(), "replacements": changes})
    return {"head": audit["head"], "ready_for_apply": False, "entry_point_edits": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("audit", type=Path)
    args = parser.parse_args()
    print(json.dumps(make_plan(args.root, json.loads(args.audit.read_text(encoding="utf-8"))),
                     indent=2, sort_keys=True))
