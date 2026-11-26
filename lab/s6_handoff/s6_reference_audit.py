# SPDX-License-Identifier: GPL-3.0-only
"""Classify S6 preview findings without changing the input checkout."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

PRESERVE_SYNTHETIC = {
    "bench/portability/tests/test_probe.py",
    "tools/ci/test_static_checks.py",
    "tools/foundation/tests/test_changed_scope.py",
    "tools/foundation/tests/test_launch_freshness.py",
    "tools/foundation/tests/test_reporting.py",
}
PRESERVE_TEXT = {
    ("apps/studio/tests/sequence-panel.spec.ts", "native/WASM"),
    ("bench/evidence/s7_1_193/test_collect.py", "native/device"),
    ("bench/offline/ui_profile_parse.cjs", "native/anonymous"),
    ("tools/dev.py", "native/Electron"),
    ("tools/dev.py", "native/tool"),
    ("tools/foundation/helpers.py", "native/tool"),
}
CMAKE_SUBDIRECTORIES = {
    "document": "../host/document document",
    "engine2": "../engine engine2",
    "tools/render": "../tools/render tools/render",
    "tools/capture": "../tools/capture tools/capture",
}
DIRECT_PATHS = {
    ("bench/sdk/out_of_tree_trial.py", "native/modules2/trial_gain"): "modules/trial_gain",
    ("tools/module/layout.json", "native/include"): "sdk/include",
    ("tools/pi/demo.sh", "native/examples/class_demo_"): "host/examples/class_demo_",
}
COORDINATED = {
    ".github/workflows/portability.yml": "Replace the old include glob with the union of SDK, engine and host include globs.",
    "bench/offline/r2_probe.py": "Use ordered include roots sdk/include and engine/include, preserving existing SDK and engine arguments.",
    "bench/portability/probe.py": "Preserve the old shared include visibility with ordered sdk/include, engine/include and host/include roots.",
    "native/web/CMakeLists.txt": "Re-anchor at the repository root and map each former native child individually; keep target names and flags.",
    "tools/foundation/tests/test_banned_includes.py": "Move scanner and fixture roots together: modules, sdk, and engine/voice. Preserve every assertion and exemption.",
}
BLIND_SPOTS = (
    (".github/workflows/", re.compile(r"""['"]native/\*\*['"]"""), "Expand trigger roots to retain coverage of moved code; retain native/ for the build entry."),
    ("tools/", re.compile(r"""(?:ROOT|root)\s*/\s*["']native["']\s*/\s*["'](?:sidecar|modules2|document|io|engine2|sdk|include|examples|voice|web|tests2?)["']"""), "Resolve chained Path segments using the approved destination."),
    ("tools/foundation/helpers.py", re.compile(r'for folder in .*"native"'), "Extend source-fingerprint inputs to every relocated source root."),
    ("native/CMakeLists.txt", re.compile(r"(?<![\w./-])(?:cli|control|sidecar|io|document|tests2)/[\w./-]+"), "Resolve bare CMake source and generated S0 paths while retaining existing binary paths and CTest names."),
    ("native/web/CMakeLists.txt", re.compile(r"\u0024\{native\}/[\w./-]+"), "Replace each use with its exact post-move directory after re-anchoring."),
)

def fmt(disposition, reason, replacement=None):
    item = {"disposition": disposition, "reason": reason}
    if replacement is not None:
        item["replacement"] = replacement
    return item

def classify(source, literal, kind, line):
    if source.startswith("ci/from-main/"):
        return fmt("preserve_history", "Retired workflow copy; active replacements must be handled separately.")
    if source.startswith("native/modules2/") and source.endswith("/DESIGN.md"):
        if re.search(r"Source:|DSP comes from|Original GPL", line):
            return fmt("preserve_history", "Provenance cites the pre-migration source at a historical revision.")
    if source in PRESERVE_SYNTHETIC:
        return fmt("preserve_synthetic_fixture", "Test deliberately constructs or quotes this synthetic path.")
    if (source, literal) in PRESERVE_TEXT:
        return fmt("preserve_nonpath_text", "Text or diagnostic category, with no filesystem lookup.")
    if (source, literal) in DIRECT_PATHS:
        return fmt("substitute", "Destination derived from the approved move map.", DIRECT_PATHS[source, literal])
    if source == "native/CMakeLists.txt" and kind == "add_subdirectory-binary-dir":
        return fmt("substitute", "Use moved source path with explicitly preserved binary subdirectory.",
                   CMAKE_SUBDIRECTORIES[literal])
    if source == "native/CMakeLists.txt" and literal == "${CMAKE_CURRENT_SOURCE_DIR}/include":
        return fmt("substitute", "Preserve all three former include roots for wirescape_osc_service and its consumers.",
                   "${CMAKE_CURRENT_SOURCE_DIR}/../sdk/include ${CMAKE_CURRENT_SOURCE_DIR}/../engine/include ${CMAKE_CURRENT_SOURCE_DIR}/../host/include")
    if source == "native/engine2/CMakeLists.txt":
        if "abi2_header_c99" in line:
            return fmt("substitute", "The C99 smoke compiles the public module header.",
                       "../sdk/include")
        if "wirescape_sdk2 INTERFACE" in line:
            return fmt("coordinated_substitution", "Keep public SDK header and all previous private header visibility after splitting includes.")
    if source in COORDINATED:
        return fmt("coordinated_substitution", COORDINATED[source])
    raise ValueError(f"Unclassified reference {source} {kind} {literal}: {line}")

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])

def build_audit(preview, root):
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if preview["head"] != head or git(root, "status", "--porcelain=v1"):
        raise ValueError("Preview head must match a clean checkout.")
    records = []
    for entry in preview["unresolved"]:
        source, literal = entry["source"], entry["literal"]
        data = (root / source).read_bytes()
        line = data.decode().splitlines()[entry["line"] - 1]
        if literal not in line:
            raise ValueError(f"Reference line drift: {source}:{entry['line']}")
        records.append({**entry, **classify(source, literal, entry["kind"], line),
                        "before_line": line, "source_sha256": hashlib.sha256(data).hexdigest()})
    followup = []
    for path in git(root, "ls-files", "-z").decode().split(chr(0)):
        if not path:
            continue
        rules = [(rule, reason) for prefix, rule, reason in BLIND_SPOTS if path.startswith(prefix)]
        if not rules:
            continue
        data = (root / path).read_bytes()
        if bytes([0]) in data:
            continue
        try:
            lines = data.decode().splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for rule, reason in rules:
                if rule.search(line):
                    followup.append({"source": path, "line": number, "before_line": line, "reason": reason,
                                     "source_sha256": hashlib.sha256(data).hexdigest()})
    return {
        "ready_for_apply": False,
        "head": head,
        "mapped": preview["mapped"],
        "moves": preview["moves"],
        "retained": preview["retained"],
        "move_map": preview["move_map"],
        "reference_dispositions": records,
        "counts": dict(Counter(item["disposition"] for item in records)),
        "unverified_preview_candidates": preview["candidate_edits"],
        "additional_reference_review": followup,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("preview", type=Path)
    args = parser.parse_args()
    with args.preview.open(encoding="utf-8") as fp:
        data = build_audit(json.load(fp), args.root)
    print(json.dumps(data, indent=2, sort_keys=True))
