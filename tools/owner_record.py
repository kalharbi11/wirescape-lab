#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Owner-run, device-off test record for Windows and Raspberry Pi.

Runs the existing device-free checks on an already built checkout and writes one
zip you can upload to a GitHub issue. It never opens audio, MIDI or LAN devices,
never installs anything and never changes tracked files.

  python3 tools/owner_record.py --tier quick      # ~10 min
  python3 tools/owner_record.py --tier standard   # ~45 min
  python3 tools/owner_record.py --tier long       # ~2.5 h (1 h edit soak, 60 s per module)

Output: build_reports/owner-record/<name>.zip (record.json, summary.md, logs/).
Home folder and user name are replaced in every log before zipping.
Build first: Windows `tools\\windows\\setup.ps1 -Ref <sha>`, Pi `sh tools/pi/update-and-build.sh <sha>`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'build' / 'native'
EXE = '.exe' if os.name == 'nt' else ''
RATE, BLOCK = 48000, 128
PERIOD_NS = 1e9 * BLOCK / RATE
# I/O and host modules have no deterministic audio path in the probe.
SKIP_PREFIXES = ('host.', 'midi.', 'osc.', 'monitor', 'essentials.output')
TIERS = {
    'quick': dict(bench_blocks=1024, module_seconds=5, soak_seconds=60, chaos=False),
    'standard': dict(bench_blocks=8192, module_seconds=20, soak_seconds=600, chaos=True),
    'long': dict(bench_blocks=32768, module_seconds=60, soak_seconds=3600, chaos=True),
}


def redact(text: str) -> str:
    home = str(Path.home())
    for needle in {home, home.replace('\\', '/')} - {'', '/'}:
        text = text.replace(needle, '~')
    user = getpass.getuser()
    if len(user) >= 3:
        text = re.sub(re.escape(user), '<user>', text, flags=re.IGNORECASE)
    return text.replace(str(ROOT), '<repo>').replace(str(ROOT).replace('\\', '/'), '<repo>')


def binary(name: str) -> Path | None:
    for folder in (NATIVE / 'Release', NATIVE):
        candidate = folder / f'{name}{EXE}'
        if candidate.is_file():
            return candidate
    return None


def read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace').strip().strip('\x00')
    except OSError:
        return None


def system_info() -> dict:
    info = {'os': platform.system(), 'release': platform.release(), 'machine': platform.machine(),
            'python': platform.python_version(), 'cpus': os.cpu_count(),
            'pi_model': read('/proc/device-tree/model'),
            'governor': read('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')}
    meminfo = read('/proc/meminfo') or ''
    match = re.search(r'MemTotal:\s+(\d+)', meminfo)
    info['mem_mib'] = int(match.group(1)) // 1024 if match else None
    if sys.platform.startswith('linux'):
        try:
            release = platform.freedesktop_os_release()
            info['distro'] = f"{release.get('ID')} {release.get('VERSION_ID')}"
        except OSError:
            pass
    else:
        info['processor'] = platform.processor()
    for tool, args in (('node', ['--version']), ('cmake', ['--version'])):
        path = shutil.which(tool)
        if path:
            try:
                out = subprocess.run([path, *args], capture_output=True, text=True, timeout=20).stdout
                info[tool] = out.splitlines()[0].strip() if out else None
            except (OSError, subprocess.SubprocessError):
                info[tool] = None
    return info


def git_info() -> dict:
    def git(*args):
        try:
            return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True,
                                  text=True, timeout=30).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ''
    return {'sha': git('rev-parse', 'HEAD'), 'dirty': bool(git('status', '--porcelain')),
            'describe': git('describe', '--always', '--tags')}


class ThermalSampler(threading.Thread):
    """Pi only: CPU temperature and throttle flags every 10 s while the record runs."""

    def __init__(self):
        super().__init__(daemon=True)
        self.samples, self.stop = [], threading.Event()
        self.vcgencmd = shutil.which('vcgencmd')

    def sample(self):
        raw = read('/sys/class/thermal/thermal_zone0/temp')
        row = {'t': round(time.monotonic(), 1), 'temp_c': int(raw) / 1000 if raw and raw.isdigit() else None}
        if self.vcgencmd:
            try:
                row['throttled'] = subprocess.run([self.vcgencmd, 'get_throttled'], capture_output=True,
                                                  text=True, timeout=5).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                pass
        self.samples.append(row)

    def run(self):
        while not self.stop.wait(10):
            self.sample()

    def summary(self):
        temps = [s['temp_c'] for s in self.samples if s.get('temp_c') is not None]
        flags = sorted({s['throttled'] for s in self.samples if s.get('throttled')})
        return {'samples': len(self.samples), 'max_temp_c': max(temps) if temps else None,
                'min_temp_c': min(temps) if temps else None, 'throttled_values': flags}


class Record:
    def __init__(self, out: Path):
        self.out, self.steps = out, []
        (out / 'logs').mkdir(parents=True, exist_ok=True)

    def run(self, name: str, command: list[str], timeout: float, parse=None) -> dict:
        print(f'[{time.strftime("%H:%M:%S")}] {name}: {" ".join(Path(c).name if i == 0 else c for i, c in enumerate(command))}',
              flush=True)
        start = time.monotonic()
        step = {'name': name, 'command': redact(' '.join(command))}
        try:
            proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                                  encoding='utf-8', errors='replace')
            step['exit_code'], stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            step['exit_code'], stdout = 'timeout', (exc.stdout or b'')
            stdout = stdout.decode('utf-8', 'replace') if isinstance(stdout, bytes) else stdout
            stderr = f'timed out after {timeout} s'
        except OSError as exc:
            step['exit_code'], stdout, stderr = 'oserror', '', str(exc)
        step['seconds'] = round(time.monotonic() - start, 1)
        (self.out / 'logs' / f'{name}.log').write_text(
            redact(f'$ {" ".join(command)}\n--- stdout\n{stdout}\n--- stderr\n{stderr}\n'), encoding='utf-8')
        step['status'] = 'passed' if step['exit_code'] == 0 else 'failed'
        if parse:
            try:
                step['result'] = parse(stdout)
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                step['parse_error'] = str(exc)
                step['status'] = 'failed'
        print(f'    -> {step["status"]} ({step["seconds"]} s)', flush=True)
        self.steps.append(step)
        return step

    def skip(self, name: str, why: str):
        print(f'    {name}: skipped ({why})', flush=True)
        self.steps.append({'name': name, 'status': 'skipped', 'reason': why})


def last_json(stdout: str):
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith('{'):
            return json.loads(line)
    return json.loads(stdout)


def probe_json(stdout: str):
    for line in stdout.splitlines():
        if line.startswith('module_cpu_probe '):
            return json.loads(line[len('module_cpu_probe '):])
    raise ValueError('no module_cpu_probe line')


def module_ids() -> list[str]:
    ids = []
    for path in sorted((ROOT / 'modules').glob('*/module.json')):
        try:
            ids.append(json.loads(path.read_text(encoding='utf-8'))['id'])
        except (OSError, ValueError, KeyError):
            continue
    return [i for i in ids if not i.startswith(SKIP_PREFIXES)]


def summarize(meta: dict, steps: list[dict]) -> str:
    lines = [f"# Wirescape owner record: {meta['git']['sha'][:12]} ({meta['tier']})", '',
             f"- When (UTC): {meta['started_utc']} → {meta['finished_utc']}",
             f"- Commit: `{meta['git']['sha']}`{' **(dirty tree)**' if meta['git']['dirty'] else ''}",
             f"- System: {meta['system'].get('pi_model') or meta['system']['os']} · {meta['system']['machine']} · "
             f"{meta['system'].get('cpus')} CPUs · {meta['system'].get('mem_mib')} MiB · "
             f"{meta['system'].get('distro') or meta['system']['release']}"]
    if meta.get('thermal', {}).get('samples'):
        t = meta['thermal']
        lines.append(f"- Pi temperature: {t['min_temp_c']}–{t['max_temp_c']} °C; throttled: {', '.join(t['throttled_values']) or 'n/a'}")
    passed = sum(s['status'] == 'passed' for s in steps)
    failed = [s['name'] for s in steps if s['status'] == 'failed']
    lines += [f"- Steps: {passed} passed, {len(failed)} failed, "
              f"{sum(s['status'] == 'skipped' for s in steps)} skipped", '']
    if failed:
        lines += ['**Failed:** ' + ', '.join(failed), '']
    lines += ['| Step | Status | Seconds | Key numbers |', '|---|---|---|---|']
    for s in steps:
        key = ''
        r = s.get('result')
        if isinstance(r, dict) and 'render_ns' in r:
            worst = float(r['render_ns']['max'])
            key = (f"p99 {float(r['render_ns']['p99']) / PERIOD_NS:.1%} · worst {worst / PERIOD_NS:.1%} of period · "
                   f"alloc {r.get('allocations')} · faults {r.get('faults')}")
        elif isinstance(r, dict) and s['name'].startswith('edit_soak'):
            perf = r.get('performance_evidence') or {}
            key = ', '.join([f'{k}={r[k]}' for k in ('status', 'cycles', 'steps', 'error') if k in r]
                            + [f'{k}={perf[k]}' for k in ('blocks', 'overruns', 'faults', 'p99', 'max') if k in perf])
        elif s.get('reason'):
            key = s['reason']
        lines.append(f"| {s['name']} | {s['status']} | {s.get('seconds', '')} | {key} |")
    lines += ['', 'Device-off record. Hosted or Xvfb numbers are diagnostics; sound, MIDI and xruns',
              'with real devices come from the owner acceptance session, not this record.']
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--tier', choices=TIERS, default='standard')
    parser.add_argument('--skip-tests', action='store_true', help='skip ctest (already run by setup)')
    parser.add_argument('--app-smoke', action='store_true', help='Pi: also run tools/pi/app_smoke.py (needs a desktop session)')
    parser.add_argument('--out', type=Path, default=ROOT / 'build_reports' / 'owner-record')
    args = parser.parse_args(argv)
    tier = TIERS[args.tier]
    started = dt.datetime.now(dt.timezone.utc)
    git = git_info()
    kind = 'pi' if (read('/proc/device-tree/model') or '').startswith('Raspberry Pi') else platform.system().lower()
    name = f"owner-record-{git['sha'][:9] or 'nogit'}-{kind}-{args.tier}-{started:%Y%m%dT%H%M%SZ}"
    out = args.out / name
    record = Record(out)
    py = sys.executable
    thermal = ThermalSampler()
    if kind == 'pi':
        thermal.sample()
        thermal.start()
    print(f'Wirescape owner record ({args.tier}) at {git["sha"][:12]}; devices stay off.\nWriting {out}', flush=True)
    if git['dirty']:
        print('Note: the working tree has local changes; the record marks it dirty.', flush=True)

    if binary('wirescape-engine') is None:
        record.steps.append({'name': 'build_check', 'status': 'failed',
                             'reason': 'no Release build under build/native; build first (see docstring)'})
        print('    build_check: failed (no Release build under build/native; build first)', flush=True)
    else:
        record.steps.append({'name': 'build_check', 'status': 'passed',
                             'engine': redact(str(binary('wirescape-engine')))})
        if args.skip_tests:
            record.skip('ctest', '--skip-tests')
        else:
            record.run('ctest', [py, 'tools/dev.py', 'test', '--json'], timeout=3600, parse=lambda s: {
                k: v for k, v in json.loads(s).items() if k in ('status', 'summary')})
        record.run('engine_benchmark', [py, 'tools/dev.py', 'benchmark', '--blocks', str(tier['bench_blocks']), '--json'],
                   timeout=3600, parse=lambda s: json.loads(s).get('benchmark'))
        probe = binary('abi2_module_cpu_probe')
        if probe is None:
            record.skip('module_cpu', 'abi2_module_cpu_probe not built')
        else:
            seconds = tier['module_seconds']
            for module in module_ids():
                record.run(f'module_cpu.{module}', [str(probe), '--module', module, '--instances', '2', '--rate',
                                                    str(RATE), '--block', str(BLOCK), '--seconds', str(seconds),
                                                    '--channels', '1'], timeout=seconds * 4 + 60, parse=probe_json)
        soak = binary('wirescape_soak')
        if tier['chaos'] and soak is not None:
            record.run('chaos_two_120s', [str(soak), '--patch', str(ROOT / 'host/examples/chaos_two.json'), '--rate',
                                          str(RATE), '--block', str(BLOCK), '--seconds', '120'], timeout=240,
                       parse=lambda s: json.loads(s))
        elif tier['chaos']:
            record.skip('chaos_two_120s', 'wirescape_soak not built')
        record.run(f'edit_soak_{tier["soak_seconds"]}s',
                   [py, 'tools/sidecar_edit_soak.py', '--seconds', str(tier['soak_seconds'])],
                   timeout=tier['soak_seconds'] * 2 + 300, parse=last_json)
    if args.app_smoke and kind == 'pi':
        record.run('pi_app_smoke', [py, 'tools/pi/app_smoke.py', '--report', 'build_reports/pi-app-smoke'], timeout=1800)

    thermal.stop.set()
    meta = {'schema': 'wirescape-owner-record/1', 'tier': args.tier, 'kind': kind, 'git': git,
            'system': system_info(), 'started_utc': f'{started:%Y-%m-%dT%H:%M:%SZ}',
            'finished_utc': f'{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}'}
    if kind == 'pi':
        meta['thermal'] = thermal.summary()
        meta['thermal_samples'] = thermal.samples
    (out / 'record.json').write_text(json.dumps({**meta, 'steps': record.steps}, indent=2) + '\n', encoding='utf-8')
    summary = summarize(meta, record.steps)
    (out / 'summary.md').write_text(summary, encoding='utf-8')
    archive = out.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(out.rglob('*')):
            zf.write(path, path.relative_to(out.parent))
    print('\n' + summary)
    print(f'Upload this file to the GitHub issue named in docs/INSTALL.md:\n  {archive}')
    return 0 if all(s['status'] != 'failed' for s in record.steps) else 1


if __name__ == '__main__':
    raise SystemExit(main())
