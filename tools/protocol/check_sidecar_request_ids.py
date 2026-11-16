# SPDX-License-Identifier: GPL-3.0-only
"""Q8: compare the shared request-ID corpus against the unmodified null-audio sidecar.

Usage: python tools/protocol/check_sidecar_request_ids.py PATH-TO-ENGINE
No MIDI/audio device or LAN flags; no existing test or runtime code is modified.
"""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from validate import read_schema, validate

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tools" / "protocol" / "request_id_cases.json"


def check(binary: str) -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    assert len(cases) >= 10
    schema = read_schema()

    with tempfile.TemporaryDirectory(prefix="wirescape-pv1-q8-") as directory:
        command = [binary, "--null-audio", "--settings", str(Path(directory) / "settings.json")]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, bufsize=0)
        messages = queue.Queue()
        stderr_tail = bytearray()

        def read_stdout():
            try:
                for raw in process.stdout:
                    messages.put(json.loads(raw.decode("utf-8")))
            except Exception as exc:
                messages.put(exc)

        def drain_stderr():
            for chunk in iter(lambda: process.stderr.read(4096), b""):
                stderr_tail.extend(chunk)
                del stderr_tail[:-8192]

        reader = threading.Thread(target=read_stdout, daemon=True)
        errors = threading.Thread(target=drain_stderr, daemon=True)
        reader.start()
        errors.start()
        try:
            hello = messages.get(timeout=10)
            assert isinstance(hello, dict) and hello.get("type") == "hello", hello
            session = hello["session"]
            for item in cases:
                wire = {"v": 0, "id": item["id"], "type": "panic"}
                schema_result = validate(wire, schema)
                assert schema_result is item["valid"], item["name"]
                process.stdin.write(
                    (json.dumps(wire, ensure_ascii=False, separators=(",", ":")) + "\n")
                    .encode("utf-8")
                )
                process.stdin.flush()
                while True:
                    response = messages.get(timeout=10)
                    if isinstance(response, Exception):
                        raise response
                    assert response.get("session") == session, (item["name"], response)
                    if "re" in response:
                        break
                assert response["ok"] is item["valid"], (item["name"], response)
                assert response["re"] == (item["id"] if item["valid"] else None), (
                    item["name"], response,
                )
                if not item["valid"]:
                    assert response.get("code") == "invalid", (item["name"], response)
            process.stdin.close()
            process.wait(timeout=10)
            assert process.returncode == 0, stderr_tail.decode(errors="replace")[-1000:]
            print(f"Q8 real sidecar null-audio request IDs: {len(cases)} / {len(cases)} "
                  "agree with schema (no hardware/LAN)")
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
