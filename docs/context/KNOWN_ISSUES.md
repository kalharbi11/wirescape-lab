<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Known issues at the snapshot

Numbers are issues/PRs in `kalharbi11/wirescape` (frozen). Open PRs there were not merged into the snapshot.

## Behaviour
- **A2: edits restart the patch.** Parameters are live events and add/remove module/cable is a live replan,
  but any module-config edit, undo/redo, snapshot restore, OSC In row edit or MIDI CC Learn sends a full
  `loadGraph`: mute, fade, every module restarts (phases, delay/reverb tails, envelopes, held notes,
  sequencer position). Groove: steps, length and tempo are config, Apply only works while stopped, playback
  restarts at step 1. Voice-count changes release held notes without warning.
- **MIDI to CV pitch/gate not reaching VCO/ADSR** on the owner's Windows patch (#724; draft PR #727 adds a regression test; the engine path passes in tests).
- **OSC Out phantom gate edge after panic reset** (#759; draft PR #763).
- **ASIO device list frozen while playing; driver switch** (#722; draft PR #758).
- **LAN-only OSC consent stays loopback without a warning** (#760; draft PR #762).
- From the first owner test session, not verified fixed: basics-04 silence after a short envelope with
  high VCA; scene-07 clicks after panic; Echo knob clicks; Groove start/stop lag.
- FlexASIO not listed on Windows (owner evidence pending).

## Not built yet
- Installer or packaged build (source only; PortAudio DLL supplied by the user on Windows).
- Web demo audio in an AudioWorklet. Stereo Output module. MIDI Out. OSC to the LAN.
- 60-minute Pi soak with scripted edits (#296). Benchmark regression gate (#91).
