# SPDX-License-Identifier: GPL-3.0-only
"""OB-g2: real sidecar, synthetic Host backend; no physical MIDI or audio."""
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

binary = sys.argv[1]


def run():
    with tempfile.TemporaryDirectory() as directory:
        settings = str(Path(directory) / "device-off-settings.json")
        for invalid in ([binary, "--scripted-midi", "--settings", settings],
                        [binary, "--scripted-midi", "--null-audio"]):
            result = subprocess.run(invalid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
            assert result.returncode != 0, "scripted MIDI needs null audio and explicit settings"

        proc = subprocess.Popen(
            [binary, "--null-audio", "--scripted-midi", "--settings", settings],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        messages = queue.Queue()
        errors = []

        def read():
            for line in proc.stdout:
                try:
                    messages.put(json.loads(line))
                except Exception as error:
                    errors.append(str(error))

        def drain():
            while proc.stderr.read(4096):
                pass

        reader = threading.Thread(target=read, daemon=True)
        stderr_reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        stderr_reader.start()
        try:
            hello = messages.get(timeout=10)
            assert hello["type"] == "hello" and hello["protocol"] == 0
            assert hello["midi"]["counters"]["release_panics"] == 0
            names = {d["system_name"] for d in hello["midi"]["devices"]}
            assert "scripted:midi-m8:0" in names, names
            before = hello["midi"]["counters"]["received"]
            deadline = time.monotonic() + 6
            observed = None
            while time.monotonic() < deadline:
                event = messages.get(timeout=max(0.1, deadline - time.monotonic()))
                if event.get("type") != "status":
                    continue
                counters = event["status"]["midi"]["counters"]
                assert {"received", "dropped", "ring_full", "malformed", "send_fail",
                        "release_panics", "ports"} <= set(counters)
                if counters["received"] > before:
                    observed = counters
                    break
            assert observed is not None, "scripted callback never reached the real Host"
            assert observed["release_panics"] == 0
            assert observed["dropped"] == observed["ring_full"] == observed["malformed"] == 0
            assert not errors, errors
        finally:
            proc.stdin.close()
            try:
                code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise
            reader.join(timeout=3)
            stderr_reader.join(timeout=3)
        assert code == 0 and not errors, (code, errors)
        print("PASS OB-g2 real null-audio sidecar --scripted-midi, additive counters, no devices")


if __name__ == "__main__":
    run()
