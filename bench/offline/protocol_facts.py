#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""1000 sequential null-audio sidecar requests and live-edit latency."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import queue
import statistics
import subprocess
import tempfile
import threading
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]


def stats(samples):
    values = sorted(samples)
    def p(percent):
        return values[max(0, (len(values) * percent + 99) // 100 - 1)] if values else None
    return {'n': len(values), 'p50_ms': p(50), 'p95_ms': p(95), 'p99_ms': p(99),
            'max_ms': values[-1] if values else None}


class Engine:
    def __init__(self, binary, settings):
        self.proc = subprocess.Popen([str(binary), '--null-audio', '--settings', str(settings)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        self.messages = queue.Queue()
        self.stderr = bytearray()
        self.reader = threading.Thread(target=self._reader, daemon=True)
        self.err_reader = threading.Thread(target=self._stderr, daemon=True)
        self.reader.start(); self.err_reader.start()
        self.count = 0
        self.hello = self.receive(10.0)
        if self.hello.get('type') != 'hello' or self.hello.get('protocol') != 0:
            raise RuntimeError(f'Not a protocol v0 hello: {self.hello}')

    def _reader(self):
        for line in self.proc.stdout:
            try:
                self.messages.put(json.loads(line))
            except (UnicodeError, json.JSONDecodeError) as exc:
                self.messages.put({'_error': repr(exc)})

    def _stderr(self):
        for chunk in iter(lambda: self.proc.stderr.read1(4096), b''):
            self.stderr.extend(chunk)
            del self.stderr[:-8192]

    def receive(self, timeout=12.0):
        try:
            message = self.messages.get(timeout=timeout)
        except queue.Empty as exc:
            raise RuntimeError(f'No sidecar reply; exit={self.proc.poll()}, stderr={self.stderr[-2000:]!r}') from exc
        if '_error' in message:
            raise RuntimeError(str(message))
        return message

    def send(self, kind, **kwargs):
        self.count += 1
        key = f'b{self.count}'
        request = dict(v=0, id=key, type=kind, **kwargs)
        started = time.perf_counter_ns()
        self.proc.stdin.write((json.dumps(request, separators=(',', ':')) + '\n').encode())
        self.proc.stdin.flush()
        while True:
            reply = self.receive()
            if reply.get('re') != key:
                # Status/telemetry/device pushes are asynchronous, never the reply.
                if 're' in reply:
                    raise RuntimeError(f'Unexpected correlation ID: {reply}')
                continue
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            return reply, elapsed_ms

    def command(self, kind, **kwargs):
        reply, latency = self.send(kind, **kwargs)
        if reply.get('ok') is not True:
            raise RuntimeError(f'{kind}: {reply}')
        return latency

    def close(self):
        if self.proc.poll() is None:
            self.proc.stdin.close()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill(); self.proc.wait(timeout=5)
        self.reader.join(timeout=2); self.err_reader.join(timeout=2)


def patch():
    return {'format': 'wirescape.native.patch', 'version': 2,
            'modules': [{'id': 7, 'module': 'essentials.output'},
                        {'id': 9, 'module': 'essentials.vco'}], 'connections': []}


def edge():
    return {'kind': 'signal', 'from': {'module': 9, 'port': 'audio'},
            'to': {'module': 7, 'port': 'audio'}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--binary', type=Path, default=ROOT / 'build/native/wirescape-engine')
    ap.add_argument('--out', type=Path, default=ROOT / 'build_reports/l4/protocol')
    ap.add_argument('--setparam-count', type=int, default=1000)
    ap.add_argument('--edit-count', type=int, default=100)
    args = ap.parse_args()
    if not args.binary.exists():
        ap.error(f'Binary absent: {args.binary}; run python tools/dev.py build --headless --config Release')
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wirescape-l4-') as tmp:
        started = time.perf_counter_ns()
        engine = Engine(args.binary, Path(tmp) / 'settings.json')
        hello_ms = (time.perf_counter_ns() - started) / 1_000_000
        result = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  'date_et': datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
                  'machine': {'os': platform.platform(), 'cpu': platform.processor() or platform.machine(),
                              'architecture': platform.machine(), 'audio_devices': 'not accessed'},
                  'method': 'one in-flight NDJSON command, stdout correlated reply, perf_counter_ns',
                  'audio': '--null-audio', 'hello_ms': hello_ms}
        try:
            engine.command('loadGraph', patch=patch())
            param_ms = [engine.command('setParam', moduleId=9, paramId='frequency',
                                       value=110 + i % 500) for i in range(args.setparam_count)]
            result['setParam'] = stats(param_ms)
            connect_ms, disconnect_ms = [], []
            for _ in range(args.edit_count):
                connect_ms.append(engine.command('connect', connection=edge()))
                disconnect_ms.append(engine.command('disconnect', connection=edge()))
            result['connect'] = stats(connect_ms)
            result['disconnect'] = stats(disconnect_ms)
            load_times = []
            seen = set()
            for base in (ROOT / 'examples', ROOT / 'native/examples'):
                if not base.exists():
                    continue
                for path in sorted(base.rglob('*.json')):
                    if path.resolve() in seen:
                        continue
                    seen.add(path.resolve())
                    try:
                        document = json.loads(path.read_text(encoding='utf-8'))
                    except (OSError, ValueError):
                        continue
                    if document.get('format') != 'wirescape.native.patch':
                        continue
                    reply, elapsed = engine.send('loadGraph', patch=document)
                    load_times.append({'path': path.relative_to(ROOT).as_posix(),
                                       'ms': elapsed, 'ok': reply.get('ok'),
                                       'code': reply.get('code') if not reply.get('ok') else None})
            result['loadGraph'] = load_times
        finally:
            engine.close()
        (args.out / 'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(args.out / 'summary.json')


if __name__ == '__main__':
    main()
