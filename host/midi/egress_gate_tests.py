# SPDX-License-Identifier: GPL-3.0-only
"""OB-g9 #348: OSC gate edges survive 256+ routed MIDI release events.

Real null-audio sidecar, --scripted-midi, localhost OSC only; no devices.
Every routed module event is copied to the engine egress ring. The scripted
midi-m8 source emits 21.3 note events/s; once 256 releases sat undrained in the
critical egress ring (~12 s), each further release raised an engine emergency,
the graph generation moved, and OSC In (which pins its start generation) could
no longer enqueue: the soak saw `missing_gate_edge`. The control owner must
drain egress. Same 50 ms edge rule as bench/io/soak.py; nothing is relaxed.
"""
import socket
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bench" / "io"))
import soak  # noqa: E402

RUN_S = 16.0  # > 256 / 21.3 releases per second, with margin


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind((soak.HOST, 0))
        return probe.getsockname()[1]


def run(binary):
    port_in = free_port()
    port_out = free_port()
    while port_out == port_in:
        port_out = free_port()
    watch = soak.Watch()
    edges = 0
    with tempfile.TemporaryDirectory() as directory, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as rx, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tx:
        rx.bind((soak.HOST, port_out))
        rx.setblocking(False)
        tx.bind((soak.HOST, 0))
        child = soak.Sidecar(Path(binary), Path(directory) / "settings.json", "midi-m8")
        try:
            child.load(soak.patch("midi-m8", port_in, port_out), 0)
            start = time.monotonic()
            next_pulse = start + 0.5  # let OSC In/Out reach listening/sending
            fall = None
            while time.monotonic() - start < RUN_S:
                now = time.monotonic()
                if child.proc.poll() is not None:
                    raise AssertionError(f"sidecar exited {child.proc.returncode}")
                if now >= next_pulse:
                    tx.sendto(soak.encode(*watch.send_gate(now, True)), (soak.HOST, port_in))
                    fall = now + 0.020
                    next_pulse += 0.100
                if fall is not None and now >= fall:
                    tx.sendto(soak.encode(*watch.send_gate(now, False)), (soak.HOST, port_in))
                    fall = None
                try:
                    while True:
                        packet, _ = rx.recvfrom(2048)
                        address, value = soak.decode(packet)
                        if address == "/io/edge":
                            before = len(watch.expected_edges)
                            watch.receive(time.monotonic(), address, value)
                            edges += before - len(watch.expected_edges)
                except BlockingIOError:
                    pass
                try:
                    watch.check(time.monotonic())
                except soak.Stop as stop:
                    raise AssertionError(
                        f"{stop.check} {stop.detail} at {time.monotonic() - start:.2f}s "
                        f"after {edges} edges") from None
                time.sleep(0.0002)
        finally:
            code, stderr = child.close()
    assert code == 0, (code, stderr[-2000:])
    assert edges >= 2 * int((RUN_S - 1) * 10), edges
    print(f"PASS OB-g9 OSC gate edges across {RUN_S:.0f}s of scripted MIDI: {edges} edges, devices off")


if __name__ == "__main__":
    run(sys.argv[1])
