#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Owner-only real-audio OB1 edit session; --dry-run never launches a process."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import select
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "apps/studio/patches/basics-08-clocked-groove.json"
FACTS = ROOT / "facts/dsp/edit_continuity.md"
TIMEOUT = 8.0
MAX_LINE = 2 * 1024 * 1024


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument("--confirm-audio", action="store_true")
    p.add_argument("--confirm-midi", action="store_true")
    p.add_argument("--midi", action="store_true")
    p.add_argument("--midi-device")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--device")
    p.add_argument("--buffer", type=int, required=True, choices=(64, 128, 256, 512, 1024))
    p.add_argument("--rate", type=int, default=48000, choices=(44100, 48000, 96000))
    p.add_argument("--engine", type=Path, default=ROOT / "build/native/wirescape-engine")
    p.add_argument("--report", type=Path)
    a = p.parse_args(argv)
    if a.dry_run:
        if a.confirm_audio or a.confirm_midi or a.midi or a.midi_device:
            p.error("dry-run is device-off; do not supply confirmation or MIDI flags")
    else:
        if not a.confirm_audio or not a.device:
            p.error("owner must explicitly supply --confirm-audio and --device NAME")
        if a.midi and not (a.confirm_midi and a.midi_device):
            p.error("MIDI requires --confirm-midi and --midi-device ID")
        if not a.midi and (a.confirm_midi or a.midi_device):
            p.error("MIDI consent and device require --midi")
    return a


def initial_patch():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def edit_plan():
    """Ten cycles of ten edits; setup and queries are not counted."""
    document = initial_patch()
    edits = []

    def add(kind, **fields):
        edits.append(dict(v=0, id=f"edit-{len(edits)+1}", type=kind, **fields))

    def param(module, name, value):
        next(m for m in document["modules"] if m["id"] == module)["parameters"][name] = value
        add("setParam", moduleId=module, paramId=name, value=value)

    for cycle in range(10):
        groove = next(m for m in document["modules"] if m["id"] == 2)
        # The second config is sent immediately after the first terminal ACK,
        # before waiting for a periodic status. Count a deferred edit only on
        # its correlated applied event; a direct success is not a deferral.
        for key in (61, 60):
            groove["config"]["tracks"][0]["steps"][0]["key"] = key
            add("applyGraph", patch=copy.deepcopy(document))
        param(4, "frequency", 220 + 10 * (cycle + 1))
        param(6, "gain", .25 if cycle % 2 == 0 else .35)
        module = 100 + cycle
        # Connect a temporary oscillator to the existing FM input, not the
        # output bus (do not raise the patch's output level with another voice).
        edge = dict(kind="signal", **{"from": {"module": module, "port": "audio"}},
                    to={"module": 4, "port": "fm"})
        add("addModule", moduleId=module, moduleType="essentials.vco")
        add("connect", connection=edge)
        add("setParam", moduleId=module, paramId="frequency", value=110 + cycle)
        add("disconnect", connection=edge)
        add("removeModule", moduleId=module)
        param(7, "mix", .20 if cycle % 2 == 0 else .24)
    return edits


class EditLedger:
    def __init__(self):
        self.rows = []
        self.ids = set()

    @property
    def completed(self):
        return len(self.rows)

    def record(self, request_id, kind, reply, ack_ms, *, completion=None,
               module_id=None, completion_ms=None):
        if request_id in self.ids or reply.get("re") != request_id:
            raise ValueError("duplicate or wrong edit correlation")
        if not math.isfinite(ack_ms) or ack_ms < 0:
            raise ValueError("invalid ACK latency")
        deferred = reply.get("ok") is not True
        if deferred:
            defer_id = reply.get("deferId")
            if (kind != "applyGraph" or reply.get("ok") is not False or
                    reply.get("code") != "busy" or reply.get("deferred") is not True or
                    not isinstance(defer_id, str) or not defer_id or not completion or
                    completion.get("type") != "configDeferred" or
                    completion.get("deferId") != defer_id or
                    completion.get("moduleId") != module_id or
                    completion.get("outcome") != "applied"):
                raise ValueError("edit refused or deferred completion not applied")
        elif completion is not None:
            raise ValueError("unexpected deferred completion")
        result = reply.get("result", {})
        if not isinstance(result, dict) or result.get("unapplied"):
            raise ValueError("malformed result or applyGraph reports unapplied parameters")
        if completion_ms is not None and (not math.isfinite(completion_ms) or completion_ms < ack_ms):
            raise ValueError("invalid completion latency")
        self.ids.add(request_id)
        self.rows.append({"id": request_id, "type": kind, "ack_ms": ack_ms,
                          "deferred": deferred, "defer_id": reply.get("deferId"),
                          "completion_ms": completion_ms})


class XrunCounter:
    """Session-cumulative dropouts from actual v0 status, never sum samples."""
    def __init__(self, device, buffer, rate=None):
        self.device = device
        self.buffer = buffer
        self.rate = rate
        self.count = None
        self.samples = 0

    def observe(self, audio):
        if (audio.get("state") != "running" or audio.get("deviceId") != self.device or
                audio.get("bufferFrames") != self.buffer or
                (self.rate is not None and audio.get("sampleRate") != self.rate)):
            raise ValueError("audio not running on requested device/buffer/rate")
        count = audio.get("dropouts")
        if type(count) is not int or not 0 <= count <= 2**64-1:
            raise ValueError("missing or invalid cumulative xrun count")
        if self.count is not None and count < self.count:
            raise ValueError("cumulative xrun count regressed")
        self.count = count
        self.samples += 1


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON member")
        obj[key] = value
    return obj


def decode_line(line):
    def invalid_constant(value):
        raise ValueError("nonfinite JSON value: " + value)
    value = json.loads(line, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise ValueError("non-object engine message")
    return value


class PipeStream:
    """One owned sidecar, nonblocking bounded I/O; Linux owner path only."""
    def __init__(self, argv):
        self.child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, bufsize=0)
        self.in_fd = self.child.stdin.fileno()
        self.out_fd = self.child.stdout.fileno()
        os.set_blocking(self.in_fd, False)
        os.set_blocking(self.out_fd, False)
        self.pending = bytearray()

    @staticmethod
    def remaining(deadline):
        seconds = deadline - time.monotonic()
        if seconds <= 0:
            raise ValueError("sidecar deadline exceeded")
        return seconds

    def send(self, message, deadline):
        raw = memoryview((json.dumps(message, separators=(",", ":"), allow_nan=False) + "\n").encode())
        if len(raw) > MAX_LINE:
            raise ValueError("command too large")
        while raw:
            if not select.select([], [self.in_fd], [], self.remaining(deadline))[1]:
                raise ValueError("sidecar write timeout")
            try:
                raw = raw[os.write(self.in_fd, raw):]
            except BlockingIOError:
                continue

    def receive(self, deadline):
        while True:
            self.remaining(deadline)
            end = self.pending.find(b"\n")
            if end >= 0:
                if end > MAX_LINE:
                    raise ValueError("oversized sidecar message")
                line = bytes(self.pending[:end])
                del self.pending[:end+1]
                return decode_line(line)
            if len(self.pending) > MAX_LINE:
                raise ValueError("oversized or unterminated sidecar message")
            if not select.select([self.out_fd], [], [], self.remaining(deadline))[0]:
                raise ValueError("sidecar read timeout")
            try:
                chunk = os.read(self.out_fd, 65536)
            except BlockingIOError:
                continue
            if not chunk:
                raise ValueError("sidecar EOF before evidence completed")
            self.pending.extend(chunk)

    def close(self):
        try:
            self.child.stdin.close()
            try:
                # Drain the owned pipe until EOF, without accepting it as a
                # final xrun snapshot. The last running status is our endpoint.
                deadline = time.monotonic() + 5
                while True:
                    if not select.select([self.out_fd], [], [], self.remaining(deadline))[0]:
                        raise ValueError("sidecar shutdown timeout")
                    try:
                        if not os.read(self.out_fd, 65536):
                            break
                    except BlockingIOError:
                        continue
                self.child.wait(timeout=self.remaining(deadline))
            except (OSError, ValueError, subprocess.TimeoutExpired):
                self.child.terminate()
                try:
                    self.child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.child.kill()
                    self.child.wait(timeout=2)
                raise ValueError("sidecar did not shut down cleanly")
            if self.child.returncode != 0:
                raise ValueError("sidecar exit was nonzero")
        finally:
            self.child.stdout.close()


class Session:
    def __init__(self, stream, meter, source):
        self.stream = stream
        self.meter = meter
        self.source = source
        self.token = None
        self.gen = None
        self.engine_sha = None
        self.ready = False
        self.ledger = EditLedger()
        self.deferred_ids = set()

    def message(self, deadline):
        msg = self.stream.receive(deadline)
        if type(msg.get("v")) is not int or msg["v"] != 0 or msg.get("session") != self.token:
            raise ValueError("protocol/session mismatch")
        if msg.get("type") == "status":
            audio = msg.get("status", {}).get("audio", {})
            if self.ready or audio.get("state") == "running":
                self.meter.observe(audio)
                self.ready = True
            elif audio.get("state") != "starting":
                raise ValueError("audio startup failed")
        return msg

    def start(self):
        deadline = time.monotonic() + TIMEOUT
        hello = self.stream.receive(deadline)
        self.token = hello.get("session")
        self.engine_sha = hello.get("engine", {}).get("sha")
        if (hello.get("type") != "hello" or type(hello.get("v")) is not int or hello["v"] != 0
                or not isinstance(self.token, str) or not self.token
                or hello.get("protocol") != 0
                or not isinstance(self.engine_sha, str)
                or not re.fullmatch(r"[0-9a-f]{12,40}", self.engine_sha)
                or not self.source.startswith(self.engine_sha)
                or "configDeferred" not in hello.get("capabilities", [])):
            raise ValueError("invalid hello, stale build, or missing configDeferred capability")
        audio = hello.get("audio", {})
        if audio.get("state") == "running":
            self.meter.observe(audio)
            self.ready = True
        elif audio.get("state") != "starting":
            raise ValueError("audio unavailable at startup")
        self.fresh_status()

    def fresh_status(self):
        before = self.meter.samples
        deadline = time.monotonic() + TIMEOUT
        while self.meter.samples == before:
            msg = self.message(deadline)
            if "re" in msg or msg.get("type") == "configDeferred":
                raise ValueError("unsolicited/duplicate terminal message")

    def request(self, command, *, edit=False):
        sent = time.monotonic()
        deadline = sent + TIMEOUT
        self.stream.send(command, deadline)
        while True:
            msg = self.message(deadline)
            if msg.get("type") == "configDeferred":
                raise ValueError("unsolicited deferred completion")
            if "re" in msg:
                break
        if msg.get("re") != command["id"] or "type" in msg:
            raise ValueError("wrong terminal reply ID/type")
        ack = (time.monotonic() - sent) * 1000
        generation = msg.get("gen")
        if not isinstance(generation, str) or not re.fullmatch(r"[0-9]+", generation):
            raise ValueError("invalid reply generation")
        gen = int(generation)
        if self.gen is not None:
            swaps = {"loadGraph", "applyGraph", "connect", "disconnect", "addModule", "removeModule"}
            expected = self.gen + int(command["type"] in swaps and msg.get("ok") is True)
            if gen != expected:
                raise ValueError("reply generation does not match accepted edit")
        self.gen = gen
        completion = None
        if (edit and command["type"] == "applyGraph" and msg.get("ok") is False
                and msg.get("code") == "busy" and msg.get("deferred") is True):
            defer_id = msg.get("deferId")
            if not isinstance(defer_id, str) or not defer_id or defer_id in self.deferred_ids:
                raise ValueError("missing or reused deferId")
            self.deferred_ids.add(defer_id)
            while True:
                event = self.message(deadline)
                if "re" in event:
                    raise ValueError("duplicate terminal reply during deferral")
                if event.get("type") == "configDeferred":
                    completion = event
                    break
            completed_gen = completion.get("generation")
            if (not isinstance(completed_gen, str) or
                    not re.fullmatch(r"[0-9]+", completed_gen) or int(completed_gen) != gen + 1):
                raise ValueError("deferred completion did not publish a new generation")
            self.gen = int(completed_gen)
        if edit:
            self.ledger.record(command["id"], command["type"], msg, ack,
                               completion=completion, module_id=2,
                               completion_ms=(time.monotonic()-sent)*1000 if completion else None)
        elif msg.get("ok") is not True:
            raise ValueError("setup command refused: " + command["type"])
        return msg

    def execute(self, midi_device=None):
        self.start()
        self.request(dict(v=0, id="setup-hello", type="hello", capabilities=["configDeferred"]))
        self.request(dict(v=0, id="setup-load", type="loadGraph", patch=initial_patch()))
        if midi_device:
            self.request(dict(v=0, id="setup-midi", type="setMidiEnabled",
                              deviceId=midi_device, on=True))
        self.fresh_status()
        for command in edit_plan():
            self.request(command, edit=True)
            # Preserve the intentional tight pair of configuration commands.
            # All other edits allow one actual status sample between edits.
            if command["type"] != "applyGraph" or command["id"] in {
                    f"edit-{cycle*10+2}" for cycle in range(10)}:
                self.fresh_status()
        self.fresh_status()
        if self.ledger.completed != 100 or self.meter.count != 0:
            raise ValueError("100 accepted edits and zero xruns required")
        if not self.deferred_ids:
            raise ValueError("no actual correlated config deferral observed")


def cn_cost_rows():
    content = FACTS.read_text(encoding="utf-8")
    # Cite the original final A69a table, not the later independent cross-check.
    start = content.rindex("| A69a row (256 frames, x64) |")
    table = content[start:].split("\n\n", 1)[0]
    rows = []
    for label in ("Black Ice Choir single-instance max", "Clocked Groove max dual-instance"):
        match = re.search(r"^\| " + re.escape(label) + r" \| ([\d,]+) \| (\d+) \|$", table, re.M)
        if not match:
            raise ValueError("required final CN cost row missing")
        rows.append({"row": label, "ir": int(match[1].replace(",", "")),
                     "block": int(match[2]), "buffer_frames": 256, "arch": "linux-x64",
                     "source": "facts/dsp/edit_continuity.md (A69a transition cost)",
                     "run": "https://github.com/kalharbi11/wirescape-lab/actions/runs/45576526381"})
    return rows


def git_source():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                  text=True, timeout=10).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("unavailable checkout SHA")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT,
                               text=True, timeout=10).strip():
        raise ValueError("owner must use a clean checkout")
    return sha


def run(args):
    result = {"status": "not-run", "mode": "dry-run" if args.dry_run else "owner-real-audio",
              "requested_edits": 100, "completed_edits": 0, "xruns": None,
              "buffer_frames": args.buffer, "sample_rate": args.rate,
              "device": args.device, "build_sha": None, "visible_stutter": None,
              "visible_stutter_note": "observed in 6b",
              "edits": [], "cn_transition_costs": cn_cost_rows(),
              "xrun_scope": "session-cumulative through final running status; not a shutdown counter"}
    if args.dry_run:
        result["planned_edits"] = [dict(id=e["id"], type=e["type"]) for e in edit_plan()]
        return 0, result
    stream = session = None
    try:
        # No real device launch in CI or on a non-ARM64/non-Linux machine.
        if (not args.confirm_audio or not args.device or os.environ.get("CI") or
                os.environ.get("GITHUB_ACTIONS") or platform.system() != "Linux" or
                platform.machine().lower() not in ("aarch64", "arm64")):
            raise ValueError("real session is owner-only on Linux ARM64 outside CI")
        if args.midi and not (args.confirm_midi and args.midi_device):
            raise ValueError("explicit MIDI consent/device required")
        result["source_sha"] = git_source()
        binary = args.engine.resolve(strict=True)
        result["binary_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="wirescape-owner-acceptance-") as temp:
            command = [str(binary), "--confirm-audio", "--device", args.device,
                       "--block", str(args.buffer), "--rate", str(args.rate),
                       "--settings", str(Path(temp) / "settings.json")]
            if args.midi:
                command.append("--confirm-midi")
            stream = PipeStream(command)
            session = Session(stream, XrunCounter(args.device, args.buffer, args.rate),
                              result["source_sha"])
            try:
                session.execute(args.midi_device if args.midi else None)
            finally:
                stream.close()
                stream = None
        result["status"] = "owner-observation-required"
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result["status"] = "failed"
        result["error"] = str(error).replace(str(ROOT), "<checkout>")
    finally:
        if session:
            result.update(build_sha=session.engine_sha, completed_edits=session.ledger.completed,
                          xruns=session.meter.count, status_samples=session.meter.samples,
                          edits=session.ledger.rows, deferred_edits=len(session.deferred_ids))
    return (0 if result["status"] == "owner-observation-required" else 1), result


def main(argv=None):
    args = parse_args(argv)
    try:
        code, result = run(args)
        output = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.report:
            # Do not overwrite any existing report or source file.
            with args.report.open("x", encoding="utf-8") as file:
                file.write(output)
        print(output, end="")
        return code
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print("acceptance session: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
