# SPDX-License-Identifier: GPL-3.0-only
"""--capture-null-sink (T0.13a): refusal outside the null sink, file format and contents.

Device-off: every engine runs with --null-audio (or is refused before startup) and an
isolated --settings file. No audio/MIDI device or LAN socket is opened.
"""
import json
import math
import queue
import struct
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

BINARY = sys.argv[1]
HEADER = struct.Struct('<8sIIIIIIQ')  # magic, version, header_bytes, rate, channels, block, segment, blocks
OPEN_SEGMENT = 2**64 - 1


def refused(*args, settings):
    """Startup must exit nonzero with a diagnostic and never emit hello."""
    result = subprocess.run([BINARY, '--settings', str(settings), *args], stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=20)
    assert result.returncode != 0, (args, result)
    assert b'"hello"' not in result.stdout, (args, result.stdout[:200])
    return result.stderr.decode(errors='replace')


class Engine:
    def __init__(self, *args):
        self.process = subprocess.Popen([BINARY, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.messages = queue.Queue()
        self.stderr_bytes = bytearray()
        threading.Thread(target=lambda: [self.messages.put(json.loads(line)) for line in self.process.stdout],
                         daemon=True).start()
        self.drain = threading.Thread(target=lambda: [self.stderr_bytes.extend(chunk) for chunk in
                                                      iter(lambda: self.process.stderr.read1(4096), b'')],
                                      daemon=True)
        self.drain.start()
        self.hello = self.messages.get(timeout=10)
        assert self.hello['type'] == 'hello', self.hello
        self.serial = 0
        self.pushes = []

    def call(self, method, **payload):
        self.serial += 1
        request = f'c{self.serial}'
        self.process.stdin.write(json.dumps(dict(v=0, id=request, type=method, **payload)).encode() + b'\n')
        self.process.stdin.flush()
        while True:
            message = self.messages.get(timeout=10)
            if message.get('re') == request:
                assert message['ok'], message
                return message
            self.pushes.append(message)

    def statuses(self, count, timeout=20.0):
        """Pace on the engine's own 100 ms status stream; returns the last status seen."""
        deadline, seen, last = time.monotonic() + timeout, 0, None
        while seen < count:
            assert time.monotonic() < deadline, f'only {seen} of {count} status messages'
            message = self.pushes.pop(0) if self.pushes else self.messages.get(timeout=timeout)
            if message.get('type') == 'status':
                seen, last = seen + 1, message['status']
        return last

    def close(self):
        self.process.stdin.close()
        assert self.process.wait(timeout=20) == 0
        self.drain.join(timeout=5)
        return bytes(self.stderr_bytes).decode(errors='replace')


def segments(data):
    """Parse the capture file strictly: every byte belongs to a header or a complete block."""
    result, offset = [], 0
    while offset < len(data):
        assert len(data) - offset >= HEADER.size, 'truncated segment header'
        magic, version, header_bytes, rate, channels, block, index, blocks = HEADER.unpack_from(data, offset)
        assert (magic, version, header_bytes) == (b'WSNSCAP1', 1, HEADER.size)
        assert index == len(result), 'segments are numbered in file order'
        assert blocks != OPEN_SEGMENT, 'a cleanly stopped engine closes every segment'
        offset += HEADER.size
        size = blocks * block * channels * 4
        assert len(data) - offset >= size, 'segment shorter than its recorded block count'
        samples = struct.unpack_from(f'<{blocks * block * channels}f', data, offset)
        offset += size
        rows = [samples[c::channels] for c in range(channels)]
        result.append(dict(rate=rate, channels=channels, block=block, blocks=blocks, rows=rows))
    assert offset == len(data)
    return result


def rising_crossings(row):
    return sum(1 for a, b in zip(row, row[1:]) if a < 0 <= b)


def edge(source, dest):
    return {'kind': 'signal', 'from': dict(module=source, port='audio'), 'to': dict(module=dest, port='audio')}


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    settings = root / 'settings.json'

    # 1. Refusal: the flag needs the null sink and is checked while parsing flags, before any
    #    device is considered. No --confirm-* flag is ever passed here (devices off).
    target = root / 'refused.f32'
    for args in (['--capture-null-sink', str(target)],
                 ['--device', 'any', '--capture-null-sink', str(target)]):
        assert '--capture-null-sink requires --null-audio' in refused(*args, settings=settings), args
        assert not target.exists(), 'a refused startup creates no capture file'
    refused('--null-audio', '--capture-null-sink', settings=settings)        # missing value
    refused('--null-audio', '--capture-null-sink', '', settings=settings)    # empty value
    stderr = refused('--null-audio', '--capture-null-sink', str(root / 'missing' / 'x.f32'), settings=settings)
    assert 'Cannot open --capture-null-sink file' in stderr, stderr

    # 2. Absent flag: no capture diagnostics and no file side effects (protocol and golden
    #    behaviour without the flag are covered by the existing protocol and golden tests).
    engine = Engine('--null-audio', '--settings', str(settings), '--rate', '48000', '--block', '256')
    engine.statuses(3)
    assert 'capture' not in engine.close()

    # 3. Capture: real rendered blocks, every bus channel, one segment per sink start.
    capture = root / 'capture.f32'
    engine = Engine('--null-audio', '--settings', str(settings), '--rate', '48000', '--block', '256',
                    '--capture-null-sink', str(capture))
    engine.statuses(3)
    # The default startup graph is one Output fed by nothing; keep a mono-to-stereo witness too.
    patch = dict(format='wirescape.native.patch', version=2,
                 modules=[dict(id=1, module='essentials.vco', parameters=dict(frequency=220)),
                          dict(id=2, module='essentials.vco', parameters=dict(frequency=330)),
                          dict(id=8, module='essentials.output'), dict(id=9, module='essentials.output')],
                 connections=[edge(1, 8), edge(2, 9)],
                 outputs=[dict(module=8, port='audio', bus_channel=0), dict(module=8, port='audio', bus_channel=1),
                          dict(module=9, port='audio', bus_channel=5)])
    engine.call('loadGraph', patch=patch)
    engine.statuses(6)
    engine.call('setBufferFrames', frames=128)  # restarts the sink: a new segment, new block size
    assert engine.statuses(6)['audio']['bufferFrames'] == 128
    stderr = engine.close()

    found = segments(capture.read_bytes())
    assert len(found) >= 2, [(s['block'], s['blocks']) for s in found]
    assert all(s['rate'] == 48000 and s['channels'] == 16 for s in found)
    assert found[0]['block'] == 256 and found[-1]['block'] == 128
    total = sum(s['blocks'] for s in found)
    summary = f'capture segments={len(found)} blocks={total} failed=0'
    assert summary in stderr, (summary, stderr)

    last = found[-1]
    assert last['blocks'] >= 60, last['blocks']
    rows = last['rows']
    tail = 48000 // 4  # the last quarter second of the final segment, well after the restart fade
    assert len(rows[0]) >= tail
    left, right, other = rows[0][-tail:], rows[1][-tail:], rows[5][-tail:]
    assert left == right, 'one route to both stereo rows renders identical samples'
    assert max(map(abs, left)) > 0.01 and max(map(abs, other)) > 0.01
    for row, hz in ((left, 220), (other, 330)):
        measured = rising_crossings(row) * 48000 / len(row)
        assert abs(measured - hz) <= 8, (hz, measured)
    silent = [c for c in range(16) if c not in (0, 1, 5)]
    assert all(not any(rows[c]) for c in silent), 'unrouted bus channels are exactly zero'
    assert all(math.isfinite(x) for x in left + other)

print('capture tests passed')
