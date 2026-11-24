<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Windows owner-evaluation patches
Load 01 and 02 in native Studio with a MIDI input enabled; 02 uses four rotating voices.
Load 03 for loopback OSC In UDP 9000 to OSC Out UDP 9001; 04 combines MIDI with OSC-controlled FM and exports LFO/envelope rows.
OSC Out only sends to 127.0.0.1; the browser cannot use UDP. Run device tests on the owner's Windows machine.
