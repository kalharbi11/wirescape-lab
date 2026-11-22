#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Offline, device-free repository inventory. Outputs are outside the source tree."""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
LANG = {'.cpp': 'C++', '.cc': 'C++', '.c': 'C', '.h': 'C/C++ header', '.hpp': 'C/C++ header',
        '.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript', '.cjs': 'JavaScript',
        '.mjs': 'JavaScript', '.py': 'Python', '.sh': 'Shell', '.css': 'CSS', '.html': 'HTML',
        '.cmake': 'CMake'}
EXCLUDED = {'node_modules', '.git', 'dist', 'build', 'build_reports', '.tools', 'vendor'}
CXX = {'.cpp', '.cc', '.h', '.hpp', '.c'}


def command(args, *, check=True):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def tracked():
    return [ROOT / p.decode() for p in subprocess.check_output(
        ['git', '-C', str(ROOT), 'ls-files', '-z']).split(b'\0') if p
        and not any(x in EXCLUDED for x in Path(os.fsdecode(p)).parts)]


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def machine():
    return {'os': platform.platform(), 'architecture': platform.machine(),
            'cpu': platform.processor() or platform.machine(), 'audio_devices': 'not accessed'}


def complexity(paths, dest):
    try:
        import lizard  # type: ignore
    except ImportError:
        return 'not measured: python package lizard is not installed'
    rows = []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        if (path.suffix not in CXX | {'.ts', '.tsx', '.js'} or
                not (rel.startswith(('native/', 'engine/', 'host/', 'modules/', 'sdk/', 'targets/', 'tests/native/', 'tools/render/', 'tools/capture/')) or rel.startswith('apps/studio/src/'))):
            continue
        try:
            data = lizard.analyze_file(str(path))
            for func in data.function_list:
                rows.append(dict(path=rel, name=func.long_name, start_line=func.start_line,
                                 end_line=func.end_line, length=func.length,
                                 nloc=func.nloc, cyclomatic_complexity=func.cyclomatic_complexity))
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(f'{rel}: {exc}') from exc
    columns = ['path', 'name', 'start_line', 'end_line', 'length', 'nloc', 'cyclomatic_complexity']
    write_csv(dest / 'complexity_top30.csv', sorted(rows,
              key=lambda r: (-r['cyclomatic_complexity'], -r['length'], r['path']))[:30], columns)
    write_csv(dest / 'length_top30.csv', sorted(rows,
              key=lambda r: (-r['length'], -r['cyclomatic_complexity'], r['path']))[:30], columns)
    return {'functions': len(rows), 'lizard_version': getattr(lizard, '__version__', 'not exposed')}


def cloc(paths, dest):
    if not shutil.which('cloc'):
        return 'not measured: cloc executable is not installed'
    candidates = [str(p.relative_to(ROOT)) for p in paths if p.suffix in LANG]
    result = command(['cloc', '--quiet', '--json', '--by-file', *candidates], check=False)
    if result.returncode:
        return f'cloc exit {result.returncode}: {result.stderr[:200]}'
    parsed = json.loads(result.stdout)
    rows = []
    for key, value in parsed.items():
        if not isinstance(value, dict) or not {'code', 'blank', 'comment'} <= value.keys():
            continue
        parts = Path(key).parts
        if not parts:
            continue
        section = 'tests' if any(p in {'tests', 'tests2', '__tests__'} for p in parts) or 'test_' in Path(key).name or Path(key).name.endswith(('.spec.ts', '.spec.cjs')) else 'tools' if parts[0] in {'tools', 'bench', 'ci'} else 'product'
        rows.append(dict(path=key, top_level=parts[0], section=section,
                         language=value.get('language', LANG.get(Path(key).suffix, 'unknown')),
                         code=value['code'], comment=value['comment'], blank=value['blank']))
    write_csv(dest / 'loc_by_file.csv', rows, ['path', 'top_level', 'section', 'language', 'code', 'comment', 'blank'])
    sums = collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        accum = sums[(r['top_level'], r['section'], r['language'])]
        accum[0] += 1
        for j, field in enumerate(('code', 'comment', 'blank'), start=1):
            accum[j] += r[field]
    write_csv(dest / 'loc_by_group.csv', [dict(top_level=k[0], section=k[1], language=k[2],
              files=v[0], code=v[1], comment=v[2], blank=v[3]) for k, v in sorted(sums.items())],
              ['top_level', 'section', 'language', 'files', 'code', 'comment', 'blank'])
    return {'files': len(rows), 'cloc': shutil.which('cloc')}


def long_lines(paths, dest):
    rows = []
    for path in paths:
        if not path.is_file() or path.suffix not in CXX or not path.relative_to(ROOT).as_posix().startswith(('native/', 'engine/', 'host/', 'modules/', 'sdk/', 'targets/', 'tests/native/', 'tools/render/', 'tools/capture/')):
            continue
        lengths = [len(line) for line in path.read_text(encoding='utf-8', errors='replace').splitlines()]
        rows.append({'path': path.relative_to(ROOT).as_posix(), 'over_120': sum(n > 120 for n in lengths),
                     'over_200': sum(n > 200 for n in lengths), 'max_chars': max(lengths, default=0)})
    write_csv(dest / 'native_long_lines.csv', sorted(rows, key=lambda r: r['path']),
              ['path', 'over_120', 'over_200', 'max_chars'])
    return {'files': len(rows), 'over_120': sum(r['over_120'] for r in rows),
            'over_200': sum(r['over_200'] for r in rows)}


def includes(paths, dest):
    rows = []
    regex = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', flags=re.MULTILINE)
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or path.suffix not in CXX or not rel.startswith(('engine/', 'host/sidecar/')) or rel.startswith(('engine/voice/', 'engine/include/')):
            continue
        for header in regex.findall(path.read_text(encoding='utf-8', errors='replace')):
            rows.append({'source': rel, 'header': header, 'area': rel.split('/')[1]})
    write_csv(dest / 'direct_includes.csv', sorted(rows, key=lambda r: (r['area'], r['source'], r['header'])),
              ['area', 'source', 'header'])
    return {'direct_includes': len(rows), 'files': len(set(r['source'] for r in rows))}


def residue(paths, dest):
    rules = {'abi1_symbols': re.compile(r'\b(?:ws_engine|ws_module|ws_port|ws_parameter|ws_engine_config|ws_module_descriptor)\w*\b'),
             'qt_mentions': re.compile(r'(?i)\b(?:qt|qtcore|qml|qt-free|qt quick)\b'),
             'issue_refs': re.compile(r'(?<!\w)#\d+\b'),
             'agent_names': re.compile(r'(?i)\b(?:gpt-builder\d+|claude-builder\d+|gpt-helper|gpt-reviewer|claude-reviewer|fable|keel)\b')}
    rows = []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or not rel.startswith(('native/', 'engine/', 'host/', 'modules/', 'sdk/', 'targets/', 'tests/native/', 'apps/', 'tools/')) or path.suffix not in {'.cpp', '.h', '.hpp', '.py', '.ts', '.tsx', '.js', '.cjs', '.md', '.cmake'}:
            continue
        source = path.read_text(encoding='utf-8', errors='replace')
        row = {'path': rel, **{key: len(regex.findall(source)) for key, regex in rules.items()}}
        if any(row[key] for key in rules):
            rows.append(row)
    write_csv(dest / 'residue_by_file.csv', rows, ['path', *rules])
    return {'scope': 'native/, engine/, host/, modules/, sdk/, targets/, tests/native/, apps/, tools/ tracked text files', 'patterns': {k: v.pattern for k, v in rules.items()},
            'totals': {k: sum(row[k] for row in rows) for k in rules}, 'matched_files': len(rows)}


def graph(dest):
    cmake = shutil.which('cmake')
    if not cmake:
        return 'not measured: cmake missing'
    build = ROOT / 'build' / 'l4-graph'
    build.mkdir(parents=True, exist_ok=True)
    dotfile = dest / 'cmake-targets.dot'
    proc = command([cmake, '-S', 'native', '-B', str(build), '-DCMAKE_BUILD_TYPE=Release',
                    f'--graphviz={dotfile}'], check=False)
    if proc.returncode or not dotfile.exists():
        return f'not measured: cmake configure exit {proc.returncode}: {proc.stderr[-250:]}'
    raw = dotfile.read_text()
    nodes = dict(re.findall(r'"(node\d+)"\s*\[\s*label\s*=\s*"([^"]+)"', raw))
    edges = re.findall(r'"(node\d+)"\s*->\s*"(node\d+)"', raw)
    linked = collections.defaultdict(set)
    used = collections.defaultdict(set)
    for src, dst in edges:
        if src in nodes and dst in nodes:
            linked[nodes[src]].add(nodes[dst]); used[nodes[dst]].add(nodes[src])
    write_csv(dest / 'cmake-targets.csv', [{'target': name, 'links': ';'.join(sorted(linked[name])),
              'used_by': ';'.join(sorted(used[name]))} for name in sorted(nodes.values())],
              ['target', 'links', 'used_by'])
    if shutil.which('dot'):
        subprocess.run(['dot', '-Tsvg', str(dotfile), '-o', str(dest / 'cmake-targets.svg')], check=True)
    return {'targets': len(nodes), 'edges': len(edges), 'svg': shutil.which('dot') is not None}


def binary_sizes(dest):
    paths = [ROOT / 'build/native', ROOT / 'apps/studio/dist', ROOT / 'apps/desktop/build']
    rows = []
    for base in paths:
        if not base.is_dir():
            rows.append({'path': base.relative_to(ROOT).as_posix(), 'bytes': '', 'kind': 'missing'})
            continue
        for p in base.rglob('*'):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if (base.name != 'native' or p.name == 'wirescape-engine' or 'wirescape_engine' in p.name
                    or p.name.startswith(('ws_', 'libws_')) or p.suffix in {'.a', '.o', '.so'}):
                rows.append({'path': rel, 'bytes': p.stat().st_size, 'kind': 'file'})
    write_csv(dest / 'binary_sizes.csv', rows, ['path', 'bytes', 'kind'])
    return {'files': sum(r['kind'] == 'file' for r in rows), 'missing_roots': sum(r['kind'] == 'missing' for r in rows)}


def dependencies(dest):
    rows = []
    for pkg in ('apps/studio/package-lock.json', 'apps/desktop/package-lock.json'):
        src = ROOT / pkg
        if src.is_file():
            data = json.loads(src.read_text(encoding='utf-8'))
            for name, rec in data.get('packages', {}).items():
                if name.startswith('node_modules/'):
                    rows.append({'name': name[len('node_modules/'):], 'version_or_commit': rec.get('version', ''),
                                 'license': rec.get('license', 'not specified in lock'), 'pinned_at': pkg})
    for src in [p for r in ('native', 'engine', 'host', 'modules', 'sdk', 'targets', 'tests/native', 'tools/render', 'tools/capture') for p in (ROOT / r).rglob('CMakeLists.txt')]:
        data = src.read_text(encoding='utf-8', errors='replace')
        for match in re.finditer(r'(?is)FetchContent_Declare\s*\(\s*([A-Za-z0-9_]+)(.*?)\)', data):
            block = match.group(2)
            pin = re.search(r'GIT_TAG\s+(\S+)', block)
            rows.append({'name': match.group(1), 'version_or_commit': pin.group(1) if pin else 'not specified',
                         'license': 'see vendor source / licence file', 'pinned_at': src.relative_to(ROOT).as_posix()})
    write_csv(dest / 'dependencies.csv', sorted(rows, key=lambda r: (r['pinned_at'], r['name'])),
              ['name', 'version_or_commit', 'license', 'pinned_at'])
    return {'entries': len(rows), 'note': 'Native licences require the dependency licence files; npm lock licences may be absent.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'build_reports/l4/repo')
    args = parser.parse_args()
    dest = args.out.resolve(); dest.mkdir(parents=True, exist_ok=True)
    paths = tracked()
    record = {'commit': command(['git', 'rev-parse', 'HEAD']).stdout.strip(),
              'date_et': dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
              'machine': machine(), 'source_files_tracked': len(paths),
              'methods': {'loc': 'cloc --json --by-file', 'complexity': 'lizard function analyzer',
                          'long_lines': 'Python len of each physical line', 'includes': 'literal #include directives',
                          'residue': 'Python regex patterns recorded below'}}
    for name, fn in [('loc', lambda: cloc(paths, dest)), ('complexity', lambda: complexity(paths, dest)),
                     ('long_lines', lambda: long_lines(paths, dest)), ('includes', lambda: includes(paths, dest)),
                     ('residue', lambda: residue(paths, dest)), ('graph', lambda: graph(dest)),
                     ('binary_sizes', lambda: binary_sizes(dest)), ('dependencies', lambda: dependencies(dest))]:
        try:
            record[name] = fn()
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
            record[name] = f'not measured: {type(exc).__name__}: {exc}'
    (dest / 'summary.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    print(dest / 'summary.json')


if __name__ == '__main__':
    main()
