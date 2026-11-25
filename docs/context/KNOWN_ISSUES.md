<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Known issues at the snapshot

Numbers are issues/PRs in `kalharbi11/wirescape` (frozen). Open PRs there were not merged into the snapshot.

## Behaviour
- **A2: edit continuity has measured limits, rather than every edit restarting the patch.** In the device-off
  E4b capture at `8e8783b`, 19 accepted edit cases (including module/cable edits, modulation amount,
  CC map, and applyGraph identical, Groove steps/length, voice count, OSC In row, one parameter,
  deleted/restored module) had 282/282 unaffected witness windows sample-exact to matched controls;
  edit-induced silence, dip and slip were zero and jump ratio one
  ([measured rows](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md#m4-cn--e4ae4b-linux-x64-2026-11-24-a50)).
  These are command-level, not every UI gesture or config subject: the Groove subject restart
  assessment is unmeasured for steps/length in those rows, and they do not establish tempo,
  Apply-while-playing, undo/redo, snapshot restore or MIDI Learn UI behavior for every path.
  A deliberate full `loadGraph` remains distinct: the historical identical-load row had
  held-note silence about 1.02 s and subject restarted; this is a historical measurement,
  not a fresh candidate/device result ([historical table](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md#edit-continuity-t013b)).
- **OB1.1: allocation-policy changes may release held notes.** Count-only edits retain voices
  that fit (A55 / #439); changes to mode, mono priority, legato or channel filter still release
  and reconfigure the affected voice owner. The earlier E4b voice-count subject was not restarted
  but its affected held-note row differed in 3/3 repeats (12.479 ms paired silence);
  do not treat the 282 unaffected comparisons as proof that the edited voice never changes
  ([affected subject row](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md#intentionally-affected-subjects-and-limitations)).
- **A2 / larger buffer rebuild (A83):** at source `8c9bb10` on Linux x64 null sink,
  the 256→512 rule-2 restart had 18/18 post-bracket witness seconds sample-exact to control,
  `freshModules` [] in 3/3 repeats, retained Delay tail and held note (39,340 and 47,920 sounding
  samples per second), clock slip 0; the bracket is reported, not gated, under A83 within
  the caps: first mismatch no earlier than the edit block, disturbance 479/480 frames
  (9.979/10.0 ms at 48 kHz), at most one newly silent sample, worst paired dip −25.6322 dB
  and Slew jump 194,911.841; the smaller 256→128 row stays fully gated (15/15 exact),
  and the arm64 raw A62 row is unmeasured ([final measured rows](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md#final-delay-inclusive-capture-2026-11-25)).
  [A83](https://github.com/kalharbi11/wirescape-lab/issues/523#issuecomment-7157532240) — **Expiry:** OB1.1 close, or any change to the restart/mute path or `max_block` preparation. After that, the row is re-measured against acceptance 2 as written.
  **Overturned by:** a post-bracket difference, a failure of the smaller row, a span over the cap, or the owner hearing more than one restart click on the Pi.
  Real-device gap/listening remains unverified.
- **Historical intermediate larger-buffer non-pass:** source `5ca0f19` had Delay tail post
  sounding count 0 versus 39,341 in control (3/3 repeats), although held-note count was
  47,920/48,000 and `freshModules` []; this is the intermediate row, not the final
  Delay-inclusive capture ([intermediate measured rows](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md#intermediate-cn-capture-2026-11-25-not-the-final-delay-candidate)).
- **MIDI to CV pitch/gate not reaching VCO/ADSR** on the owner's Windows patch (#724; draft PR #727 adds a regression test; the engine path passes in tests).
- **OSC Out phantom gate edge after panic reset** (#759; source PR #763; ported to the lab).
- **ASIO device list frozen while playing; driver switch** (#722; draft PR #758).
- **LAN-only OSC consent stays loopback without a warning** (#760; source PR #762; ported to the lab).
- From the first owner test session, not verified fixed: basics-04 silence after a short envelope with
  high VCA; scene-07 clicks after panic; Echo knob clicks; Groove start/stop lag.
- **Linux: virtual MIDI inputs not listed — fixed in lab (#31).** The snapshot's libremidi observer
  used `track_virtual` off, so software ALSA sequencer ports (including "Wirescape Bench") were absent.
  The lab MIDI observer now enables `track_virtual`, matching the Pi quick run's temporary patch
  (`facts/device/results/pi5/2026-11-14-b1d92be-quick/source.patch`).
  Device-free fake-backend tests cover virtual-port listing, stable system identities and unplug/reconnect;
  live ALSA behaviour remains subject to the owner's next device-authorized run.
- **Buffer-size change gap:** in that run, `setBufferFrames` was followed by 546 ms of silence and panic by 306 ms
  (`review.json`, silence_gap_diagnostic_flags).
- FlexASIO not listed on Windows (owner evidence pending).

## Not built yet
- Installer or packaged build (source only; PortAudio DLL supplied by the user on Windows).
- Web demo audio in an AudioWorklet. Stereo Output module. MIDI Out. OSC to the LAN.
- 60-minute Pi soak with scripted edits (#296). Benchmark regression gate (#91).
