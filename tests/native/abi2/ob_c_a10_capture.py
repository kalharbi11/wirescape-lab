# SPDX-License-Identifier: GPL-3.0-only
"""OB-c A10: real, device-off sidecar null-sink capture helpers.

This module is source-only until an authorized CTest registration supplies the
compiled wirescape_engine_sidecar. It does not import or modify sidecar tests.
Native/setup errors must fail normally, never be marked expected product failure.
"""
from __future__ import annotations

import json
import os
import queue
import re
import struct
import subprocess
import threading
import time
from pathlib import Path

HEADER = struct.Struct("<8sIIIIIIQ")
OPEN_SEGMENT = (1 << 64) - 1
RATE = 48000
CHANNELS = 16
ROOT = Path(__file__).resolve().parents[3]


def sidecar_binary() -> Path:
    raw = os.environ.get("WIRESCAPE_OB_C_SIDECAR")
    if not raw:
        raise RuntimeError("INFRA: WIRESCAPE_OB_C_SIDECAR must name built native sidecar")
    path = Path(raw).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"INFRA: real sidecar binary absent: {path}")
    return path


def drone(frequency: float = 220) -> dict:
    return {
        "format": "wirescape.native.patch", "version": 2,
        "modules": [
            {"id": 1, "module": "essentials.vco", "parameters": {"frequency": frequency}},
            {"id": 2, "module": "essentials.output", "parameters": {}},
        ],
        "connections": [{"kind": "signal",
                         "from": {"module": 1, "port": "audio"},
                         "to": {"module": 2, "port": "audio"}}],
        "outputs": [{"module": 2, "port": "audio", "bus_channel": 0},
                    {"module": 2, "port": "audio", "bus_channel": 1}],
    }


class CaptureClient:
    """Production sidecar process with real null-sink block/mark files; no devices."""
    def __init__(self, binary: Path, path: Path, *, rate=RATE, block=128):
        self.path = path
        self.block = block
        self._serial = 0
        self._messages = queue.Queue()
        self._pushes = []
        self._stderr = bytearray()
        self.process = subprocess.Popen(
            [str(binary), "--null-audio", "--bench-summary",
             "--settings", str(path.with_suffix(".settings.json")),
             "--rate", str(rate), "--block", str(block),
             "--capture-null-sink", str(path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()
        self.hello = self._next(timeout=12)
        assert self.hello["type"] == "hello", f"INFRA: no sidecar hello: {self.hello!r}"
        assert self.hello["audio"]["sampleRate"] == rate
        assert self.hello["audio"]["bufferFrames"] == block

    def _read_stdout(self):
        try:
            for line in self.process.stdout:
                self._messages.put(json.loads(line))
        except Exception as exc:
            self._messages.put(exc)

    def _read_stderr(self):
        for chunk in iter(lambda: self.process.stderr.read(4096), b""):
            self._stderr.extend(chunk)

    def _next(self, timeout=12):
        item = self._messages.get(timeout=timeout)
        if isinstance(item, Exception):
            raise RuntimeError("INFRA: sidecar stdout reader failed") from item
        return item

    def call(self, kind: str, **payload) -> dict:
        self._serial += 1
        id_ = f"a10_{self._serial}"
        command = {"v": 0, "id": id_, "type": kind, **payload}
        self.process.stdin.write((json.dumps(command) + "\n").encode())
        self.process.stdin.flush()
        deadline = time.monotonic() + 12
        while True:
            reply = self._next(max(0.01, deadline - time.monotonic()))
            if reply.get("re") == id_:
                assert reply.get("ok") is True, f"INFRA: sidecar refused {kind}: {reply}"
                return reply
            self._pushes.append(reply)

    def statuses(self, count: int) -> list[dict]:
        result = []
        until = time.monotonic() + max(12, count * .5)
        while len(result) < count:
            item = self._pushes.pop(0) if self._pushes else self._next(max(.01, until - time.monotonic()))
            if item.get("type") == "status":
                result.append(item["status"])
        return result

    def close(self) -> str:
        self.process.stdin.close()
        code = self.process.wait(timeout=20)
        self._stdout_thread.join(timeout=3)
        self._stderr_thread.join(timeout=3)
        stderr = self._stderr.decode(errors="replace")
        assert code == 0, f"INFRA: sidecar exited {code}: {stderr}"
        assert re.search(r"capture segments=\d+ blocks=\d+ failed=0", stderr), stderr
        assert re.search(r"overruns=0(?:\s|$)", stderr), f"PRODUCT: null-sink overrun: {stderr}"
        return stderr


def read_segments(path: Path) -> list[dict]:
    """Strictly account for all frame bytes; no missing/duplicated capture blocks."""
    raw = path.read_bytes()
    cursor, result = 0, []
    while cursor < len(raw):
        assert len(raw) - cursor >= HEADER.size, "INFRA: partial capture header"
        magic, version, hsize, rate, channels, block, index, blocks = HEADER.unpack_from(raw, cursor)
        assert (magic, version, hsize, index) == (b"WSNSCAP1", 1, HEADER.size, len(result))
        assert blocks != OPEN_SEGMENT, "INFRA: unclosed capture segment"
        assert rate == RATE and channels == CHANNELS, "INFRA: capture rate/bus mismatch"
        cursor += HEADER.size
        sample_bytes = int(blocks) * block * channels * 4
        assert len(raw) - cursor >= sample_bytes, "INFRA: truncated frame data"
        result.append({"blocks": int(blocks), "block": block, "frames": int(blocks) * block,
                       "bytes": memoryview(raw)[cursor:cursor + sample_bytes]})
        cursor += sample_bytes
    assert cursor == len(raw) and result, "INFRA: unparsed bytes/empty capture"
    return result


def read_marks(path: Path, segments: list[dict]) -> list[dict]:
    marks = [json.loads(line) for line in Path(str(path) + ".marks").read_text().splitlines()]
    total_blocks = sum(s["blocks"] for s in segments)
    assert all({"re", "type", "ok", "gen", "b0", "b1"} == set(m) for m in marks)
    assert all(m["ok"] is True and 0 <= m["b0"] <= m["b1"] <= total_blocks for m in marks)
    assert all(a["b1"] <= b["b0"] for a, b in zip(marks, marks[1:])), "INFRA: marks reorder"
    return marks


def channel(segment: dict, channel_index: int = 0) -> tuple[float, ...]:
    n = segment["frames"] * CHANNELS
    values = struct.unpack("<" + "f" * n, segment["bytes"])
    return values[channel_index::CHANNELS]


def marker(marks: list[dict], type_: str) -> dict:
    hits = [m for m in marks if m["type"] == type_]
    assert len(hits) == 1, f"INFRA: expected one {type_} mark; got {hits}"
    return hits[0]
