# SPDX-License-Identifier: GPL-3.0-only
"""OB-a3 pin 7: real null-audio NDJSON graph entry points never save v1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading


def snapshot(folder: Path) -> tuple:
    return tuple((p.name, p.read_bytes(), hashlib.sha256(p.read_bytes()).hexdigest(),
                  p.stat().st_mtime_ns) for p in sorted(folder.iterdir()))


def main() -> None:
    engine, old_source, modern_source = map(Path, sys.argv[1:4])
    with tempfile.TemporaryDirectory(prefix="wirescape-ob-a3-sidecar-") as temp:
        root = Path(temp)
        inputs = root / "inputs"
        inputs.mkdir()
        old = inputs / "legacy.json"
        modern = inputs / "modern.json"
        shutil.copy2(old_source, old)
        shutil.copy2(modern_source, modern)
        before = snapshot(inputs)
        v1, v2 = json.loads(old.read_bytes()), json.loads(modern.read_bytes())
        assert v1["version"] == 1 and v2["version"] == 2
        settings = root / "settings.json"
        child = subprocess.Popen(
            [str(engine), "--null-audio", "--settings", str(settings)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=root)
        output = queue.Queue()
        errors = bytearray()

        def read_stdout():
            for line in child.stdout:
                output.put(json.loads(line))

        def read_stderr():
            for line in child.stderr:
                errors.extend(line)
                if len(errors) > 16384:
                    del errors[:-16384]

        reader = threading.Thread(target=read_stdout, daemon=True)
        drainer = threading.Thread(target=read_stderr, daemon=True)
        reader.start()
        drainer.start()

        def receive():
            try:
                return output.get(timeout=12)
            except queue.Empty as exc:
                raise AssertionError(f"no NDJSON reply; stderr={bytes(errors[-1500:])!r}") from exc

        try:
            hello = receive()
            assert hello["type"] == "hello", hello
            serial = 0

            def call(method, patch):
                nonlocal serial
                serial += 1
                ident = f"ob-a3-{serial}"
                req = dict(v=0, id=ident, type=method, patch=patch)
                child.stdin.write(json.dumps(req).encode() + b"\n")
                child.stdin.flush()
                for _ in range(256):
                    reply = receive()
                    if reply.get("re") == ident:
                        return reply
                raise AssertionError(f"missing reply for {ident}")

            started = call("loadGraph", v2)
            assert started["ok"] is True, started
            gen = started["gen"]
            assert snapshot(inputs) == before
            for method in ("loadGraph", "applyGraph"):
                rejected = call(method, v1)
                assert rejected["ok"] is False, rejected
                assert rejected.get("code"), rejected
                assert rejected["gen"] == gen, rejected
                assert snapshot(inputs) == before, f"{method} mutated v1 input or sibling"
            accepted = call("applyGraph", v2)
            assert accepted["ok"] is True, accepted
            assert int(accepted["gen"]) == int(gen) + 1, accepted
            assert snapshot(inputs) == before, "accepted v2 modified an input"
        finally:
            child.stdin.close()
            try:
                rc = child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
                raise
            reader.join(timeout=2)
            drainer.join(timeout=2)
            assert rc == 0, bytes(errors[-1600:])
        assert not any(".bak-v1" in p.name or p.name.endswith(".v1.json")
                       for p in inputs.iterdir())
    print("OB-a3 sidecar: both v1 graph requests refused; v2 accepted; no input writes")


if __name__ == "__main__":
    main()
