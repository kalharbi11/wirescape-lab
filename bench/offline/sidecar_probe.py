# SPDX-License-Identifier: GPL-3.0-only
"""Check failed soak documents against the real, device-free sidecar protocol."""
import json
import queue
import subprocess
import tempfile
import threading
from pathlib import Path


def classify_reply(response):
    """Retain the protocol's exact acknowledgement/refusal, without guessing."""
    if response.get("ok") is True:
        return {"sidecar_result": "ack", "sidecar_generation": response.get("gen")}
    if response.get("ok") is False:
        return {"sidecar_result": "refuse", "sidecar_generation": response.get("gen"),
                "sidecar_code": response.get("code"),
                "sidecar_message": response.get("message")}
    return {"sidecar_result": "unavailable", "sidecar_error": "invalid reply envelope"}


def check_loads(executable, rows, patches_dir, sample_rate):
    """Annotate each failed (patch, block) with a real null-audio loadGraph reply.

    One isolated engine process per block size, no audio/MIDI device flags, and
    one request at a time. A transport failure is not represented as a refusal.
    """
    for block in sorted({row["block_frames"] for row in rows}):
        group = [row for row in rows if row["block_frames"] == block]
        with tempfile.TemporaryDirectory(prefix="ws-sidecar-check-") as folder:
            command = [str(executable), "--null-audio", "--settings",
                       str(Path(folder) / "settings.json"), "--rate", str(sample_rate),
                       "--block", str(block)]
            process = None
            try:
                with (Path(folder) / "stderr.log").open("wb") as diagnostics:
                    process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE, stderr=diagnostics,
                                               bufsize=0)
                    lines = queue.Queue()

                    def receive():
                        for raw in process.stdout:
                            lines.put(raw)
                        lines.put(None)

                    threading.Thread(target=receive, daemon=True).start()

                    def next_message():
                        for _ in range(600):
                            raw = lines.get(timeout=25)
                            if raw is None:
                                raise RuntimeError("sidecar closed stdout before reply")
                            if len(raw) > 2097153:
                                raise RuntimeError("sidecar protocol line exceeds 2 MiB")
                            message = json.loads(raw.decode("utf-8"))
                            if isinstance(message, dict):
                                return message
                        raise RuntimeError("sidecar reply limit exceeded")

                    hello = next_message()
                    if hello.get("type") != "hello" or hello.get("v") != 0:
                        raise RuntimeError("expected protocol v0 hello")
                    for index, row in enumerate(group):
                        patch = json.loads((patches_dir / row["patch"]).read_text(encoding="utf-8"))
                        request_id = "soak-%d-%d" % (block, index)
                        request = {"v": 0, "id": request_id,
                                   "type": "loadGraph", "patch": patch}
                        encoded = (json.dumps(request, separators=(",", ":"),
                                              allow_nan=False) + "\n").encode("utf-8")
                        if len(encoded) > 2097153:
                            raise RuntimeError("loadGraph request exceeds 2 MiB")
                        process.stdin.write(encoded)
                        process.stdin.flush()
                        for _ in range(600):
                            reply = next_message()
                            if reply.get("re") == request_id:
                                row.update(classify_reply(reply))
                                break
                        else:
                            raise RuntimeError("matched loadGraph reply not received")
            except (OSError, ValueError, TypeError, RuntimeError, TimeoutError,
                    UnicodeError, queue.Empty, json.JSONDecodeError) as exc:
                for row in group:
                    if "sidecar_result" not in row:
                        row.update(sidecar_result="unavailable",
                                   sidecar_error="%s: %s" % (type(exc).__name__, exc))
            finally:
                if process is not None:
                    try:
                        if process.stdin and not process.stdin.closed:
                            process.stdin.close()
                        process.wait(timeout=12)
                    except (OSError, subprocess.TimeoutExpired):
                        process.kill()
                        process.wait()
    return rows
