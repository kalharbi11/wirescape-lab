# SPDX-License-Identifier: GPL-3.0-only
"""Plan post-move gate and tool path changes without writing source files."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from s6_replay_moves import git


PRODUCT_ROOTS = ("engine", "host", "modules", "sdk", "targets", "tests/native")
TRIGGER_ROOTS = (*PRODUCT_ROOTS, "tools/render", "tools/capture")
TRIGGER_WORKFLOWS = (
    "golden-renders.yml", "instruction-gate.yml", "m1-stage-evidence.yml", "offline-facts.yml",
)
GLOBS = re.compile(r"""^(?P<prefix> +\- )(?P<quote>["'])native/\*\*(?P=quote)$""")
INCLUDE_GLOBS = re.compile(r'^(?P<prefix> +\- )"native/include/\*\*"$')
SUBSTITUTIONS = {
    "tools/cloud/git_deps.py": {'ROOT / "native" / "modules2"': 'ROOT / "modules"'},
    "tools/protocol/generate.py": {'ROOT / "native" / "sidecar"': 'ROOT / "host" / "sidecar"'},
    "tools/protocol/test_protocol.py": {'ROOT / "native" / "sidecar"': 'ROOT / "host" / "sidecar"'},
    "tools/protocol/validate_sidecar.py": {'ROOT / "native" / "sidecar"': 'ROOT / "host" / "sidecar"'},
    "tools/foundation/tests/test_banned_includes.py": {
        "('native/modules2', 'native/sdk', 'native/voice')": "('modules', 'sdk', 'engine/voice')",
        "directory != 'native/modules2'": "directory != 'modules'",
        "for tree in ('modules2', 'sdk', 'voice'):": "for tree in ('modules', 'sdk', 'engine/voice'):",
        "root / 'native' / tree / 'nested/test.cpp'": "root / tree / 'nested/test.cpp'",
        "'native/modules2/example'": "'modules/example'",
        "'native/modules2/example/dsp.h'": "'modules/example/dsp.h'",
    },
}


def globs(line, expressions, paths, preserve_original):
    match = expressions.fullmatch(line)
    if not match:
        return line
    quote = match.groupdict().get("quote", '"')
    entries = [line] if preserve_original else []
    entries += [f"{match['prefix']}{quote}{path}/**{quote}" for path in paths]
    return "\n".join(entries)


def physical_substitutions(lines, pairs):
    for old, new in pairs.items():
        matching = [i for i, line in enumerate(lines) if old in line]
        if len(matching) != 1 or lines[matching[0]].count(old) != 1:
            raise ValueError(f"Fail closed on path substitution {old!r}")
        i, = matching
        lines[i] = lines[i].replace(old, new, 1)
    return lines


def collect(root, head):
    roots = ("native", *PRODUCT_ROOTS, "tools")
    root_args = ", ".join(f'root / "{name}"' for name in roots)
    specs = {
        **{f".github/workflows/{name}":
           lambda lines: [globs(line, GLOBS, TRIGGER_ROOTS, True) for line in lines]
           for name in TRIGGER_WORKFLOWS},
        ".github/workflows/portability.yml":
            lambda lines: [globs(line, INCLUDE_GLOBS, ("sdk/include", "engine/include", "host/include"), False)
                           for line in lines],
        "tools/foundation/helpers.py": lambda lines: physical_substitutions(lines, {
            'for folder in (root / "native", root / "tools"):': f"for folder in ({root_args}):",
            'native/ and tools/ excluding __pycache__':
                ", ".join(f"{p}/" for p in roots) + " excluding __pycache__",
        }),
        **{path: (lambda lines, changes=changes: physical_substitutions(lines, changes))
           for path, changes in SUBSTITUTIONS.items()},
    }
    records = []
    for source, action in specs.items():
        raw = (root / source).read_bytes()
        before = raw.decode().splitlines()
        after = action(before.copy())
        replacements = [{"line": i, "before": old, "after": new}
                        for i, (old, new) in enumerate(zip(before, after, strict=True), 1)
                        if old != new]
        if not replacements:
            raise ValueError(f"No changes planned for {source}")
        records.append({"source": source, "destination": source,
                        "source_sha256": hashlib.sha256(git(root, "show", f"HEAD:{source}")).hexdigest(), "replacements": replacements})
    return {"head": head, "ready_for_apply": False, "entry_point_edits": records}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("head")
    args = ap.parse_args()
    print(json.dumps(collect(args.root, args.head), indent=2, sort_keys=True))
