#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-off inventory and optional wall-time runs of test suites."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]


def run(argv, cwd, execute, extra_env=None):
    started = time.perf_counter()
    if not execute:
        return {'command': argv, 'status': 'not executed', 'seconds': None, 'exit_code': None}
    try:
        proc = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, errors='replace',
                              timeout=900, env={**os.environ, 'CI': '1', 'GITHUB_ACTIONS': '1',
                                                **(extra_env or {})})
        result = {'command': argv, 'status': 'passed' if proc.returncode == 0 else 'failed',
                  'seconds': round(time.perf_counter() - started, 6),
                  'exit_code': proc.returncode, 'stdout_tail': proc.stdout[-100000:],
                  'stderr_tail': proc.stderr[-3000:]}
        if proc.returncode:
            # Staging redacts paths before keeping these 40 lines in committed facts.
            result['failure_output_lines'] = (proc.stdout.splitlines() + proc.stderr.splitlines())[-40:]
        return result
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'command': argv, 'status': 'unavailable', 'seconds': None,
                'exit_code': None, 'error': str(exc)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute', action='store_true', help='Execute test suites; no hardware flags are passed')
    ap.add_argument('--out', type=Path, default=ROOT / 'build_reports/l4/tests')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    git = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    record = {'commit': git, 'date_et': datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
              'machine': {'os': platform.platform(), 'cpu': platform.processor() or platform.machine(),
                          'architecture': platform.machine(), 'audio_devices': 'not accessed'},
              'tests_executed': args.execute, 'suites': {}}
    build = ROOT / 'build/native'
    # A multi-config Visual Studio generator needs -C for both listing and execution.
    config = ['-C', 'Release'] if os.name == 'nt' else []
    ctest = run(['ctest', '--test-dir', str(build), *config, '-N'], ROOT,
                build.joinpath('CTestTestfile.cmake').exists())
    count = len(re.findall(r'^\s*Test\s+#\d+:', ctest.get('stdout_tail', ''), re.MULTILINE)) if ctest.get('status') == 'passed' else None
    record['suites']['ctest'] = {'count': count, 'inventory': ctest,
                                 'run': run(['ctest', '--test-dir', str(build), *config,
                                             '--output-on-failure', '-j', '2'], ROOT,
                                            args.execute and count is not None)}
    # The sidecar protocol suite is a CTest subset; count it without re-running separately.
    if ctest.get('status') == 'passed':
        raw = ctest['stdout_tail']
        names = re.findall(r'^\s*Test\s+#\d+:\s+([^\n]+)', raw, re.MULTILINE)
        record['suites']['protocol'] = {'count': sum('sidecar' in n or 'protocol' in n for n in names),
                                         'method': 'CTest test names containing sidecar or protocol',
                                         'time': 'included in ctest suite'}
    else:
        record['suites']['protocol'] = {'count': None, 'status': 'CTest has not been configured'}
    unit_run = run(['python', '-m', 'unittest', 'discover', '-s', 'tools/foundation/tests', '-p', 'test*.py', '-v'], ROOT, args.execute)
    unit_count = re.search(r'Ran (\d+) tests?', unit_run.get('stderr_tail', ''))
    record['suites']['unittest'] = {'count': int(unit_count.group(1)) if unit_count else None,
       'method': 'python -m unittest discover tools/foundation/tests', 'run': unit_run}
    # npm package.json in apps/studio does not define a Vitest script at this commit.
    record['suites']['vitest'] = {'count': 0, 'status': 'no Vitest suite configured in package.json'}
    studio = ROOT / 'apps/studio'
    desktop = ROOT / 'apps/desktop'
    pw = studio / 'node_modules/playwright/cli.js'
    if pw.exists():
        for name, cwd, config in [('playwright_studio', studio, 'playwright.config.ts'),
                                  ('playwright_desktop', desktop, 'playwright.config.cjs')]:
            listing = run(['node', str(pw), 'test', '--config', config, '--list'], cwd, True)
            total = re.search(r'Total:\s*(\d+)\s+tests?', listing.get('stdout_tail', ''))
            record['suites'][name] = {'count': int(total.group(1)) if total else None,
                'inventory': listing,
                'run': run(['node', str(pw), 'test', '--config', config], cwd,
                           args.execute and listing.get('status') == 'passed',
                           {'WIRESCAPE_REAL_ENGINE': str(build / 'Release/wirescape-engine.exe')}
                           if name == 'playwright_desktop' and os.name == 'nt' else None)}
    else:
        for name in ('playwright_studio', 'playwright_desktop'):
            record['suites'][name] = {'count': None, 'status': 'npm ci required in apps/studio'}
    (args.out / 'summary.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    print(args.out / 'summary.json')


if __name__ == '__main__':
    main()
