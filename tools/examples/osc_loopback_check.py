# SPDX-License-Identifier: GPL-3.0-only
"""Check OSC In -> OSC Out against a built wirescape-engine, without devices.

  python tools/examples/osc_loopback_check.py build/native/wirescape-engine

Use W2's 03-osc-in-to-out.json when present, otherwise an equivalent inline
native v2 patch. Communicates via the existing sidecar stdin protocol only.
"""
from __future__ import annotations

import argparse
import json
import math
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from osc_in_sender import LOOPBACK, encode
from osc_out_receiver import decode

REPO_ROOT = Path(__file__).resolve().parents[2]
W2_PATCH = REPO_ROOT / "bench/owner_eval/windows/03-osc-in-to-out.json"
ADDRESS_IN = "/pico1/knob/1"
ADDRESS_OUT = "/ws/row/1"
PORT_IN, PORT_OUT = 9000, 9001
VALUES = (0.25, 0.75, 0.50)


def inline_patch() -> dict:
    """Equivalent minimal patch for the interval before W2 merges."""
    return {
        "format": "wirescape.native.patch", "version": 2,
        "modules": [
            {"id": 1, "module": "osc.in", "version": 1,
             "config": {"version": 1, "port": PORT_IN, "lan": False,
                        "rows": [{"pattern": ADDRESS_IN, "argument": 0, "kind": "cv",
                                  "input_min": 0, "input_max": 1,
                                  "output_min": 0, "output_max": 1,
                                  "smoothing_ms": 5, "timeout_ms": 1000, "stale": "hold"}]}},
            {"id": 2, "module": "osc.out", "version": 1,
             "config": {"version": 1, "port": PORT_OUT, "rate_hz": 100,
                        "rows": [{"address": ADDRESS_OUT, "kind": "cv", "deadband": 0.001}]}},
            {"id": 3, "module": "essentials.output", "version": 2},
        ],
        "connections": [{"kind": "signal",
                         "from": {"module": 1, "port": "row1"},
                         "to": {"module": 2, "port": "row1"}}],
        "outputs": [{"module": 3, "port": "audio", "bus_channel": 0},
                    {"module": 3, "port": "audio", "bus_channel": 1}],
    }


class Sidecar:
    """Bounded NDJSON stdin/stdout client, matching existing sidecar tests."""

    def __init__(self, executable: Path, settings: Path):
        self.messages: queue.Queue = queue.Queue()
        self.errors = bytearray()
        self.process = subprocess.Popen(
            [str(executable), "--null-audio", "--settings", str(settings)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.drainer = threading.Thread(target=self._drain, daemon=True)
        self.drainer.start()
        try:
            self.hello = self._next(10)
            if self.hello.get("type") != "hello":
                raise RuntimeError(f"engine did not send hello: {self.hello!r}")
        except Exception:
            try:
                self.close()
            except Exception:
                pass
            raise

    def _read(self) -> None:
        try:
            for line in self.process.stdout:
                self.messages.put(json.loads(line))
        except (ValueError, OSError) as exc:
            self.messages.put({"error": f"malformed sidecar stdout: {exc}"})

    def _drain(self) -> None:
        for chunk in iter(lambda: self.process.stderr.read(2048), b""):
            self.errors.extend(chunk)
            del self.errors[:-8192]

    def _next(self, timeout: float) -> dict:
        try:
            result = self.messages.get(timeout=timeout)
        except queue.Empty as exc:
            raise RuntimeError("sidecar response timeout; " + self.stderr()) from exc
        if "error" in result:
            raise RuntimeError(result["error"])
        return result

    def send_patch(self, patch: dict) -> None:
        # The engine accepts loadGraph without listing it in hello.capabilities
        # (session.cpp handles it unconditionally); a refusal comes back in the reply.
        self.process.stdin.write((json.dumps(
            {"v": 0, "id": "w1-load", "type": "loadGraph", "patch": patch},
            separators=(",", ":")) + "\n").encode())
        self.process.stdin.flush()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            reply = self._next(max(0.1, deadline - time.monotonic()))
            if reply.get("re") == "w1-load":
                if reply.get("ok") is not True:
                    raise RuntimeError(f"loadGraph refused: {reply!r}")
                return
        raise RuntimeError("loadGraph reply timeout")

    def stderr(self) -> str:
        return self.errors.decode(errors="replace")[-4000:]

    def close(self) -> None:
        try:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
            try:
                status = self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
                raise RuntimeError("engine did not exit after stdin EOF")
            if status != 0:
                raise RuntimeError(f"engine exited {status}; {self.stderr()}")
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait(timeout=5)


def receive_value(listener: socket.socket, sender: socket.socket,
                  expected: float, timeout: float) -> float:
    """Resend until a settled, changed OSC Out value is received."""
    deadline = time.monotonic() + timeout
    next_send = 0.0
    last = None
    while time.monotonic() < deadline:
        now = time.monotonic()
        if now >= next_send:
            sender.sendto(encode(ADDRESS_IN, expected), (LOOPBACK, PORT_IN))
            next_send = now + 0.05
        listener.settimeout(min(0.05, max(0.001, deadline - now)))
        try:
            packet, peer = listener.recvfrom(2048)
        except socket.timeout:
            continue
        if peer[0] != LOOPBACK:
            continue
        try:
            address, args = decode(packet)
        except (ValueError, UnicodeError, IndexError, struct.error):
            continue
        if address != ADDRESS_OUT or len(args) != 1 or not isinstance(args[0], (float, int)):
            continue
        last = float(args[0])
        if math.isfinite(last) and abs(last - expected) <= 0.03:
            return last
    raise RuntimeError(f"OSC Out mismatch: sent={expected:.5f}, last received={last!r}")


def run(executable: Path, patch_file: Path, timeout: float) -> int:
    if not executable.is_file():
        raise ValueError(f"engine executable not found: {executable}")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("--timeout must be finite and positive")
    if patch_file.is_file():
        patch = json.loads(patch_file.read_text(encoding="utf-8"))
        label = str(patch_file)
    else:
        patch = inline_patch()
        label = "inline W2-equivalent patch"
    if patch.get("format") != "wirescape.native.patch" or patch.get("version") != 2:
        raise ValueError("patch is not native v2")
    print(f"patch: {label}", flush=True)
    print(f"engine: {executable} --null-audio (temporary settings)", flush=True)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender, \
         tempfile.TemporaryDirectory(prefix="wlab-w1-") as tmp:
        listener.bind((LOOPBACK, PORT_OUT))
        engine = None
        error = None
        try:
            engine = Sidecar(executable, Path(tmp) / "settings.json")
            engine.send_patch(patch)
            for sent in VALUES:
                received = receive_value(listener, sender, sent, timeout)
                print(f"sent {sent:.5f} -> received {received:.5f} ({ADDRESS_OUT})", flush=True)
        except Exception as exc:
            error = exc
        finally:
            if engine is not None:
                try:
                    engine.close()
                except Exception as exc:
                    if error is None:
                        error = exc
        if error is not None:
            raise RuntimeError(f"{error}; stderr: {engine.stderr() if engine else 'unavailable'}")
    print("PASS: device-off OSC loopback 127.0.0.1:9000 -> 127.0.0.1:9001", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("engine", type=Path, help="path to built wirescape-engine executable")
    parser.add_argument("--patch", type=Path, default=W2_PATCH, help="W2 native v2 patch; inline fallback if missing")
    parser.add_argument("--timeout", type=float, default=4, help="seconds per value (default 4)")
    opts = parser.parse_args(argv)
    try:
        return run(opts.engine.resolve(), opts.patch, opts.timeout)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
