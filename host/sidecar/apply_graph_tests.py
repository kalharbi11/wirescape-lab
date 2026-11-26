# SPDX-License-Identifier: GPL-3.0-only
"""applyGraph on the null sink (M2 E1a, proposals/0005 section 3, invariants J1-J5).

Each semantic is shown with a render-backed observable that a restart would reset:
a running Groove's play state and loop count, and a VCO's nominal pitch telemetry.
Devices off: --null-audio, temporary settings, no confirmation flags.
"""
import copy
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

BINARY = sys.argv[1]


class Engine:
    def __init__(self, settings):
        self.process = subprocess.Popen([BINARY, '--null-audio', '--settings', str(settings)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.messages = queue.Queue()
        self.pushes = []
        self.serial = 0
        self.stderr_tail = bytearray()

        def read():
            for line in self.process.stdout:
                self.messages.put(json.loads(line))

        def drain():
            for chunk in iter(lambda: self.process.stderr.read1(4096), b''):
                self.stderr_tail.extend(chunk)
                del self.stderr_tail[:-16384]
        threading.Thread(target=read, daemon=True).start()
        self.drainer = threading.Thread(target=drain, daemon=True)
        self.drainer.start()
        self.hello = self.messages.get(timeout=10)
        assert self.hello['type'] == 'hello', self.hello

    def stderr(self):
        return bytes(self.stderr_tail).decode(errors='replace')

    def receive(self):
        try:
            return self.messages.get(timeout=10)
        except queue.Empty as error:
            raise AssertionError(f'no message within 10s; stderr: {self.stderr()[-2000:]}') from error

    def call(self, method, expected=True, **payload):
        self.serial += 1
        request_id = f'a{self.serial}'
        line = json.dumps(dict(v=0, id=request_id, type=method, **payload)).encode() + b'\n'
        self.process.stdin.write(line)
        self.process.stdin.flush()
        while True:
            message = self.receive()
            if message.get('re') == request_id:
                assert message['ok'] == expected, message
                return message
            self.pushes.append(message)

    def telemetry_when(self, gen, predicate, timeout=8.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = self.pushes.pop(0) if self.pushes else self.receive()
            if message.get('type') == 'telemetry' and message['gen'] == gen and predicate(message['telemetry']):
                return message['telemetry']
        raise AssertionError(f'no matching telemetry at gen {gen}; stderr: {self.stderr()[-2000:]}')

    def close(self):
        self.process.stdin.close()
        assert self.process.wait(timeout=10) == 0, self.stderr()[-2000:]
        self.drainer.join(timeout=5)


def groove_patch(bpm=300):
    # Unknown fields at root, module and connection level ride along (J5).
    return dict(format='wirescape.native.patch', version=2,
                modules=[dict(id=7, module='essentials.output', extra={'kept': 1}),
                         dict(id=1, module='sequencing.groove',
                              config=dict(version=1, bpm=bpm,
                                          tracks=[dict(steps=[dict(kind='note', key=60, velocity=1)])])),
                         dict(id=9, module='essentials.vco', parameters=dict(frequency=440))],
                connections=[dict(kind='signal', **{'from': dict(module=9, port='audio'),
                                                     'to': dict(module=7, port='audio')}, note='kept')],
                ui=dict(opaque={'unchanged': True}))


def playing(t):
    tracks = t.get('groove', {}).get('1')
    return bool(tracks) and tracks[0].get('playing') is True


def loops(t):
    return t['groove']['1'][0]['loop']


def pitch(t, module='9'):
    return t.get('effective_pitch', {}).get(module)


with tempfile.TemporaryDirectory() as directory:
    engine = Engine(Path(directory) / 'settings.json')
    # J2: advertised; additive to v0.
    assert 'applyGraph' in engine.hello['capabilities'], engine.hello['capabilities']
    base = groove_patch()
    gen = engine.call('loadGraph', patch=base)['gen']
    engine.call('setParam', moduleId=1, paramId='run', value=1)
    before = engine.telemetry_when(gen, lambda t: playing(t) and loops(t) >= 2)
    assert abs(pitch(before) - 69) < 0.02, before.get('effective_pitch')

    # Rules 1, 2 and 4: same namespace, gen advances, unchanged modules keep their instances;
    # an added module is created. The Groove keeps playing and its loop count keeps rising.
    added = copy.deepcopy(base)
    added['modules'].append(dict(id=12, module='essentials.lfo'))
    added['modules'][1]['parameters'] = dict(run=1)  # equal to the committed value: no event
    reply = engine.call('applyGraph', patch=added)
    assert int(reply['gen']) == int(gen) + 1, reply
    assert reply['result'] == dict(path='live', replaced=[], unapplied=[]), reply
    kept = engine.telemetry_when(reply['gen'], lambda t: playing(t))
    assert loops(kept) >= loops(before), (loops(kept), loops(before))
    gen = reply['gen']

    # Rule 5: a changed parameter of a kept instance arrives as a live event.
    retuned = copy.deepcopy(added)
    retuned['modules'][2]['parameters'] = dict(frequency=880)
    reply = engine.call('applyGraph', patch=retuned)
    assert reply['result'] == dict(path='live', replaced=[], unapplied=[]), reply
    after = engine.telemetry_when(reply['gen'], lambda t: pitch(t) is not None and abs(pitch(t) - 81) < 0.02)
    assert playing(after), 'the Groove was not touched by a VCO parameter change'
    # ...and a parameter removed from the document returns to the module's initial value.
    reply = engine.call('applyGraph', patch=added)
    engine.telemetry_when(reply['gen'], lambda t: pitch(t) is not None and abs(pitch(t) - 69) < 0.02)
    gen = reply['gen']

    # Rule 3: a changed config replaces that instance only, and it is listed in `replaced`.
    faster = copy.deepcopy(added)
    faster['modules'][1]['config']['bpm'] = 240
    running = engine.telemetry_when(gen, lambda t: playing(t) and loops(t) >= 2)
    reply = engine.call('applyGraph', patch=faster)
    assert reply['result'] == dict(path='live', replaced=[1], unapplied=[]), reply
    fresh = engine.telemetry_when(reply['gen'], lambda t: '1' in t.get('groove', {}))
    assert not playing(fresh) or loops(fresh) < loops(running), (fresh['groove'], running['groove'])
    gen = reply['gen']

    # Rule 4 and D3: a removed ID may return through applyGraph (addModule still refuses it).
    removed = copy.deepcopy(faster)
    removed['modules'] = [m for m in removed['modules'] if m['id'] != 12]
    gen = engine.call('applyGraph', patch=removed)['gen']
    assert engine.call('addModule', False, moduleId=12, moduleType='essentials.lfo')['code'] == 'duplicate'
    reply = engine.call('applyGraph', patch=faster)
    assert int(reply['gen']) == int(gen) + 1 and reply['result']['replaced'] == [], reply
    gen = reply['gen']

    # J3: a refused applyGraph leaves graph, document and gen untouched.
    bad = copy.deepcopy(faster)
    bad['modules'].append(dict(id=30, module='no.such.module'))
    refused = engine.call('applyGraph', False, patch=bad)
    assert refused['code'] == 'unknown-module' and refused['gen'] == gen, refused
    engine.telemetry_when(gen, lambda t: '1' in t.get('groove', {}) and pitch(t) is not None)
    # E3a-2: invalid live data is a field-named refusal, not a graph edit.
    malformed = copy.deepcopy(faster)
    malformed['modules'][2]['data'] = []
    refused = engine.call('applyGraph', False, patch=malformed)
    assert refused['gen'] == gen and 'data' in refused['message'], refused
    refused = engine.call('setData', False, moduleId=9, slot='missing', value={})
    assert refused['code'] == 'invalid' and 'missing' in refused['message'] and refused['gen'] == gen, refused
    refused = engine.call('setData', False, moduleId=999, slot='missing', value={})
    assert refused['code'] == 'not-found' and refused['gen'] == gen, refused
    # J5: the committed document (unknown fields included) is the base of the next edit.
    reply = engine.call('addModule', moduleId=40, moduleType='essentials.vco')
    assert int(reply['gen']) == int(gen) + 1
    engine.telemetry_when(reply['gen'], lambda t: '40' in t.get('effective_pitch', {}))

    # loadGraph is unchanged: a new namespace and a restart of every instance.
    reply = engine.call('loadGraph', patch=base)
    assert 'result' not in reply, reply
    engine.telemetry_when(reply['gen'], lambda t: t.get('playhead', {}).get('1') == [-1, -1])
    engine.close()
    # Exactly one commit line per accepted graph change: loadGraph (d5), six applyGraph and one
    # addModule (all live), then loadGraph (d5). Refusals log nothing.
    commits = [line.split(' gen=')[0] for line in engine.stderr().splitlines() if line.startswith('commit path=')]
    assert commits == ['commit path=d5'] + ['commit path=live'] * 7 + ['commit path=d5'], commits
print('applyGraph tests passed')
