# SPDX-License-Identifier: GPL-3.0-only
"""Send an OSC 1.0 float32 message or a 50 Hz 0->1->0 sweep to OSC In.

  python tools/examples/osc_in_sender.py /pico1/knob/1 0.5
  python tools/examples/osc_in_sender.py /pico1/knob/1 --sweep 4

Localhost only. Standard-library Python; no third-party dependencies.
"""
from __future__ import annotations

import argparse
import math
import socket
import struct
import sys
import time

LOOPBACK = "127.0.0.1"
DEFAULT_PORT = 9000
SWEEP_HZ = 50


def require_loopback(host: str) -> str:
    if host != LOOPBACK:
        raise ValueError("--host must be 127.0.0.1 (loopback only)")
    return host


def encode(address: str, value: float) -> bytes:
    """Encode one non-bundle OSC 1.0 ',f' message."""
    if not address.startswith("/") or address == "/" or any(c.isspace() for c in address):
        raise ValueError("OSC address must be a non-empty path starting with /")
    try:
        path = address.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("OSC address must be ASCII") from exc
    if b"\0" in path or any(c < 0x20 or c > 0x7e for c in path):
        raise ValueError("OSC address must contain printable ASCII without NUL")
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("OSC In CV value must be finite and between 0 and 1")

    def osc_string(data: bytes) -> bytes:
        terminated = data + b"\0"
        return terminated + b"\0" * (-len(terminated) % 4)

    return osc_string(path) + osc_string(b",f") + struct.pack(">f", value)


def sweep_value(elapsed: float, duration: float) -> float:
    """Triangle ramp beginning and ending at zero, with peak halfway."""
    phase = min(1.0, max(0.0, elapsed / duration))
    return 1.0 - abs(2.0 * phase - 1.0)


def run(address: str, value: float | None, sweep: float | None, port: int, host: str) -> int:
    require_loopback(host)
    if not 1 <= port <= 65535:
        raise ValueError("--port must be 1..65535")
    if sweep is not None and (not math.isfinite(sweep) or sweep <= 0):
        raise ValueError("--sweep must be finite and greater than zero")
    if sweep is None and value is None:
        raise ValueError("provide a VALUE or --sweep SECONDS")
    encode(address, 0.0 if sweep is not None else value)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        if sweep is None:
            sock.sendto(encode(address, value), (host, port))
            print(f"sent {address} {value:.6f} -> {host}:{port}")
            return 0
        start = time.monotonic()
        n = 0
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= sweep:
                sock.sendto(encode(address, 0.0), (host, port))
                n += 1
                break
            sock.sendto(encode(address, sweep_value(elapsed, sweep)), (host, port))
            n += 1
            next_tick = start + n / SWEEP_HZ
            time.sleep(max(0.0, min(start + sweep, next_tick) - time.monotonic()))
        print(f"sent {n} {address} messages (0->1->0, {SWEEP_HZ} Hz) -> {host}:{port}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("address", help="OSC input address, e.g. /pico1/knob/1")
    parser.add_argument("value", type=float, nargs="?", help="CV value in 0..1")
    parser.add_argument("--sweep", type=float, metavar="SECONDS", help="triangle ramp at 50 Hz")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP port (default 9000)")
    parser.add_argument("--host", default=LOOPBACK, help="must be 127.0.0.1 (loopback only)")
    opts = parser.parse_args(argv)
    try:
        return run(opts.address, opts.value, opts.sweep, opts.port, opts.host)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
