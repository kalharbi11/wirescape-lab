# SPDX-License-Identifier: GPL-3.0-only
"""OB-g1: device-off OSC endurance, localhost only, null-audio sidecar."""
from __future__ import annotations

import argparse
from collections import deque
import json
import math
import os
from pathlib import Path
import platform
import queue
import re
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"
TIERS = {"L0": 60, "L1": 600, "L2": 3600, "L3": 14400, "L4": 43200, "L5": 86400}
PROFILES = ("osc-gates", "osc-heavy", "osc-stress", "midi-m8", "mixed")
MIDI_PROFILES = frozenset(("midi-m8", "mixed"))
OSC_LOAD_PROFILES = frozenset(("osc-heavy", "osc-stress", "mixed"))
MIDI_STOP_FIELDS = ("dropped", "ring_full", "malformed", "send_fail", "release_panics")
A2_FAILURES = ("missing_echo", "missing_gate_edge", "stuck_gate",
               "gate_edge_order", "unexpected_gate_edge")


class Stop(Exception):
    def __init__(self, check, detail, witness=None):
        self.check, self.detail, self.witness = check, detail, witness
        super().__init__(f"{check}: {detail}")


def osc_string(value):
    data = value.encode("ascii") + b"\0"
    return data + b"\0" * (-len(data) % 4)


def encode(address, value):
    if not address.startswith("/") or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("invalid OSC address/value")
    return osc_string(address) + osc_string(",f") + struct.pack(">f", value)


def decode(packet):
    def read(pos):
        end = packet.find(b"\0", pos)
        if end < 0:
            raise ValueError("unterminated OSC string")
        return packet[pos:end].decode("ascii"), (end + 4) & ~3
    address, pos = read(0)
    tags, pos = read(pos)
    if not address.startswith("/") or tags != ",f" or pos + 4 > len(packet):
        raise ValueError("unexpected OSC packet")
    return address, struct.unpack_from(">f", packet, pos)[0]


def row(address, kind="cv"):
    return {"pattern": address, "argument": 0, "kind": kind,
            "input_min": 0, "input_max": 1, "output_min": 0, "output_max": 1,
            "smoothing_ms": 0, "timeout_ms": 0, "stale": "hold"}


def patch(profile, port_in, port_out):
    if profile not in PROFILES:
        raise ValueError(profile)
    modules = [
        {"id": 1, "module": "osc.in", "version": 1,
         "config": {"version": 1, "port": port_in, "lan": False,
                    "rows": [row("/io/seq"), row("/io/gate", "gate")]}},
        {"id": 2, "module": "osc.out", "version": 1,
         "config": {"version": 1, "port": port_out, "rate_hz": 500,
                    "rows": [{"address": "/io/echo", "kind": "cv", "deadband": 0},
                             {"address": "/io/edge", "kind": "gate", "deadband": 0}]}},
        {"id": 90, "module": "essentials.output", "version": 2}]
    if profile in OSC_LOAD_PROFILES:
        # Each OSC In module permits 8 configured rows, not 64.
        for group in range(8):
            modules.append({"id": 10 + group, "module": "osc.in", "version": 1,
                            "config": {"version": 1, "port": port_in, "lan": False,
                                       "rows": [row(f"/io/load/{group * 8 + i:02d}",
                                                    "gate" if (group * 8 + i) % 2 else "cv")
                                                for i in range(8)]}})
    connections = [{"kind": "signal",
                    "from": {"module": 1, "port": f"row{i}"},
                    "to": {"module": 2, "port": f"row{i}"}} for i in (1, 2)]
    if profile in MIDI_PROFILES:
        modules.extend([
            {"id": 80, "module": "midi.in", "version": 1,
             "config": {"endpoint": "all_enabled"}},
            {"id": 81, "module": "midi.to_cv", "version": 1,
             "parameters": {"voice_count": 4}},
        ])
        connections.append({"kind": "event",
                            "from": {"module": 80, "port": "midi"},
                            "to": {"module": 81, "port": "midi"}})
    return {"format": "wirescape.native.patch", "version": 2,
            "settings": {"sample_rate": 48000, "max_block_frames": 128,
                         "max_channels": 16, "seed": 305},
            "modules": modules,
            "connections": connections,
            "outputs": [{"module": 90, "port": "audio", "bus_channel": i}
                        for i in (0, 1)]}


def sidecar_args(engine, settings, profile):
    if profile not in PROFILES:
        raise ValueError(profile)
    flags = [str(engine), "--null-audio", "--bench-summary", "--settings", str(settings)]
    if profile in MIDI_PROFILES:
        flags.append("--scripted-midi")
    return flags


class Sidecar:
    def __init__(self, engine, settings, profile="osc-gates"):
        self.messages = queue.Queue()
        self.errors = deque(maxlen=300)
        self.proc = subprocess.Popen(
            sidecar_args(engine, settings, profile),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "WIRESCAPE_OSC_ENQUEUE_DIAGNOSTIC": "1"})
        threading.Thread(target=self._read, daemon=True).start()
        self.error_reader = threading.Thread(target=self._err, daemon=True)
        self.error_reader.start()
        try:
            self.hello = self.messages.get(timeout=10)
            if self.hello.get("type") != "hello":
                raise Stop("engine_hello", str(self.hello))
        except Exception:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.proc.stdout:
                try:
                    self.messages.put(json.loads(line))
                except (UnicodeDecodeError, ValueError):
                    self.messages.put({"type": "invalid_stdout"})
        except OSError:
            pass

    def _err(self):
        for line in self.proc.stderr:
            self.errors.append(line.decode(errors="replace").strip())

    def load(self, graph, serial):
        token = f"io-load-{serial}"
        try:
            self.proc.stdin.write((json.dumps(
                {"v": 0, "id": token, "type": "loadGraph", "patch": graph},
                separators=(",", ":")) + "\n").encode())
            self.proc.stdin.flush()
        except OSError as exc:
            raise Stop("engine_exit", str(exc)) from exc
        pending = []
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                msg = self.messages.get(timeout=min(.1, max(.001, deadline - time.monotonic())))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise Stop("engine_exit", f"exit={self.proc.returncode}")
                continue
            if msg.get("re") == token:
                if msg.get("ok") is not True:
                    raise Stop("loadGraph", str(msg))
                return pending
            pending.append(msg)
        raise Stop("loadGraph_timeout", token)

    def close(self):
        try:
            if self.proc.stdin and not self.proc.stdin.closed:
                self.proc.stdin.close()
        except OSError:
            pass
        try:
            code = self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            code = self.proc.wait(timeout=5)
        # The child has exited: drain its final post-join diagnostic before snapshot.
        self.error_reader.join(timeout=1)
        return code, "\n".join(self.errors)


def counters(message):
    state = message.get("status", message)
    result = {}
    osc = state.get("osc", {})
    for kind in ("routes", "out"):
        for i, route in enumerate(osc.get(kind, [])):
            for name in ("dropped", "malformed", "truncated"):
                if type(route.get(name)) is int:
                    result[f"osc.{kind}.{route.get('module', i)}.{name}"] = route[name]
    midi = state.get("midi", {})
    observed = midi.get("counters", midi)
    for name in (*MIDI_STOP_FIELDS, "release_panic"):
        if type(observed.get(name)) is int:
            result[f"midi.{name}"] = observed[name]
    return result


def osc_drop_diagnostics(status):
    """Preserve optional OSC attribution fields without affecting stop gates.

    Listener snapshots repeat across routes on a shared port. Deduplicate
    identical observations, but retain disagreements: relaxed atomic reads
    are observational, not one transactional service snapshot.
    """
    routes, listeners = {}, {}
    for i, route in enumerate(status.get("osc", {}).get("routes", [])):
        port = route.get("port")
        split = {name: route[name] for name in ("budget_dropped", "enqueue_dropped")
                 if type(route.get(name)) is int}
        if split:
            if type(port) is int:
                split["port"] = port
            routes[str(route.get("module", i))] = split
        observed = {name: route["listener_" + name]
                    for name in ("budget_dropped", "enqueue_dropped")
                    if type(route.get("listener_" + name)) is int}
        if observed and type(port) is int:
            snapshots = listeners.setdefault(str(port), [])
            if observed not in snapshots:
                snapshots.append(observed)
    return {"routes": routes, "listeners": listeners}


def midi_received(status):
    details = status.get("midi", {}).get("counters")
    if not isinstance(details, dict) or any(
            type(details.get(name)) is not int for name in ("received", *MIDI_STOP_FIELDS)):
        raise Stop("midi_counters_unavailable", "scripted Host counters absent or invalid")
    return details["received"]


def check_counters(before, after):
    for name, value in after.items():
        if name in before:
            if value > before[name]:
                raise Stop("counter_rise", f"{name}: {before[name]} -> {value}")
            if value < before[name]:
                raise Stop("counter_reset", f"{name}: {before[name]} -> {value}")


def record_counters(result, baseline, current):
    """Keep the actual failing sample and include fresh-service stop counters.

    OSC route/out counters start at zero when the graph creates the service.
    MIDI hello supplies the pre-load baseline for its own counters. A newly
    exposed OSC key (including mixed profiles) must not hide early losses.
    """
    for name in current:
        baseline.setdefault(name, 0)
    result["counters_before"] = dict(baseline)
    result["counters_after"] = dict(current)
    check_counters(baseline, current)


def record_midi_received(result, received):
    """Retain the observed sample even when the monotonicity check fails."""
    previous = result["midi_received_after"]
    result["midi_received_after"] = received
    if received < previous:
        raise Stop("midi_counter_reset", f"received count decreased: {previous} -> {received}")
    return received > previous


def percentile(values, percent):
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(len(values) * percent / 100) - 1)]


def rss_bytes(pid):
    if sys.platform.startswith("linux"):
        try:
            match = re.search(r"^VmRSS:\s+(\d+)\s+kB",
                              Path(f"/proc/{pid}/status").read_text(), re.M)
            return int(match.group(1)) * 1024 if match else None
        except (OSError, ValueError):
            return None
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t)]
            handle = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x0400, False, pid)
            if handle:
                try:
                    data = PMC()
                    data.cb = ctypes.sizeof(data)
                    if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(data), data.cb):
                        return int(data.WorkingSetSize)
                finally:
                    ctypes.windll.kernel32.CloseHandle(handle)
        except (OSError, AttributeError, ImportError):
            pass
    return None


class Watch:
    def __init__(self):
        self.sequence = 0
        self.expected_seq = deque()
        self.expected_edges = deque()
        self.latencies_ms = []
        self.last_gate = 0
        self.gate_seen = False
        self.fall_at = None
        self.high_edge = None
        self.edit = None
        self.events = deque(maxlen=20000)

    def note(self, now, event):
        self.events.append((now, event))

    def begin_edit(self, serial, now):
        """Pin only the specific sends/edges already in flight at loadGraph start."""
        self.edit = {
            "serial": serial, "started_at": now, "completed_at": None,
            "sequences": tuple(self.expected_seq),
            "edges": tuple(self.expected_edges),
            "active_high": self.high_edge if self.last_gate == 1 else None,
        }
        self.note(now, f"loadGraph start id={serial} seq={len(self.edit['sequences'])} "
                  f"edges={len(self.edit['edges'])} high={self.edit['active_high'] is not None}")

    def end_edit(self, now):
        if self.edit is not None:
            self.edit["completed_at"] = now
            self.note(now, f"loadGraph end id={self.edit['serial']}")

    def attribute_fault(self, failure, now):
        """Return an A2 witness only for a pre-edit in-flight sentinel.

        A later failure with the same check name is never made expected merely
        because an older config edit occurred. At most 350ms after the actual
        loadGraph response is attributable (250ms OSC echo budget + margin).
        """
        edit = self.edit
        if (edit is None or edit["completed_at"] is None or
                not edit["started_at"] <= now <= edit["completed_at"] + .350):
            return None
        witness = failure.witness
        if failure.check == "missing_echo":
            matched = witness in edit["sequences"]
            kind = "sequence"
        elif failure.check in ("missing_gate_edge", "gate_edge_order"):
            matched = witness in edit["edges"]
            kind = "edge"
        elif failure.check == "stuck_gate":
            matched = witness is not None and (
                witness == edit["active_high"] or witness in edit["edges"])
            kind = "high_edge"
        else:
            return None
        if not matched:
            return None
        return {
            "edit_id": edit["serial"],
            "started_at": edit["started_at"],
            "completed_at": edit["completed_at"],
            "observed_at": now,
            "pending_at_edit": {"sequences": len(edit["sequences"]),
                                "edges": len(edit["edges"]),
                                "active_high": edit["active_high"] is not None},
            "witness": {"kind": kind, "value": witness[0], "sent_at": witness[1]},
            "fault": {"check": failure.check, "detail": failure.detail},
        }

    def send_seq(self, now):
        self.sequence += 1
        value = (self.sequence % 1023 + 1) / 1024
        self.expected_seq.append((value, now))
        self.note(now, f"seq {self.sequence} value={value:.6f}")
        return "/io/seq", value

    def send_gate(self, now, high):
        value = int(high)
        self.expected_edges.append((value, now))
        if not high:
            self.fall_at = now
        self.note(now, f"gate_out {value}")
        return "/io/gate", float(value)

    def receive(self, now, address, value):
        if not math.isfinite(value):
            raise Stop("malformed_echo", address)
        self.note(now, f"osc_out {address}={value:.6f}")
        if address == "/io/echo":
            if self.expected_seq and abs(value - self.expected_seq[0][0]) <= .0005:
                _, start = self.expected_seq.popleft()
                self.latencies_ms.append((now - start) * 1000)
        elif address == "/io/edge":
            level = int(value >= .5)
            if not self.gate_seen:
                self.gate_seen = True
                if not level:
                    return
            if level == self.last_gate:
                return
            self.last_gate = level
            if not self.expected_edges:
                raise Stop("unexpected_gate_edge", str(level))
            expected, _ = self.expected_edges.popleft()
            if level != expected:
                raise Stop("gate_edge_order", f"expected={expected} actual={level}",
                           (expected, _))
            if level:
                self.high_edge = (expected, _)
            else:
                self.high_edge = None
                self.fall_at = None

    def check(self, now):
        if self.fall_at is not None and self.last_gate == 1 and now - self.fall_at > .050:
            raise Stop("stuck_gate", "gate >50ms after scheduled fall", self.high_edge)
        if self.expected_edges and now - self.expected_edges[0][1] > .050:
            raise Stop("missing_gate_edge", str(self.expected_edges[0][0]),
                       self.expected_edges[0])
        if self.expected_seq and now - self.expected_seq[0][1] > .250:
            raise Stop("missing_echo", f"seq value={self.expected_seq[0][0]:.6f}",
                       self.expected_seq[0])


def bench_line(stderr):
    for line in reversed(stderr.splitlines()):
        if line.startswith("bench "):
            try:
                return {k: float(v) if any(c in v for c in ".eE") else int(v)
                        for k, v in re.findall(r"([a-z_0-9]+)=([0-9.eE+\-]+)", line)}
            except ValueError:
                return None
    return None


BENCH_STOP_FIELDS = ("overruns", "faults", "overrun_render_count", "overrun_wake_count")


def check_bench(bench):
    if bench is None:
        raise Stop("bench_missing", "expected --bench-summary on shutdown")
    for key in BENCH_STOP_FIELDS:
        if key not in bench or not isinstance(bench[key], (float, int)):
            raise Stop("bench_missing", f"missing/invalid bench field: {key}")
        if not math.isfinite(bench[key]) or bench[key] < 0:
            raise Stop("bench_missing", f"invalid bench field: {key}={bench[key]}")
        if bench[key] > 0:
            raise Stop("bench_fault", f"{key}={bench[key]}")


def enqueue_reason_summaries(stderr):
    """A67 opt-in rows are observations, not an exhaustive cross-epoch total."""
    rows, malformed = [], 0
    keys = ("module", "port", "total", "invalid", "capacity", "state", "other")
    pattern = "osc_enqueue_reason " + " ".join(
        key + r"=([0-9]{1,20})" for key in keys)
    for line in stderr.splitlines():
        if not line.startswith("osc_enqueue_reason "):
            continue
        match = re.fullmatch(pattern, line)
        if not match:
            malformed += 1
            continue
        row = dict(zip(keys, map(int, match.groups())))
        if (not 1 <= row["module"] <= 0xffffffff
                or not 1 <= row["port"] <= 65535
                or any(value > 0xffffffffffffffff for value in row.values())
                or row["total"] == 0
                or row["total"] != sum(row[key] for key in keys[3:])):
            malformed += 1
            continue
        rows.append(row)
    return {"observations": rows, "malformed": malformed} if rows or malformed else None


def apply_shutdown_checks(result, exit_code, stderr):
    """XFAIL retains its A2 witness, but cannot hide bench faults or engine exit."""
    result["bench"] = bench_line(stderr)
    reasons = enqueue_reason_summaries(stderr)
    if reasons is not None:
        result["osc_enqueue_reasons"] = reasons
    if result["status"] not in ("passed", "xpass", "xfail"):
        return
    try:
        if exit_code != 0:
            raise Stop("engine_exit", f"shutdown exit={exit_code}")
        check_bench(result["bench"])
    except Stop as exc:
        result["status"] = "failed"
        result["first_failure"] = {"check": exc.check, "detail": exc.detail}


def source_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL, timeout=4).decode().strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unknown"


def check_previous(path, tier, source, profile, mode):
    previous_tier = list(TIERS)[list(TIERS).index(tier) - 1]
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (doc.get("status") != "passed" or doc.get("tier") != previous_tier or
            doc.get("source_sha") != source or doc.get("profile") != profile or
            doc.get("edit_mode") != mode):
        raise Stop("tier_prerequisite", f"passing same-SHA {previous_tier} needed")


def load_baseline(path, source, profile, mode):
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (doc.get("status") != "passed" or doc.get("tier") != "L0" or
            doc.get("source_sha") != source or doc.get("profile") != profile or
            doc.get("edit_mode") != mode or
            not isinstance(doc.get("p99_ms"), (float, int)) or doc["p99_ms"] <= 0):
        raise Stop("L0_baseline", "passing same-SHA L0 report with p99 required")
    return float(doc["p99_ms"])


def classify(edit_mode, e5, failure, a2_observation=None):
    if edit_mode != "config-edits" or e5:
        return ("failed", failure) if failure else ("passed", None)
    if failure is None:
        return "xpass", {"check": "A2_unexpected_pass",
                         "detail": "no measured pre-E5 edit-time disruption"}
    if (a2_observation is not None and failure["check"] in A2_FAILURES and
            a2_observation.get("fault") == failure):
        return "xfail", {"check": "A2_expected_failure",
                         "detail": str(failure),
                         "edit_id": a2_observation["edit_id"]}
    return "failed", failure


def reports(dest, result):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "report.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    failure = result.get("first_failure") or {}
    lines = ["<!-- SPDX-License-Identifier: GPL-3.0-only -->", "# I/O endurance — OB-g1/g2", "",
             f"- Status: {result['status']} (advisory, OB r2.4a)",
             f"- Source: {result['source_sha']}; engine: {result['engine_sha']}",
             f"- Profile/mode/tier: {result['profile']}/{result['edit_mode']}/{result['tier']}",
             f"- Duration: {result['elapsed_s']:.3f}s; tier {result['duration_s']}s",
             f"- First failure: {failure.get('check', 'none')}: {failure.get('detail', '')}",
             f"- Counters before: {json.dumps(result['counters_before'], sort_keys=True)}",
             f"- Counters after: {json.dumps(result['counters_after'], sort_keys=True)}",
             f"- OSC drop diagnostics (latest status; absent means unobserved): {json.dumps(result.get('osc_drop_diagnostics', {}), sort_keys=True)}",
             f"- RTT p99 ms: {result['p99_ms']}; L0 baseline ms: {result['l0_p99_ms']}",
             f"- RSS peak bytes: {result['rss_peak_bytes']}; bench: {result['bench']}",
             f"- Counter coverage: {result['counter_visibility']}",
             f"- Scripted MIDI received before/after: {result['midi_received_before']} / {result['midi_received_after']}",
             f"- Qualifying A2 edit observation: {json.dumps(result['a2_observation'], sort_keys=True)}", "",
             "## Last five seconds of events", "", "Events:",
             *result["events_last_5s"], "End events", ""]
    (dest / "report.md").write_text("\n".join(lines))


def run_tier(engine, profile, mode, tier, output, in_port, out_port, l0_path, previous, e5):
    source = source_sha()
    started = time.monotonic()
    watch = Watch()
    child = None
    result = {"schema_version": 1, "profile": profile, "edit_mode": mode, "tier": tier,
              "duration_s": TIERS[tier], "platform": platform.platform(), "source_sha": source,
              "engine_sha": "unknown", "advisory": True, "status": "blocked",
              "first_failure": None, "counters_before": {}, "counters_after": {},
              "counter_visibility": {}, "bench": None, "p99_ms": None, "l0_p99_ms": None,
              "osc_drop_diagnostics": {"routes": {}, "listeners": {}},
              "rss_peak_bytes": None, "events_last_5s": [], "elapsed_s": 0.0,
              "load_edits": 0, "messages_sent": 0, "messages_received": 0,
              "scripted_midi": profile in MIDI_PROFILES,
              "midi_received_before": None, "midi_received_after": None,
              "a2_observation": None}
    try:
        if not engine.is_file() or not os.access(engine, os.X_OK):
            raise Stop("engine_missing", f"executable unavailable: {engine}")
        if source == "unknown":
            raise Stop("source_unpinned", "run from pinned Git checkout")
        l0 = load_baseline(l0_path, source, profile, mode) if l0_path else None
        if tier != "L0":
            if l0 is None:
                raise Stop("L0_baseline", "--baseline-report required")
            if previous is None:
                raise Stop("tier_prerequisite", "--previous-report required")
            check_previous(previous, tier, source, profile, mode)
        result["l0_p99_ms"] = l0
        graph = patch(profile, in_port, out_port)
        with tempfile.TemporaryDirectory(prefix="wlab-ob-g1-") as temp, \
             socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as rx, \
             socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tx:
            rx.bind((HOST, out_port))
            rx.setblocking(False)
            tx.bind((HOST, 0))
            child = Sidecar(engine, Path(temp) / "settings.json", profile)
            if profile in MIDI_PROFILES:
                result["midi_received_before"] = midi_received({"midi": child.hello.get("midi", {})})
                result["midi_received_after"] = result["midi_received_before"]
            engine_sha = str(child.hello.get("engine", {}).get("sha", "unknown"))
            result["engine_sha"] = engine_sha
            if engine_sha != "unknown" and len(engine_sha) >= 7 and not source.startswith(engine_sha):
                raise Stop("engine_sha_mismatch", f"checkout={source} engine={engine_sha}")
            unprocessed = child.load(graph, 0)
            start = time.monotonic()
            next_seq = next_load = next_rss = start
            next_fall = None
            next_edit = start + 30
            # MIDI hello provides pre-load counts. Fresh OSC service stop
            # counters have a zero baseline, including before the first status.
            initial = (counters({"status": {"midi": child.hello.get("midi", {})}})
                       if profile in MIDI_PROFILES else {})
            rss_anchor = None
            rss_peak = 0
            load_count = 0
            last_rate = 10
            midi_last_progress = start
            while time.monotonic() - start < TIERS[tier]:
                now = time.monotonic()
                if child.proc.poll() is not None:
                    raise Stop("engine_exit", f"exit={child.proc.returncode}")
                if now >= next_seq:
                    for addr, val in (watch.send_seq(now), watch.send_gate(now, True)):
                        tx.sendto(encode(addr, val), (HOST, in_port))
                        result["messages_sent"] += 1
                    next_fall = now + .020
                    next_seq += .100
                    if now - next_seq > .100:
                        raise Stop("sender_overrun", "sentinel generator >100ms late")
                if next_fall is not None and now >= next_fall:
                    addr, val = watch.send_gate(now, False)
                    tx.sendto(encode(addr, val), (HOST, in_port))
                    result["messages_sent"] += 1
                    next_fall = None
                if profile in OSC_LOAD_PROFILES and now >= next_load:
                    rate = min(1600, 200 * (2 ** int((now - start) // 15))) \
                        if profile == "osc-stress" else 200
                    last_rate = rate
                    for i in range(64):
                        value = ((load_count + i * 17) % 97) / 96 \
                            if i % 2 == 0 else float((load_count + i) % 2)
                        tx.sendto(encode(f"/io/load/{i:02d}", value), (HOST, in_port))
                    result["messages_sent"] += 64
                    load_count += 1
                    next_load += 1 / rate
                    if now - next_load > .250:
                        raise Stop("sender_overrun", f"cannot sustain {rate} Hz per address")
                try:
                    while True:
                        packet, peer = rx.recvfrom(2048)
                        if peer[0] != HOST:
                            raise Stop("nonloopback_traffic", str(peer))
                        addr, value = decode(packet)
                        if addr in ("/io/echo", "/io/edge"):
                            watch.receive(time.monotonic(), addr, value)
                            result["messages_received"] += 1
                except BlockingIOError:
                    pass
                while unprocessed:
                    unprocessed.pop()
                while True:
                    try:
                        msg = child.messages.get_nowait()
                    except queue.Empty:
                        break
                    if msg.get("type") == "invalid_stdout":
                        raise Stop("malformed_sidecar", "invalid NDJSON")
                    if msg.get("type") == "status":
                        status = msg.get("status", {})
                        result["osc_drop_diagnostics"] = osc_drop_diagnostics(status)
                        osc = status.get("osc", {})
                        if osc.get("lan") is True or osc.get("bind") not in (None, HOST):
                            raise Stop("lan_forbidden", str(osc.get("bind")))
                        for route in osc.get("routes", []):
                            if route.get("state") not in ("listening", "lan-not-confirmed"):
                                raise Stop("osc_route_unavailable", str(route))
                        for route in osc.get("out", []):
                            if route.get("state") != "sending":
                                raise Stop("osc_out_unavailable", str(route))
                        current = counters(msg)
                        record_counters(result, initial, current)
                        if profile in MIDI_PROFILES:
                            received = midi_received(status)
                            if record_midi_received(result, received):
                                midi_last_progress = now
                                watch.note(now, f"midi received={received}")
                            if now - midi_last_progress > 2.0:
                                raise Stop("midi_stalled", "no scripted Host receives for >2s")
                if now >= next_rss:
                    mem = rss_bytes(child.proc.pid)
                    if mem is not None:
                        rss_peak = max(rss_peak, mem)
                        if now - start >= 600 and rss_anchor is None:
                            rss_anchor = (now, mem)
                        if rss_anchor and now - rss_anchor[0] >= 60:
                            growth = (mem - rss_anchor[1]) / (1024 * 1024) / \
                                     ((now - rss_anchor[0]) / 3600)
                            if growth > 8:
                                raise Stop("rss_growth", f"{growth:.3f} MiB/hour >8 after 10min")
                        result["rss_peak_bytes"] = rss_peak
                    next_rss = now + .100
                    if l0 is not None and len(watch.latencies_ms) >= 10:
                        p99 = percentile(watch.latencies_ms, 99)
                        if p99 > 2 * l0:
                            raise Stop("p99_regression", f"{p99:.3f} ms > 2x L0 {l0:.3f}ms")
                watch.check(now)
                if mode == "config-edits" and now >= next_edit:
                    result["load_edits"] += 1
                    watch.begin_edit(result["load_edits"], time.monotonic())
                    try:
                        unprocessed.extend(child.load(graph, result["load_edits"]))
                    finally:
                        watch.end_edit(time.monotonic())
                    next_edit += 30
                time.sleep(.0002)
            result["rate_hz_per_address"] = last_rate
            if profile in MIDI_PROFILES and result["midi_received_after"] <= result["midi_received_before"]:
                raise Stop("midi_stalled", "no scripted MIDI received during tier")
            until = time.monotonic() + .250
            while time.monotonic() < until and (watch.expected_seq or watch.expected_edges):
                try:
                    packet, peer = rx.recvfrom(2048)
                except BlockingIOError:
                    time.sleep(.001)
                    continue
                if peer[0] != HOST:
                    raise Stop("nonloopback_traffic", str(peer))
                addr, value = decode(packet)
                watch.receive(time.monotonic(), addr, value)
            watch.check(time.monotonic())
            if watch.expected_seq or watch.expected_edges:
                raise Stop("missing_echo", "pending seq/gate at boundary")
            result["status"], result["first_failure"] = classify(mode, e5, None)
    except (Stop, OSError, ValueError, queue.Empty, subprocess.TimeoutExpired) as exc:
        check = exc.check if isinstance(exc, Stop) else type(exc).__name__
        detail = exc.detail if isinstance(exc, Stop) else str(exc)
        failure = {"check": check, "detail": detail}
        observation = watch.attribute_fault(exc, time.monotonic()) if isinstance(exc, Stop) else None
        result["a2_observation"] = observation
        result["status"], result["first_failure"] = classify(
            mode, e5, failure, observation)
        if check in ("engine_missing", "source_unpinned", "L0_baseline", "tier_prerequisite"):
            result["status"] = "blocked"
    finally:
        if child:
            exit_code, stderr = child.close()
            apply_shutdown_checks(result, exit_code, stderr)
        result["elapsed_s"] = time.monotonic() - started
        result["p99_ms"] = percentile(watch.latencies_ms, 99)
        cutoff = time.monotonic() - 5
        result["events_last_5s"] = [f"{t:.6f} {event}" for t, event in watch.events if t >= cutoff]
        result["counter_visibility"] = {
            "available": sorted(result["counters_after"]),
            "unexposed_on_current_engine": ["osc.in.malformed", "osc.in.truncated"] +
                ([] if profile in MIDI_PROFILES else ["midi.counters (requires --scripted-midi)"])}
        reports(output / profile / mode / tier, result)
    return result


def self_test():
    found = []
    class Dead:
        returncode = 137
        def poll(self):
            return 137
    try:
        dead = Dead()
        if dead.poll() is not None:
            raise Stop("engine_exit", f"exit={dead.returncode}")
    except Stop as exc:
        assert exc.check == "engine_exit"
        found.append("engine_exit")
    lost = Watch()
    lost.send_seq(10)
    try:
        lost.check(10.3)
    except Stop as exc:
        assert exc.check == "missing_echo"
        found.append("missing_echo")
    stuck = Watch()
    stuck.send_gate(10, True)
    stuck.receive(10.002, "/io/edge", 1)
    stuck.send_gate(10.020, False)
    try:
        stuck.check(10.071)
    except Stop as exc:
        assert exc.check == "stuck_gate"
        found.append("stuck_gate")
    assert found == ["engine_exit", "missing_echo", "stuck_gate"]
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path)
    parser.add_argument("--profile", choices=PROFILES, default="osc-gates")
    parser.add_argument("--edit-mode", choices=("still", "config-edits"), default="still")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--tier", choices=TIERS, default="L0")
    choice.add_argument("--ladder", action="store_true")
    parser.add_argument("--baseline-report", type=Path)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--report-dir", type=Path, default=ROOT / "build_reports/io-soak")
    parser.add_argument("--port-in", type=int, default=9000)
    parser.add_argument("--port-out", type=int, default=9001)
    parser.add_argument("--e5-merged", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        print("SELF-TEST PASS: " + ", ".join(self_test()))
        return 0
    if args.engine is None:
        parser.error("--engine is required")
    if not (1 <= args.port_in <= 65535 and 1 <= args.port_out <= 65535
            and args.port_in != args.port_out):
        parser.error("ports must be distinct and 1..65535; host fixed to loopback")
    baseline_path, previous = args.baseline_report, args.previous_report
    for tier in (list(TIERS) if args.ladder else [args.tier]):
        result = run_tier(args.engine.resolve(), args.profile, args.edit_mode, tier,
                          args.report_dir, args.port_in, args.port_out, baseline_path,
                          previous, args.e5_merged)
        path = args.report_dir / args.profile / args.edit_mode / tier / "report.json"
        print(f"{tier} {result['status']}: {result['first_failure']} ({path})", flush=True)
        if result["status"] != "passed":
            return 0 if result["status"] == "xfail" else 1
        if tier == "L0":
            baseline_path = path
        previous = path
    return 0


if __name__ == "__main__":
    sys.exit(main())
