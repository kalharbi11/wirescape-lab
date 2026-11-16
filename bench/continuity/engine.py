# SPDX-License-Identifier: GPL-3.0-only
"""Drive one sidecar run on the null sink with --capture-null-sink (devices off).

The engine is started with --null-audio and an isolated --settings file; no --confirm-* flag is
ever passed, so no audio/MIDI device or LAN socket is opened. Pacing uses the engine's own
100 ms status stream; the edit's position comes from the marks file, never from these waits.
"""
from __future__ import annotations

import json
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import capture
import marks as mk


@dataclass
class Step:
    """One script step: a command (`method`, payload) or a pause of `statuses` status messages."""
    method: str | None = None
    payload: dict = field(default_factory=dict)
    statuses: int = 0
    label: str | None = None   # request id to use; defaults to a running counter


@dataclass
class Run:
    replies: dict          # request id -> reply object
    marks: list            # marks.Mark, in file order
    segments: list         # capture.Segment
    stderr: str


class Engine:
    def __init__(self, binary: str, workdir: Path, rate: int = 48000, block: int = 256):
        self.capture_path = workdir / 'capture.f32'
        settings = workdir / 'settings.json'
        self.process = subprocess.Popen(
            [binary, '--null-audio', '--settings', str(settings), '--rate', str(rate), '--block', str(block),
             '--capture-null-sink', str(self.capture_path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.messages: queue.Queue = queue.Queue()
        self.stderr_bytes = bytearray()
        threading.Thread(target=self._read, daemon=True).start()
        self.drain = threading.Thread(target=lambda: [self.stderr_bytes.extend(c) for c in
                                                      iter(lambda: self.process.stderr.read1(4096), b'')],
                                      daemon=True)
        self.drain.start()
        self.pushes: list = []
        hello = self.messages.get(timeout=15)
        if hello.get('type') != 'hello':
            raise RuntimeError(f'expected hello, got {hello}')

    def _read(self):
        for line in self.process.stdout:
            self.messages.put(json.loads(line))

    def send(self, request: str, method: str, payload: dict, timeout: float = 30.0) -> dict:
        self.process.stdin.write(json.dumps(dict(v=0, id=request, type=method, **payload)).encode() + b'\n')
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            message = self.messages.get(timeout=max(0.1, deadline - time.monotonic()))
            if message.get('re') == request:
                return message
            self.pushes.append(message)

    def statuses(self, count: int, timeout: float = 30.0):
        deadline, seen = time.monotonic() + timeout, 0
        while seen < count:
            if time.monotonic() > deadline:
                raise TimeoutError(f'only {seen} of {count} status messages')
            message = self.pushes.pop(0) if self.pushes else self.messages.get(timeout=timeout)
            if message.get('type') == 'status':
                seen += 1

    def close(self) -> str:
        self.process.stdin.close()
        code = self.process.wait(timeout=30)
        self.drain.join(timeout=5)
        stderr = bytes(self.stderr_bytes).decode(errors='replace')
        if code != 0:
            raise RuntimeError(f'engine exited {code}: {stderr[-500:]}')
        return stderr


def run(binary: str, steps: list[Step], rate: int = 48000, block: int = 256, keep: str | None = None) -> Run:
    with tempfile.TemporaryDirectory(prefix='continuity-') as d:
        work = Path(d)
        engine = Engine(binary, work, rate, block)
        replies, serial = {}, 0
        try:
            engine.statuses(3)
            for step in steps:
                if step.method:
                    serial += 1
                    request = step.label or f's{serial}'
                    replies[request] = engine.send(request, step.method, step.payload)
                if step.statuses:
                    engine.statuses(step.statuses)
        finally:
            stderr = engine.close()
        if 'failed=0' not in stderr:
            raise RuntimeError(f'capture reported a failure: {stderr[-300:]}')
        result = Run(replies, mk.read(work / 'capture.f32.marks'), capture.read(engine.capture_path), stderr)
        if keep:  # raw evidence for audit: the capture and its marks, byte for byte
            dest = Path(keep)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(engine.capture_path, dest / 'capture.f32')
            shutil.copyfile(work / 'capture.f32.marks', dest / 'capture.f32.marks')
        return result
