<!-- SPDX-License-Identifier: GPL-3.0-only -->
# T0.11 golden contribution facts

Source engine commit: 919f047b3c9f64eebbd04e0f3b072f5cb5f2049f
Fixture source commit: 919f047b3c9f64eebbd04e0f3b072f5cb5f2049f
Date (New York): 2026-11-15
Workflow: [Golden patch renders run 43785858733](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733)

| Machine | Runner CPU | Artifacts | Observed module interventions | Golden primary patches |
| --- | --- | --- | ---: | ---: |
| linux-x64 | Intel(R) Xeon(R) 6975P-C | [golden-diagnostics-linux-x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733/artifacts/14189794411) (ID 14189794411) | 28/34 | 24 bundled + 3 coverage |
| linux-arm64 | Neoverse-N2 | [golden-diagnostics-linux-arm64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733/artifacts/14190537461) (ID 14190537461) | 28/34 | 24 bundled + 3 coverage |
| windows-x64 | AMD64 Family 25 Model 1 Stepping 1, AuthenticAMD | [golden-diagnostics-windows-x64](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733/artifacts/14191115448) (ID 14191115448) | 28/34 | 24 bundled + 3 coverage |

Three machine-specific raw coverage JSON files:
- [linux-x64 measured inventory](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733/artifacts/14189794411) — facts/dsp/coverage/ci-linux-x64-modules-2026-11-15.json
- [linux-arm64 measured inventory](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733/artifacts/14190537461) — facts/dsp/coverage/ci-linux-arm64-modules-2026-11-15.json
- [windows-x64 measured inventory](https://github.com/kalharbi11/wirescape-lab/actions/runs/43785858733/artifacts/14191115448) — facts/dsp/coverage/ci-windows-x64-modules-2026-11-15.json

The `.json` inventories record source code path, bundled patch presence and each connected source-port/destination-port pair; exact input fixture/control SHA-256, observed output RMS/peak, and maximum absolute PCM delta for tested modules. All six unverified records remain explicitly unverified. The WAV files were not committed.

| Module ID | Descriptor source | Measured source patch | Status | x64 output RMS FS | x64 peak delta FS | ARM64 peak delta FS | Windows peak delta FS |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| essentials.adsr | native/modules2/adsr/dsp.h | bundled/basics-01-first-tone.json | measured_pcm_intervention | 0.068651 | 0.880000 | 0.880000 | 0.880000 |
| essentials.chaos_lite | native/modules2/chaos_lite/dsp.h | bundled/basics-06-chaos-keys.json | measured_pcm_intervention | 0.077237 | 0.303905 | 0.303905 | 0.303905 |
| essentials.chord | native/modules2/chord/dsp.h | coverage/chord-notes.json | measured_audio_bypass_intervention | 0.707111 | 1.999996 | 1.999996 | 1.999996 |
| essentials.clock | native/modules2/clock/dsp.h | bundled/basics-04-sequencer-and-quantizer.json | measured_pcm_intervention | 0.182418 | 0.541587 | 0.541587 | 0.541587 |
| essentials.function_envelope | native/modules2/function_envelope/dsp.h | bundled/chaos-03-orbiting-iron-fx.json | measured_pcm_intervention | 0.018286 | 0.108853 | 0.108853 | 0.108853 |
| essentials.ladder | native/modules2/ladder/dsp.h | bundled/scene-01-hollow-chapel.json | measured_pcm_intervention | 0.230289 | 0.657442 | 0.657442 | 0.657443 |
| essentials.lfo | native/modules2/lfo/dsp.h | bundled/basics-02-fm-filter-lfo.json | measured_pcm_intervention | 0.048644 | 0.179406 | 0.179406 | 0.179406 |
| essentials.mixer | native/modules2/mixer/dsp.h | bundled/scene-01-hollow-chapel.json | measured_pcm_intervention | 0.230289 | 0.657442 | 0.657442 | 0.657443 |
| essentials.noise | native/modules2/noise/dsp.h | bundled/basics-05-random-melody.json | measured_pcm_intervention | 0.042236 | 0.585123 | 0.585123 | 0.585123 |
| essentials.notes_to_cv | native/modules2/notes_to_cv/dsp.h | coverage/notes-to-cv.json | measured_audio_bypass_intervention | 0.707107 | 1.999999 | 1.999999 | 1.999999 |
| essentials.output | native/modules2/output/dsp.h | bundled/basics-01-first-tone.json | measured_pcm_intervention | 0.068651 | 0.219970 | 0.219970 | 0.219970 |
| essentials.quad_vca | native/modules2/quad_vca/dsp.h | bundled/quad-vca-01-lpg-plucks.json | measured_pcm_intervention | 0.055448 | 0.568376 | 0.568376 | 0.568376 |
| essentials.quantizer | native/modules2/quantizer/dsp.h | bundled/basics-04-sequencer-and-quantizer.json | measured_pcm_intervention | 0.182418 | 1.031441 | 1.031441 | 1.031441 |
| essentials.resonator | native/modules2/resonator/dsp.h | bundled/basics-05-random-melody.json | measured_pcm_intervention | 0.042236 | 0.585123 | 0.585123 | 0.585123 |
| essentials.scale_offset | native/modules2/scale_offset/dsp.h | bundled/basics-08-clocked-groove.json | measured_pcm_intervention | 0.126735 | 0.471799 | 0.471799 | 0.471799 |
| essentials.slew | native/modules2/slew/dsp.h | bundled/scene-02-breathing-walls.json | measured_pcm_intervention | 0.090216 | 0.182698 | 0.182698 | 0.182698 |
| essentials.vca | native/modules2/vca/dsp.h | bundled/basics-01-first-tone.json | measured_pcm_intervention | 0.068651 | 0.219970 | 0.219970 | 0.219970 |
| essentials.vcf | native/modules2/vcf/dsp.h | bundled/basics-02-fm-filter-lfo.json | measured_pcm_intervention | 0.048644 | 0.201662 | 0.201662 | 0.201662 |
| essentials.vco | native/modules2/vco/dsp.h | bundled/basics-01-first-tone.json | measured_pcm_intervention | 0.068651 | 0.219970 | 0.219970 | 0.219970 |
| example.random_source | native/sdk/examples/random_source/dsp.h | bundled/basics-05-random-melody.json | measured_pcm_intervention | 0.042236 | 0.415222 | 0.415222 | 0.415222 |
| example.step_sequencer | native/sdk/examples/step_sequencer/dsp.h | bundled/basics-04-sequencer-and-quantizer.json | measured_pcm_intervention | 0.182418 | 0.541587 | 0.541587 | 0.541587 |
| fx.delay | native/modules2/delay/dsp.h | bundled/basics-03-echo-and-reverb.json | measured_pcm_intervention | 0.024339 | 0.255844 | 0.255844 | 0.255844 |
| fx.reverb | native/modules2/reverb/dsp.h | bundled/basics-03-echo-and-reverb.json | measured_pcm_intervention | 0.024339 | 0.255844 | 0.255844 | 0.255844 |
| host.keyboard | native/modules2/host_keyboard/dsp.h | bundled/basics-01-first-tone.json | measured_pcm_intervention | 0.068651 | 0.219970 | 0.219970 | 0.219970 |
| midi.cc_to_cv | native/modules2/midi_cc_to_cv/dsp.h | - | not_exercised_offline | — | — | — | — |
| midi.in | native/modules2/midi_in/dsp.h | - | not_exercised_offline | — | — | — | — |
| midi.to_cv | native/modules2/midi_to_cv/dsp.h | - | not_exercised_offline | — | — | — | — |
| monitor | native/modules2/monitor/dsp.h | - | not_exercised_offline | — | — | — | — |
| osc.in | native/modules2/osc_in/dsp.h | - | not_exercised_offline | — | — | — | — |
| osc.out | native/modules2/osc_out/dsp.h | bundled/osc-out-01.json | bundled_presence_unverified | — | — | — | — |
| ports.macro_oscillator | native/modules2/macro_oscillator/dsp.h | bundled/basics-07-macro-keys.json | measured_pcm_intervention | 0.065050 | 0.268737 | 0.268737 | 0.268737 |
| sequencing.groove | native/modules2/groove/dsp.h | bundled/basics-08-clocked-groove.json | measured_pcm_intervention | 0.126735 | 0.471799 | 0.471799 | 0.471799 |
| sound.blend | native/modules2/blend/dsp.h | bundled/scene-06-dust-reactor.json | measured_pcm_intervention | 0.095481 | 0.395619 | 0.395619 | 0.395619 |
| sound.spectral | native/modules2/spectral/dsp.h | coverage/spectral-cross.json | measured_audio_bypass_intervention | 0.043303 | 1.066022 | 1.066022 | 1.066023 |

Unverified module IDs (current WAV-only renderer input/output contract): `midi.in`, `midi.to_cv`, `midi.cc_to_cv`, `osc.in`, `osc.out`, `monitor`. The first four have no injected raw MIDI/OSC payload in the device-free renderer; the last two have no PCM output port (outbound bus/capture tap observations not exposed). The recorded status is not contribution coverage.
