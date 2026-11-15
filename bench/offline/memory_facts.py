#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Device-free null-audio sidecar RSS using /proc on Linux or psutil on Windows."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import time
from zoneinfo import ZoneInfo

from protocol_facts import Engine, ROOT


def rss_kib(pid):
    if platform.system() == 'Windows':
        import psutil
        return psutil.Process(pid).memory_info().rss // 1024
    status = Path('/proc') / str(pid) / 'status'
    for line in status.read_text().splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1])
    raise ValueError(f'VmRSS not exposed by {status}')


def main():
    ap = argparse.ArgumentParser()
    binary = (ROOT / 'build/native/Release/wirescape-engine.exe'
              if platform.system() == 'Windows'
              else ROOT / 'build/native/wirescape-engine')
    ap.add_argument('--binary', type=Path, default=binary)
    ap.add_argument('--out', type=Path, default=ROOT / 'build_reports/l4/memory')
    args = ap.parse_args()
    if not args.binary.is_file():
        ap.error(f'Missing binary: {args.binary}')
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wirescape-l4-') as tmp:
        engine = Engine(args.binary, Path(tmp) / 'settings.json')
        try:
            time.sleep(0.5)
            idle = rss_kib(engine.proc.pid)
            files = []
            for f in sorted((ROOT / 'native/examples').glob('*.json')):
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                except ValueError:
                    continue
                if data.get('format') == 'wirescape.native.patch':
                    files.append((f.stat().st_size, f, data))
            loaded = None
            if files:
                size, file, patch = sorted(files, reverse=True, key=lambda item:item[0])[0]
                reply, ms = engine.send('loadGraph', patch=patch)
                time.sleep(0.5)
                loaded = {'patch': file.relative_to(ROOT).as_posix(), 'patch_bytes': size,
                          'accepted': reply.get('ok') is True,
                          'error_code': reply.get('code') if not reply.get('ok') else None,
                          'rss_kib': rss_kib(engine.proc.pid), 'loadGraph_ms': ms}
            result = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      'date_et':datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
                      'machine': {'os':platform.platform(), 'cpu':platform.processor() or platform.machine(),
                                  'architecture':platform.machine(), 'audio_devices':'not accessed'},
                      'method':('psutil.Process.memory_info().rss (Windows)'
                                if platform.system() == 'Windows'
                                else 'Linux /proc/<pid>/status VmRSS') +
                               ', 500 ms after null-audio startup/load',
                      'engine_idle_rss_kib':idle,'largest_bundled_patch':loaded,
                      'electron_process_rss_kib':None,
                      'electron_note':'Electron process RSS measured separately in startup.json'}
            (args.out/'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
            print(args.out/'summary.json')
        finally:
            engine.close()


if __name__ == '__main__':
    main()
