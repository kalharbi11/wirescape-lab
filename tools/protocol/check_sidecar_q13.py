# SPDX-License-Identifier: GPL-3.0-only
"""Q13: verify actual null-audio sidecar output-bus bounds and merged applyGraph.

No device/MIDI/LAN authorization. At channel 15, graph-level refusal is
reported as observed, not represented as a schema rejection (Fable Q13).
"""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from validate import ROOT, read_schema, validate

CASES = ROOT / "tools" / "protocol" / "bus_channel_cases.json"


def check(binary: str) -> None:
    schema = read_schema()
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    assert len(cases) == 6
    with tempfile.TemporaryDirectory(prefix="wirescape-pv1-q13-") as tmp:
        process = subprocess.Popen(
            [binary, "--null-audio", "--settings", str(Path(tmp) / "settings.json")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        incoming = queue.Queue()
        stderr_tail = bytearray()

        def read():
            try:
                for line in process.stdout:
                    incoming.put(json.loads(line))
            except Exception as exc:
                incoming.put(exc)

        def drain():
            for chunk in iter(lambda: process.stderr.read(4096), b""):
                stderr_tail.extend(chunk)
                del stderr_tail[:-8192]

        reader = threading.Thread(target=read, daemon=True)
        errors = threading.Thread(target=drain, daemon=True)
        reader.start()
        errors.start()

        def message():
            item = incoming.get(timeout=15)
            if isinstance(item, BaseException):
                raise item
            assert isinstance(item, dict), item
            return item

        try:
            hello = message()
            assert hello.get("type") == "hello", hello
            assert validate(hello, schema), "sidecar hello violates PV1 schema"
            assert "applyGraph" in hello.get("capabilities", []), "E1a capability absent"
            session = hello["session"]
            serial = 0

            def request(method, patch):
                nonlocal serial
                serial += 1
                request_id = "q13-" + str(serial)
                command = {"v": 0, "id": request_id, "type": method, "patch": patch}
                shape = validate(command, schema)
                process.stdin.write(
                    (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8"))
                process.stdin.flush()
                while True:
                    reply = message()
                    assert reply.get("session") == session, reply
                    if "re" in reply:
                        assert reply["re"] == request_id, reply
                        assert validate(reply, schema), reply
                        return shape, reply

            base_patch = {
                "format": "wirescape.native.patch", "version": 2,
                "modules": [{"id": 7, "module": "essentials.output"}],
                "connections": [], "future_q3": {"opaque": [1, None, "retained"]},
            }
            for case in cases:
                patch = {**base_patch, "outputs": [
                    {"module": 7, "port": "audio", "bus_channel": case["value"]}]}
                shape, reply = request("loadGraph", patch)
                assert shape is case["valid"], (case["name"], shape)
                if not case["valid"]:
                    assert not reply["ok"], (case["name"], reply)
                elif case["value"] == 0:
                    assert reply["ok"], ("valid channel 0 unexpectedly refused", reply)
                elif case["value"] == 15 and not reply["ok"]:
                    # Q13 expressly permits an unrelated graph-level refusal at 15.
                    print("Q13 channel 15: schema accepted; sidecar graph refused:",
                          reply.get("code"), reply.get("message"))
                else:
                    assert reply["ok"], (case["name"], reply)

            # Independently exercise E1a on a known valid route.
            patch = {**base_patch, "outputs": [
                {"module": 7, "port": "audio", "bus_channel": 0}]}
            valid, load = request("loadGraph", patch)
            assert valid and load["ok"], load
            valid, applied = request("applyGraph", patch)
            assert valid and applied["ok"], applied
            assert int(applied["gen"]) > int(load["gen"]), (load, applied)
            result = applied["result"]
            result_shape = {"$defs": schema["$defs"], "$ref": "#/$defs/applyGraphResult"}
            assert validate(result, result_shape), result
            assert result["path"] in ("live", "restart")
            assert isinstance(result["replaced"], list)
            assert isinstance(result["unapplied"], list)
            process.stdin.close()
            process.wait(timeout=15)
            assert process.returncode == 0, stderr_tail.decode(errors="replace")[-1000:]
            print("Q13 sidecar: 6 bus-channel schema/sidecar boundary cases, "
                  "applyGraph capability, command and reply-result shape verified")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            reader.join(timeout=5)
            errors.join(timeout=5)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    check(sys.argv[1])
