# SPDX-License-Identifier: GPL-3.0-only
"""M1 S6 deterministic, read-only move/reference preview (issue #294).

This is a *proposal*, never a writer. It neither moves nor changes any file.
Run against a clean, exact-sha checkout, then review every reported reference
and unresolved entry before authorizing the eventual replay/apply script.

The verified mapping lives in m1_s6_map.py. Do not duplicate it here.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import posixpath
from pathlib import Path
import re
import subprocess
import sys

from m1_s6_map import repository_plan, git

# Files that can contain executable physical source-root references. Historical
# docs, facts and proposals are deliberately excluded from automatic rewrites.
TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".inc",
    ".cmake", ".py", ".js", ".cjs", ".mjs", ".ts", ".tsx",
    ".json", ".yml", ".yaml", ".sh", ".ps1", ".cmd", ".txt",
}
ACTIVE_PREFIXES = (".github/workflows/", "apps/", "bench/", "ci/", "tools/", "native/")
INCLUDE = re.compile(r'^\s*#\s*include\s*"([^"\n]+)"')
ROOT_PATH = re.compile(r'(?<![\w./-])native/[A-Za-z0-9_./+\-]+')
CMAKE_VAR = re.compile(r'\$\{(CMAKE_CURRENT_SOURCE_DIR|PROJECT_SOURCE_DIR|CMAKE_SOURCE_DIR)\}/([A-Za-z0-9_./+\-]+)')
CMAKE_REL = re.compile(r'(?<![\w$./-])(\.\./|\./)[A-Za-z0-9_./+\-]+')
CMAKE_ADD_SUBDIR = re.compile(r'\badd_subdirectory\(\s*([A-Za-z0-9_./+\-]+)\s*\)', re.I)


def tracked_paths(root: Path) -> list[str]:
    return sorted(v.decode('utf-8') for v in git(root, 'ls-files', '-z').split(bytes([0])) if v)


def directory_destinations(mapping: dict[str, str]) -> dict[str, set[str]]:
    """Old directory -> candidate new directory, respecting split include roots."""
    indexed: dict[str, set[str]] = defaultdict(set)
    for old, new in mapping.items():
        a, b = old.split('/'), new.split('/')
        for depth in range(1, len(a)):
            # Number of path components beneath this ancestor must be retained.
            suffix_count = len(a) - depth
            if len(b) < suffix_count:
                continue
            old_parent = '/'.join(a[:depth])
            new_parent = '/'.join(b[:-suffix_count])
            indexed[old_parent].add(new_parent)
    return indexed


def resolve_destination(path: str, mapping: dict[str, str], dirs: dict[str, set[str]]) -> tuple[str | None, str]:
    if path in mapping:
        return mapping[path], 'file'
    options = dirs.get(path, set())
    if len(options) == 1:
        return next(iter(options)), 'directory'
    if len(options) > 1:
        return None, 'ambiguous directory'
    return None, 'not tracked'


def mapped_relative(old_file: str, new_file: str, literal: str, mapping: dict[str, str], dirs: dict[str, set[str]]) -> tuple[str | None, str]:
    old_target = posixpath.normpath(posixpath.join(posixpath.dirname(old_file), literal))
    new_target, why = resolve_destination(old_target, mapping, dirs)
    if new_target is None:
        # Unmoved paths (e.g. apps/studio/patches) can still need a new relative
        # spelling when their referencing CMake/source file was moved.
        if old_target in dirs or old_target in mapping:
            return None, why
        new_target = old_target
        why = 'unmoved-or-unverified'
    return posixpath.relpath(new_target, posixpath.dirname(new_file)), why


def cma_ref(old_file: str, new_file: str, variable: str, literal: str,
            mapping: dict[str, str], dirs: dict[str, set[str]]) -> tuple[str | None, str]:
    """Handle deterministic CMake source-root literals conservatively."""
    if variable == 'CMAKE_CURRENT_SOURCE_DIR':
        oldbase, newbase = posixpath.dirname(old_file), posixpath.dirname(new_file)
    elif variable in ('PROJECT_SOURCE_DIR', 'CMAKE_SOURCE_DIR'):
        # native is the CMake project root, *except* standalone web which moves.
        if old_file.startswith('native/web/'):
            oldbase, newbase = 'native/web', 'targets/web'
        else:
            oldbase = newbase = 'native'
    else:
        raise ValueError(variable)
    old_target = posixpath.normpath(posixpath.join(oldbase, literal))
    new_target, why = resolve_destination(old_target, mapping, dirs)
    if new_target is None:
        if why == 'ambiguous directory':
            return None, why
        new_target = old_target
        why = 'unmoved-or-unverified'
    return posixpath.relpath(new_target, newbase), why


def collect_references(src: str, dst: str, content: str,
                       mapping: dict[str, str], dirs: dict[str, set[str]]) -> tuple[list[dict], list[dict]]:
    edits, blockers = [], []
    cmake = posixpath.basename(src) == 'CMakeLists.txt' or src.endswith('.cmake')
    for number, line in enumerate(content.splitlines(), 1):
        # Preserve the original line. A preview reports positions and replacement
        # candidates; it does not blindly modify comments, fixtures or protocols.
        include = INCLUDE.match(line)
        if include:
            literal = include.group(1)
            if literal.startswith('../') or literal.startswith('./'):
                replacement, why = mapped_relative(src, dst, literal, mapping, dirs)
                if replacement is None:
                    blockers.append({'source': src, 'line': number, 'kind': 'relative-include', 'literal': literal, 'why': why})
                elif replacement != literal:
                    edits.append({'source': src, 'target': dst, 'line': number, 'kind': 'relative-include', 'old': literal, 'new': replacement, 'why': why})

        for match in ROOT_PATH.finditer(line):
            literal = match.group(0).rstrip('.,:;')
            new, why = resolve_destination(literal.rstrip('/'), mapping, dirs)
            if new is None:
                blockers.append({'source': src, 'line': number, 'kind': 'root-physical-path', 'literal': literal, 'why': why})
            elif new != literal:
                edits.append({'source': src, 'target': dst, 'line': number, 'kind': 'root-physical-path', 'old': literal, 'new': new, 'why': why})

        if cmake:
            for match in CMAKE_VAR.finditer(line):
                variable, literal = match.groups()
                replacement, why = cma_ref(src, dst, variable, literal, mapping, dirs)
                if replacement is None:
                    blockers.append({'source': src, 'line': number, 'kind': 'cmake-variable', 'literal': match.group(0), 'why': why})
                elif replacement != literal:
                    edits.append({'source': src, 'target': dst, 'line': number, 'kind': 'cmake-variable', 'old': match.group(0), 'new': '$' + '{' + variable + '}/' + replacement, 'why': why})
            for match in CMAKE_REL.finditer(line):
                literal = match.group(0).rstrip('.,:;')
                replacement, why = mapped_relative(src, dst, literal, mapping, dirs)
                if replacement is None:
                    blockers.append({'source': src, 'line': number, 'kind': 'cmake-relative', 'literal': literal, 'why': why})
                elif replacement != literal:
                    edits.append({'source': src, 'target': dst, 'line': number, 'kind': 'cmake-relative', 'old': literal, 'new': replacement, 'why': why})
            for match in CMAKE_ADD_SUBDIR.finditer(line):
                literal = match.group(1)
                if literal.startswith('native/'):
                    continue  # ROOT_PATH handles it
                old_target = posixpath.normpath(posixpath.join(posixpath.dirname(src), literal))
                new_target, why = resolve_destination(old_target, mapping, dirs)
                if new_target is None:
                    blockers.append({'source': src, 'line': number, 'kind': 'add_subdirectory', 'literal': literal, 'why': why})
                elif new_target != old_target:
                    # When moving outside the CMake source tree, CMake requires a
                    # separate binary directory. This MUST be manually audited.
                    blockers.append({'source': src, 'line': number, 'kind': 'add_subdirectory-binary-dir',
                                     'literal': literal, 'suggest': new_target, 'why': 'requires explicit binary dir'})
    return edits, blockers


def source_candidate(path: str, mapping: dict[str, str]) -> bool:
    if path in mapping:
        return True
    if not path.startswith(ACTIVE_PREFIXES):
        return False
    return path.endswith('CMakeLists.txt') or posixpath.splitext(path)[1].lower() in TEXT_SUFFIXES


def preview(root: Path) -> dict:
    before = repository_plan(root)
    if not before['ok']:
        raise RuntimeError('STOP map preflight failed: ' + ', '.join(before['errors']))
    mapping = before['mapping']
    dirs = directory_destinations(mapping)
    files = tracked_paths(root)
    entries, unresolved, skipped = [], [], []
    for src in files:
        if not source_candidate(src, mapping):
            continue
        dst = mapping.get(src, src)
        data = (root / src).read_bytes()
        if b'\x00' in data:
            skipped.append({'source': src, 'reason': 'binary (preserved unchanged)'})
            continue
        try:
            content = data.decode('utf-8')
        except UnicodeDecodeError:
            skipped.append({'source': src, 'reason': 'non-UTF8 (preserved unchanged)'})
            continue
        edits, blockers = collect_references(src, dst, content, mapping, dirs)
        unresolved.extend(blockers)
        if edits:
            entries.append({'source': src, 'destination': dst,
                            'source_sha256': hashlib.sha256(data).hexdigest(), 'references': edits})
    return {'status': 'PREVIEW_ONLY_NO_WRITES', 'head': before['head'],
            'mapped': before['native_sources'], 'moves': before['moved'], 'retained': before['retained'],
            'move_map': [{'from': a, 'to': b} for a, b in sorted(mapping.items()) if a != b],
            'candidate_edits': entries, 'unresolved': unresolved, 'nontext': skipped,
            'ready_for_apply': False,
            'warning': 'Manual CMake/include/workflow review, complete rewrite manifest and full replay required before apply.'}


def self_test() -> None:
    mapping = {
        'native/modules2/quad_vca/dsp.h': 'modules/quad_vca/dsp.h',
        'native/control/module_catalog.h': 'engine/control/module_catalog.h',
        'native/CMakeLists.txt': 'native/CMakeLists.txt',
        'native/engine2/CMakeLists.txt': 'engine/CMakeLists.txt',
        'native/include/wirescape/module2.h': 'sdk/include/wirescape/module2.h',
        'native/include/wirescape/output_policy.h': 'host/include/wirescape/output_policy.h',
    }
    dirs = directory_destinations(mapping)
    assert resolve_destination('native/modules2/quad_vca', mapping, dirs)[0] == 'modules/quad_vca'
    assert resolve_destination('native/include', mapping, dirs)[1] == 'ambiguous directory'
    assert mapped_relative('native/control/module_catalog.h', 'engine/control/module_catalog.h',
                           '../modules2/quad_vca/dsp.h', mapping, dirs)[0] == '../../modules/quad_vca/dsp.h'
    edits, blockers = collect_references('native/control/module_catalog.h', 'engine/control/module_catalog.h',
                                        '#include "../modules2/quad_vca/dsp.h"\n', mapping, dirs)
    assert any(x['new'] == '../../modules/quad_vca/dsp.h' for x in edits), (edits, blockers)
    edits, blockers = collect_references('native/CMakeLists.txt', 'native/CMakeLists.txt',
                                        'add_subdirectory(engine2)\n', mapping, dirs)
    assert any(x['kind'] == 'add_subdirectory-binary-dir' for x in blockers)
    edits, blockers = collect_references('tools/gen.py', 'tools/gen.py',
                                        '"native/modules2/quad_vca/dsp.h"\n', mapping, dirs)
    assert any(x['new'] == 'modules/quad_vca/dsp.h' for x in edits)
    print('S6 no-write preview pure self-test PASS; no full-checkout execution implied')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        root = Path(git(args.root, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
        result = preview(root)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    # Always an explicit dry-run, never a successful apply or merge signal.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
