# SPDX-License-Identifier: GPL-3.0-only
"""A93 OB-h3: device-free patch-switch witness, 200 (or 1000) switches.

Run with the local wirescape-engine executable. Draft-ahead: no product
change, no physical audio/MIDI, no LAN. Linux-only CTest registration.
The 50 ms ingress-to-echo deadline is a contract gate, never retried.
"""
import argparse
from collections import deque
import json
import math
from pathlib import Path
import queue
import socket
import statistics
import struct
import subprocess
import sys
import tempfile
import threading
import time

# Reuse the bounded, correlated, session/generation-checking soak client.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from sidecar_edit_soak import Sidecar, SoakFailure  # noqa: E402

RATE = 48000
BLOCK = 256
CHANNELS = 16
PORT_IN = 9000
PORT_OUT = 9001
HEADER = struct.Struct('<8sIIIIIIQ')


def require(condition, message):
    if not condition:
        raise SoakFailure(message)


class CaptureSidecar(Sidecar):
    def __init__(self, binary, settings, capture):
        self.process = subprocess.Popen(
            [str(binary), '--null-audio', '--settings', str(settings),
             '--rate', str(RATE), '--block', str(BLOCK), '--capture-null-sink', str(capture)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.timeout = 5.0
        self.inbox = queue.Queue(maxsize=128)
        self.errors = deque(maxlen=2)
        self.tail = bytearray()
        self.bench_lines = []
        self.step = 0
        self.gen = 0
        self.session = None
        self.counts = {}
        self.threads = [threading.Thread(target=self._stdout, daemon=True),
                        threading.Thread(target=self._stderr, daemon=True)]
        for thread in self.threads:
            thread.start()

    def route(self, node, out_node):
        deadline = time.monotonic() + self.timeout
        status_seen = notes_seen = False
        while not (status_seen and notes_seen):
            msg = self._next(deadline)
            require(msg.get('session') == self.session and msg.get('v') == 0,
                    'status session/version mismatch')
            if msg.get('gen') != str(self.gen):
                continue
            if msg.get('type') == 'telemetry':
                require(msg['telemetry']['heldNotes'] == [],
                        f'new generation has held MIDI notes: {msg["telemetry"]["heldNotes"]}')
                notes_seen = True
                continue
            if msg.get('type') != 'status':
                continue
            osc = msg['status']['osc']
            routes = osc['routes']
            require(len(routes) == 1, f'wrong ingress route count: {routes}')
            route = routes[0]
            require(osc['enabled'] and not osc['lan'] and route['bind'] == '127.0.0.1' and
                    route['module'] == str(node) and route['port'] == PORT_IN and
                    route['state'] == 'listening' and osc.get('last_error') != 'port-busy',
                    f'new generation ingress not listening: {osc}')
            out = osc['out']
            require(len(out) == 1 and out[0]['module'] == str(out_node) and
                    out[0]['port'] == PORT_OUT and out[0]['state'] == 'sending',
                    f'new generation egress not sending: {out}')
            status_seen = True

    def held(self, key):
        deadline = time.monotonic() + self.timeout
        while True:
            msg = self._next(deadline)
            require(msg.get('session') == self.session and msg.get('v') == 0,
                    'held-note session/version mismatch')
            if msg.get('gen') == str(self.gen) and msg.get('type') == 'telemetry':
                if key in msg['telemetry']['heldNotes']:
                    return


def pad(value):
    raw = value.encode('ascii') + b'\0'
    return raw + b'\0' * (-len(raw) % 4)


def packet(address, value):
    return pad(address) + pad(',f') + struct.pack('>f', value)


def decode(payload):
    def field(offset):
        end = payload.index(b'\0', offset)
        return payload[offset:end].decode('ascii'), (end + 4) & ~3
    address, at = field(0)
    tags, at = field(at)
    if tags == ',f' and len(payload) == at + 4:
        return address, struct.unpack_from('>f', payload, at)
    if tags == ',ifi' and len(payload) == at + 12:
        return address, struct.unpack_from('>ifi', payload, at)
    raise SoakFailure(f'unexpected OSC packet: {address} {tags}')


def receive_until(receiver, deadline, expected):
    """Actual UDP receipt, never a sent counter; ignore other load datagrams."""
    pending = set(expected)
    while pending:
        remaining = deadline - time.monotonic()
        require(remaining > 0, f'OSC receive deadline: {pending}')
        receiver.settimeout(remaining)
        try:
            payload, source = receiver.recvfrom(1500)
        except socket.timeout as error:
            raise SoakFailure(f'OSC receive deadline: {pending}') from error
        require(source[0] == '127.0.0.1', 'non-loopback packet')
        pending.discard(decode(payload))
    require(time.monotonic() <= deadline, 'OSC deadline exceeded')


def row(address):
    return dict(pattern=address, argument=0, kind='cv', input_min=0, input_max=1,
                output_min=0, output_max=1, smoothing_ms=0, timeout_ms=0, stale='hold')


def patch(index):
    # Distinct instance ids and addresses expose an accidentally retained route.
    prefix, base = ('a', 10) if index == 0 else ('b', 20)
    address = '/ob-h3/' + prefix
    source, destination, keyboard, cv, dc, audio, gate = range(base, base + 7)

    def edge(kind, a, port, b, dest):
        return dict(kind=kind, **{'from': dict(module=a, port=port), 'to': dict(module=b, port=dest)})

    doc = dict(format='wirescape.native.patch', version=2,
               modules=[
                   dict(id=source, module='osc.in', config=dict(port=PORT_IN, lan=False,
                        rows=[row(address + '/in'), row('/ob-h3/load')] +
                             [dict(enabled=False) for _ in range(6)])),
                   dict(id=destination, module='osc.out', config=dict(port=PORT_OUT, rate_hz=100,
                        rows=[dict(address=address + '/echo', kind='cv', deadband=0),
                              dict(address=address + '/load', kind='cv', deadband=0),
                              dict(address=address + '/gate', kind='gate')] +
                             [dict(enabled=False) for _ in range(5)],
                        notes=dict(address=address + '/note', enabled=True))),
                   dict(id=keyboard, module='host.keyboard'),
                   dict(id=cv, module='essentials.notes_to_cv'),
                   dict(id=dc, module='essentials.scale_offset',
                        parameters=dict(scale=0, offset=.25 if index == 0 else .5)),
                   dict(id=audio, module='essentials.output'),
                   dict(id=gate, module='essentials.output')],
               connections=[
                   edge('signal', source, 'row1', destination, 'row1'),
                   edge('signal', source, 'row2', destination, 'row2'),
                   edge('event', keyboard, 'notes', cv, 'notes'),
                   edge('event', keyboard, 'notes', destination, 'notes'),
                   edge('signal', cv, 'gate', destination, 'row3'),
                   edge('signal', cv, 'gate', gate, 'audio'),
                   edge('signal', dc, 'control', audio, 'audio')],
               outputs=[dict(module=audio, port='audio', bus_channel=0),
                        dict(module=gate, port='audio', bus_channel=1)])
    return doc, address, source, destination


def rss_kib(pid):
    for line in Path(f'/proc/{pid}/status').read_text().splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1])
    raise SoakFailure('VmRSS missing')


def capture_index(stream):
    segments, blocks = [], 0
    length = stream.seek(0, 2)
    stream.seek(0)
    while stream.tell() < length:
        raw = stream.read(HEADER.size)
        require(len(raw) == HEADER.size, 'truncated capture header')
        magic, version, size, rate, channels, block, index, count = HEADER.unpack(raw)
        require((magic, version, size, rate, channels, block, index) ==
                (b'WSNSCAP1', 1, HEADER.size, RATE, CHANNELS, BLOCK, len(segments)),
                'invalid capture header')
        require(count != 2**64 - 1, 'unclosed capture segment')
        offset = stream.tell()
        end = offset + count * BLOCK * CHANNELS * 4
        require(end <= length, 'truncated capture segment')
        segments.append((blocks, blocks + count, offset))
        blocks += count
        stream.seek(end)
    require(stream.tell() == length and blocks > 0, 'empty/incomplete capture')
    return segments, blocks


def samples(stream, segments, first, end):
    """Read only the bracket, across any sink restart, not the entire long capture."""
    audio, gate = [], []
    for begin, stop, offset in segments:
        lo, hi = max(begin, first), min(stop, end)
        if lo >= hi:
            continue
        stream.seek(offset + (lo - begin) * BLOCK * CHANNELS * 4)
        size = (hi - lo) * BLOCK * CHANNELS
        raw = stream.read(size * 4)
        require(len(raw) == size * 4, 'short capture bracket')
        interleaved = struct.unpack(f'<{size}f', raw)
        audio.extend(interleaved[0::CHANNELS])
        gate.extend(interleaved[1::CHANNELS])
    require(len(audio) == (end - first) * BLOCK, 'missing capture blocks')
    return audio, gate


def fade_gap(audio):
    """DC witness: exact zero between nonzero plateaus, with samples on both ramps."""
    require(all(math.isfinite(x) and x >= 0 for x in audio), 'invalid DC capture')
    require(audio[0] > 0 and audio[-1] > 0, 'no nonzero before/after witness')
    try:
        lo = audio.index(0.0)
    except ValueError as error:
        raise SoakFailure('no exact master-fade zero') from error
    hi = lo
    while hi < len(audio) and audio[hi] == 0.0:
        hi += 1
    require(any(0 < x < audio[0] for x in audio[:lo]), 'no fade-out ramp to zero')
    require(any(0 < x < audio[-1] for x in audio[hi:]), 'no fade-in ramp from zero')
    require(all(x > 0 for x in audio[hi:]), 'second unexpected silent interval')
    require(all(a >= b for a, b in zip(audio[:lo], audio[1:lo])), 'fade-out not monotonic')
    require(all(a <= b for a, b in zip(audio[hi:], audio[hi + 1:])), 'fade-in not monotonic')
    return (hi - lo) * 1000 / RATE


def analyze(capture, switches, mark_ids):
    marks_path = Path(str(capture) + '.marks')
    marks = [json.loads(line) for line in marks_path.read_text().splitlines()]
    by_id = {m['re']: m for m in marks}
    require(len(by_id) == len(marks), 'duplicate capture mark')
    gaps = []
    with capture.open('rb') as stream:
        segments, total = capture_index(stream)
        require(len(mark_ids) == switches, 'missing switch marks')
        for number, (hold_id, swap_id) in enumerate(mark_ids, 1):
            hold, swap = by_id[hold_id], by_id[swap_id]
            require(hold['type'] == 'noteOn' and swap['type'] == 'loadGraph' and
                    hold['ok'] and swap['ok'] and int(swap['gen']) == int(hold['gen']) + 1,
                    f'switch {number}: wrong mark correlation')
            require(0 <= hold['b0'] <= hold['b1'] <= swap['b0'] <= swap['b1'] < total,
                    f'switch {number}: invalid mark bracket')
            # M0 capture marks bracket a command through b1+1. Include one
            # preceding block and one complete following block for plateaus.
            first = max(0, swap['b0'] - 1)
            end = min(total, swap['b1'] + 2)
            audio, gate = samples(stream, segments, first, end)
            _, held = samples(stream, segments, hold['b0'], swap['b0'])
            require(any(x > 0 for x in held) and gate[0] > 0,
                    f'switch {number}: no held note immediately before swap')
            if any(gate[-BLOCK:]):
                # Do not change the oracle, bracket, offered load or deadline.
                # A later intentional noteOn may overlap the R7 bracket: report
                # its marks and the offending sample positions to distinguish
                # that hypothesis from a genuinely retained gate.
                next_hold = (by_id[mark_ids[number][0]]
                             if number < len(mark_ids) else None)
                final = gate[-BLOCK:]
                nonzero = [i for i, value in enumerate(final) if value != 0.0]
                block_summary = [
                    dict(block=first + offset // BLOCK,
                         nonzero=sum(value != 0.0 for value in gate[offset:offset + BLOCK]),
                         minimum=min(gate[offset:offset + BLOCK]),
                         maximum=max(gate[offset:offset + BLOCK]))
                    for offset in range(0, len(gate), BLOCK)
                ]
                detail = dict(switch=number, hold=hold, swap=swap,
                              next_hold=next_hold, first_block=first, end_block=end,
                              last_block=end - 1, first_nonzero=nonzero[0],
                              last_nonzero=nonzero[-1], blocks=block_summary)
                raise SoakFailure(
                    f'switch {number}: gate/note retained after swap; '
                    + json.dumps(detail, separators=(',', ':')))
            try:
                gaps.append(fade_gap(audio))
            except SoakFailure as error:
                raise SoakFailure(f'switch {number}: {error}') from error
    return gaps


def run(binary, switches):
    rss, marks, ack_ms = {}, [], []
    with tempfile.TemporaryDirectory(prefix='ob-h3-') as directory, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        root = Path(directory)
        capture = root / 'switches.f32'
        receiver.bind(('127.0.0.1', PORT_OUT))  # exact A93 ports, no fallback
        engine = CaptureSidecar(binary, root / 'settings.json', capture)
        stop, load_error = threading.Event(), []

        def traffic():
            value = 0.0
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as load:
                    while not stop.is_set():
                        load.sendto(packet('/ob-h3/load', value), ('127.0.0.1', PORT_IN))
                        value = 1.0 - value
                        stop.wait(.005)
            except OSError as error:
                load_error.append(str(error))

        worker = threading.Thread(target=traffic, daemon=True)
        try:
            engine.hello()
            old, address, source, out = patch(0)
            engine.request('loadGraph', swap=True, patch=old)
            engine.route(source, out)
            worker.start()
            for number in range(1, switches + 1):
                require(not load_error, f'OSC load failed: {load_error}')
                # Hold the note across the switch, without sending noteOff/panic.
                engine.request('noteOn', note=60, velocity=.5)
                hold_id = f'soak-{engine.step}'
                receive_until(receiver, time.monotonic() + 2, {
                    (address + '/gate', (1.0,)), (address + '/note', (60, .5, 0))})
                engine.held(60)
                # Allow the real held block to be captured before the command;
                # the offline witness still requires a high pre-swap sample.
                time.sleep(2 * BLOCK / RATE)
                new, address, source, out = patch(number % 2)
                started = time.monotonic()
                engine.request('loadGraph', swap=True, patch=new)
                acknowledged = time.monotonic()
                ack_ms.append((acknowledged - started) * 1000)
                swap_id = f'soak-{engine.step}'
                deadline = acknowledged + .050
                value = number / 2048  # unique exactly representable sentinel
                sender.sendto(packet(address + '/in', value), ('127.0.0.1', PORT_IN))
                receive_until(receiver, deadline, {(address + '/echo', (value,))})
                # Observe the newly committed route only after the timed echo.
                engine.route(source, out)
                marks.append((hold_id, swap_id))
                if number in (100, 1000):
                    rss[str(number)] = rss_kib(engine.process.pid)
            # Pacing on a fresh status gives the final fade/capture time to publish.
            engine.route(source, out)
        finally:
            stop.set()
            if worker.ident is not None:
                worker.join(timeout=2)
            failure = engine.close()
            require(not failure, f'sidecar shutdown: {failure}; {engine.tail[-1000:]!r}')
        require(not load_error, f'OSC load failed: {load_error}')
        gaps = analyze(capture, switches, marks)
    return dict(status='passed', switches=switches, gap_ms_p50=statistics.median(gaps),
                gap_ms_max=max(gaps), rss_kib=rss,
                load_ack_ms_p50=statistics.median(ack_ms), load_ack_ms_max=max(ack_ms),
                gap_definition='exact-zero captured samples; excludes stopped wall-clock time')


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('engine', type=Path)
    parser.add_argument('--switches', type=int, choices=(200, 1000), default=200)
    args = parser.parse_args()
    try:
        require(args.engine.is_file(), 'engine executable missing')
        print(json.dumps(run(args.engine.resolve(), args.switches), sort_keys=True, allow_nan=False))
    except (SoakFailure, OSError, ValueError, KeyError) as error:
        print(f'OB-h3 failure: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
