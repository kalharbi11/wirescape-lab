# SPDX-License-Identifier: GPL-3.0-only
"""A51: live applyGraph replaces/removes OSC Out while ASan watches its bus."""
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

def patch(osc=True, changed=False):
    modules = [dict(id=7, module='essentials.output'),
               dict(id=8, module='essentials.lfo')]
    connections = []
    if osc:
        modules.append(dict(id=9, module='osc.out', config=dict(
            port=19001, rate_hz=20 if changed else 10,
            rows=[dict(address='/ws/row/1', kind='cv', deadband=0)] +
                 [dict(enabled=False) for _ in range(7)])))
        connections.append(dict(kind='signal', **{
            'from': dict(module=8, port='control'),
            'to': dict(module=9, port='row1')}))
    return dict(format='wirescape.native.patch', version=2,
                modules=modules, connections=connections)

with tempfile.TemporaryDirectory() as directory:
    settings = Path(directory) / 'settings.json'
    proc = subprocess.Popen([sys.argv[1], '--null-audio', '--settings', str(settings)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1)
    messages = queue.Queue()
    errors = []
    def read():
        for line in proc.stdout:
            messages.put(json.loads(line))
    def drain():
        for line in proc.stderr:
            errors.append(line)
    reader = threading.Thread(target=read, daemon=True)
    drainer = threading.Thread(target=drain, daemon=True)
    reader.start()
    drainer.start()
    try:
        hello = messages.get(timeout=30)
        assert hello['type'] == 'hello' and 'applyGraph' in hello['capabilities'], hello
        def call(method, serial, graph):
            rid = str(serial)
            proc.stdin.write(json.dumps(dict(v=0, id=rid, type=method, patch=graph)) + '\n')
            proc.stdin.flush()
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                msg = messages.get(timeout=max(.01, deadline-time.monotonic()))
                if 're' in msg:
                    assert msg['re'] == rid and msg['ok'], msg
                    return msg
            raise AssertionError('missing reply')
        call('loadGraph', 1, patch())
        time.sleep(.15)
        call('applyGraph', 2, patch(changed=True))
        time.sleep(.15)
        call('applyGraph', 3, patch(osc=False))
        time.sleep(.15)
        proc.stdin.close()
        assert proc.wait(timeout=20) == 0, ''.join(errors)
        reader.join(timeout=5)
        drainer.join(timeout=5)
        stderr = ''.join(errors)
        assert stderr.count('commit path=live gen=') >= 2, stderr
        assert 'AddressSanitizer' not in stderr and 'runtime error:' not in stderr, stderr
        print('PASS A51 live applyGraph OSC Out replacement/removal; no sanitizer reports')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
