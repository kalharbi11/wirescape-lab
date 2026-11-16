<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Deterministic coverage fixtures (T0.11)

These are device-free native patch-v2 JSON assets. The three top-level patches are included in the same-runner golden render when `--coverage-root head` is supplied to the head's measurement script for **both** base and head. Controls live under `controls/` and are never golden cases by themselves.

| Fixture | Target module | Observable path | Bypass intervention |
| --- | --- | --- | --- |
| `notes-to-cv.json` | `essentials.notes_to_cv` | Keyboard note events -> NotesToCV pitch -> VCO pitch -> Output audio | Disconnect NotesToCV pitch; VCO fixed at 220 Hz |
| `chord-notes.json` | `essentials.chord` | Keyboard note events -> Chord note events -> VCO note events -> Output audio | Direct Keyboard notes -> VCO notes |
| `spectral-cross.json` | `sound.spectral` | VCO plus seeded noise -> two Spectral inputs -> Output audio | Direct VCO -> Output audio |

For each case the renderer requires non-silent PCM (`rms_fs > 1e-8`) and a positive maximum absolute sample delta (`>1e-8 FS`) against the controlled bypass. It records both exact patch byte SHA-256s and the measured delta. If either is not measured, the golden job fails, never substituting unrelated background audio.

## Current offline instrumentation boundary

Current device-free `native/tools/render/main.cpp` accepts only `noteOn`, `noteOff`, `gate`, and `setParam` script entries. It cannot enqueue raw MIDI UMP or OSC message events. No product/renderer changes are permitted by issue #66.

| Runtime ID | Reproduction / observation boundary |
| --- | --- |
| `midi.in` | Module processes `WS2_MIDI` UMP events; renderer's event parser rejects `type: midi`, so no deterministic offline MIDI ingress to propagate to audio |
| `midi.to_cv` | Its `midi` input needs `WS2_MIDI`; renderer supports no such input event, so pitch/gate conversion cannot be causally observed |
| `midi.cc_to_cv` | Its `midi` input needs `WS2_MIDI` CC messages; renderer supports no raw UMP, so CC modulation is not exercised |
| `osc.in` | Input expects `WS2_MESSAGE` OSC bytes; offline script rejects `type: osc`, so a mapped control signal cannot be stimulated |
| `osc.out` | No audio or signal output; DSP writes an internal `OutBus` that the headless WAV renderer does not expose. Bundled `osc-out-01.json` includes it, but its output audio can be entirely independent of `osc.out` |
| `monitor` | No outputs; DSP writes capture observations to a `Tap`, not the audio renderer. Renderer exposes WAV and metering only, not tap samples |

To reproduce the missing script capability without opening devices, invoke the renderer with an otherwise valid coverage patch and a script containing an event of the unsupported type, e.g. `[{"frame":0,"node":1,"type":"midi"}]`; it returns `wirescape_render: unknown event type: midi`. Corresponding OSC events fail similarly. For `osc.out` and `monitor`, inspect the zero-output descriptor and compare WAVs with their disconnected instances: no causal PCM difference is expected. A future issue would need **test-only, device-free** raw event injection plus OSC-out/monitor bus/tap inspection, approved and implemented by Fable, to meet the remaining strict contribution criteria.

Current coverage facts distinguish unmeasured contribution, non-silent bundled patch *presence*, and a measured audio bypass intervention. There is no claim that the six modules above have passed the T0.11 contribution gate, or that unrelated background audio proves coverage.

Audio WAVs are job-local only; divergent samples and experiments can be uploaded by CI with short retention. No audio/MIDI device or LAN socket is opened.
