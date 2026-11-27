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

The device-free renderer accepts `noteOn`, `noteOff`, `gate`, `setParam`, and raw `midi` script entries. A MIDI entry supplies a target `node`, absolute `frame`, and `words` array of 1–4 unsigned 32-bit UMP words; the count must match the message-type nibble. OSC message injection remains unsupported. Issue #722 adds MIDI ingress; it does not by itself establish causal coverage for every MIDI module.

| Runtime ID | Reproduction / observation boundary |
| --- | --- |
| `midi.in` | Raw UMP ingress is available; a causal routed-output coverage case remains to be established |
| `midi.to_cv` | Renderer regression #722 checks sample-exact gate and bend conversion from raw UMP; broader coverage-suite contribution remains separate |
| `midi.cc_to_cv` | Raw UMP CC injection is available; a causal CC modulation coverage case remains to be established |
| `osc.in` | Input expects `WS2_MESSAGE` OSC bytes; offline script rejects `type: osc`, so a mapped control signal cannot be stimulated |
| `osc.out` | No audio or signal output; DSP writes an internal `OutBus` that the headless WAV renderer does not expose. Bundled `osc-out-01.json` includes it, but its output audio can be entirely independent of `osc.out` |
| `monitor` | No outputs; DSP writes capture observations to a `Tap`, not the audio renderer. Renderer exposes WAV and metering only, not tap samples |

For device-free MIDI injection, use an entry such as `{"frame":0,"node":1,"type":"midi","words":[546323556]}` (MIDI 1.0 note-on). The renderer regression exercises note-on/off and pitch bend. OSC injection and OSC-out/monitor bus or tap inspection remain separate gaps; zero-output descriptors cannot establish causal PCM contribution by themselves.

Current coverage facts distinguish unmeasured contribution, non-silent bundled patch *presence*, and a measured audio bypass intervention. There is no claim that the six modules above have passed the T0.11 contribution gate, or that unrelated background audio proves coverage.

Audio WAVs are job-local only; divergent samples and experiments can be uploaded by CI with short retention. No audio/MIDI device or LAN socket is opened.
