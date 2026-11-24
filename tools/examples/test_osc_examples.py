# SPDX-License-Identifier: GPL-3.0-only
"""Known-answer OSC encoding/receiver tests for W1 (stdlib only).

  python tools/examples/test_osc_examples.py
"""
from __future__ import annotations

import math
import socket
import struct
import unittest

from osc_in_sender import encode, require_loopback, sweep_value
from osc_loopback_check import inline_patch
from osc_out_receiver import decode


class OscExamplesTests(unittest.TestCase):
    def test_known_answer_float_half(self):
        packet = encode("/pico1/knob/1", 0.5)
        expected = b"/pico1/knob/1\x00\x00\x00" + b",f\x00\x00" + b"\x3f\x00\x00\x00"
        self.assertEqual(packet, expected)
        self.assertEqual(decode(packet), ("/pico1/knob/1", [0.5]))

    def test_float32_endpoints_and_round_trip(self):
        for value in (0.0, 0.125, 0.25, 0.75, 1.0):
            with self.subTest(value=value):
                address, arguments = decode(encode("/ws/row/1", value))
                self.assertEqual(address, "/ws/row/1")
                self.assertEqual(arguments, [struct.unpack(">f", struct.pack(">f", value))[0]])
                self.assertEqual(len(encode("/ws/row/1", value)) % 4, 0)

    def test_invalid_address_and_values(self):
        for address in ("", "/", "not/absolute", "/contains space", "/bad\0byte", "/résumé"):
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    encode(address, 0.5)
        for value in (-0.1, 1.1, math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    encode("/pico1/knob/1", value)

    def test_loopback_only(self):
        self.assertEqual(require_loopback("127.0.0.1"), "127.0.0.1")
        for host in ("0.0.0.0", "192.168.1.5", "localhost", "::1", "255.255.255.255"):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    require_loopback(host)

    def test_sender_to_actual_local_receiver(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as recv, \
             socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send:
            recv.bind(("127.0.0.1", 0))
            recv.settimeout(1)
            send.sendto(encode("/pico1/knob/1", 0.625), ("127.0.0.1", recv.getsockname()[1]))
            packet, peer = recv.recvfrom(512)
            self.assertEqual(peer[0], "127.0.0.1")
            self.assertEqual(decode(packet), ("/pico1/knob/1", [0.625]))

    def test_sweep_triangle(self):
        self.assertEqual([sweep_value(v, 2) for v in (0, 0.5, 1, 1.5, 2)],
                         [0.0, 0.5, 1.0, 0.5, 0.0])

    def test_inline_patch_is_native_v2_and_wired(self):
        patch = inline_patch()
        self.assertEqual((patch["format"], patch["version"]), ("wirescape.native.patch", 2))
        types = {m["id"]: m["module"] for m in patch["modules"]}
        self.assertEqual(types, {1: "osc.in", 2: "osc.out", 3: "essentials.output"})
        cable, = patch["connections"]
        self.assertEqual(cable["from"], {"module": 1, "port": "row1"})
        self.assertEqual(cable["to"], {"module": 2, "port": "row1"})
        self.assertEqual(patch["modules"][0]["config"]["port"], 9000)
        self.assertEqual(patch["modules"][1]["config"]["port"], 9001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
