<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Essentials ADSR — experimental ABI 2

Offline engine2 port only; stable essentials.adsr identity, GPL-3.0-only. The ABI1 app still uses its original module. DSP: dsp.h; registration: module.cpp. Tests are maintained together in native/tests2/module_tests.cpp (reference, matrix, reset, scalar/no-exception builds) and integration_tests.cpp (graph/voice proof), rather than duplicated per module.

A connected nonzero-channel gate cable wins over all note events. Gates use >0.5 on / <0.25 off. With no cable, NOTE_ON/OFF track source_id/note_id per explicit voice channel; matching CHOKE clears even a release tail. Attack/decay/release times latch at segment start; sustain is sampled. No local held-note fallback: use the shared upstream allocator. Float envelope level and double/sample-count timing retain ABI1 reference behavior.

See [spec](../../../docs/specs/ABI2_SPEC.md) and [review](../../../docs/reviews/M1_FOUNDATION_SLICE_REVIEW.md) for evidence and limitations. No hardware/plugin adapter claim.

## OB-g5 triggered envelope (draft; S6-gated)

`mode` defaults to **Gate (0)**, preserving the original cable/event behavior and all old patch defaults. **Trigger (1)** runs one envelope cycle per rising gate edge or accepted NOTE_ON when no gate cable is connected. Each start uses the **current** envelope level, so overlapping notes do not force a zero-level reset. NOTE_OFF and falling cable gates do not end the Trigger cycle. After Attack and Decay, Sustain is held for `hold` seconds (0–30, default 0), then Release completes automatically. CHOKE for the matching no-cable voice and module reset retain the existing clear behavior. A connected gate cable still takes precedence over Notes events.

Standalone device-off regression runner (the shared native CMake targets remain unchanged during S6):

```sh
cmake -S native/modules2/adsr -B /tmp/adsr-ob-g5
cmake --build /tmp/adsr-ob-g5
ctest --test-dir /tmp/adsr-ob-g5 --output-on-failure
```

The module-local tests include an independent copy of the old Gate calculation and compare sample bits; they also check explicit Trigger attack/retrigger, zero/positive timed hold, release timing, NOTE_OFF immunity, and matching CHOKE/reset. This is a test recipe, **not a claim of a completed execution**.
