<!-- SPDX-License-Identifier: GPL-3.0-only -->
# OB-e1 module census — 2026-11-17 ET

Read-only source inventory; not a module-behavior acceptance claim. Lab source snapshot: `b2c3059d1d9502c98668ab6d85e0589777b68ec2` (GitHub source index); source files fetched from `main` on 2026-11-17, category: GitHub API source inspection, no device. Measured coverage provenance: engine/fixture `919f047b3c9f64eebbd04e0f3b072f5cb5f2049f`, CI Linux x64 Xeon 6975P, Linux ARM64 Neoverse-N2, Windows x64 AMD64; 2026-11-15.

**Count reconciliation:** The OB contract says 33; current generated Studio palette and presentation list **34** runtime IDs, as does `native/control/module_catalog.inc`. Two (`example.random_source`, `example.step_sequencer`) originate in `native/sdk/examples/`, leaving **32** `native/modules2/` registrations. Thus 33 does not match either current native directory count (32) or displayed palette count (34). All 34 actual palette IDs are retained rather than suppressing one. [Palette source](https://github.com/kalharbi11/wirescape-lab/blob/main/apps/studio/public/wirescape_modules.json) · [catalog](https://github.com/kalharbi11/wirescape-lab/blob/main/native/control/module_catalog.inc) · [portability classification](https://github.com/kalharbi11/wirescape-lab/blob/main/bench/portability/README.md).

`Yes` under palette means generated catalog membership only. Patch column identifies the cited historical source patch, `—` means no bundled source in that coverage row; coverage fixtures are not bundled patches. Test column describes the *specific existing evidence*, not OB-e2 every-module smoke acceptance. Source evidence is pinned in the T0.11 table, including descriptor paths and event-path test line links. Known-issue column uses the snapshot issue inventory; `none named` means no module-specific entry in that inventory, not defect-free.

| Runtime module | Palette | Bundled patch source | Test evidence | Known issue / limitation |
| --- | --- | --- | --- | --- |
| `essentials.adsr` | Yes | `basics-01-first-tone.json` | T0.11 measured pcm intervention | none named |
| `essentials.chaos_lite` | Yes | `basics-06-chaos-keys.json` | T0.11 measured pcm intervention | none named |
| `essentials.resonator` | Yes | `basics-05-random-melody.json` | T0.11 measured pcm intervention | none named |
| `essentials.clock` | Yes | `basics-04-sequencer-and-quantizer.json` | T0.11 measured pcm intervention | none named |
| `essentials.function_envelope` | Yes | `chaos-03-orbiting-iron-fx.json` | T0.11 measured pcm intervention | none named |
| `host.keyboard` | Yes | `basics-01-first-tone.json` | T0.11 measured pcm intervention | none named |
| `essentials.ladder` | Yes | `scene-01-hollow-chapel.json` | T0.11 measured pcm intervention | none named |
| `essentials.lfo` | Yes | `basics-02-fm-filter-lfo.json` | T0.11 measured pcm intervention | none named |
| `ports.macro_oscillator` | Yes | `basics-07-macro-keys.json` | T0.11 measured pcm intervention | none named |
| `midi.cc_to_cv` | Yes | — | R3 unit/protocol assertion; [abi2_midi_cc_to_cv_tests](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/native/modules2/midi_cc_to_cv/tests.cpp#L5-L24) | event-path only; no PCM contribution proof |
| `midi.in` | Yes | — | R3 unit/protocol assertion; [abi2_midi_in_tests](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/native/modules2/midi_in/tests.cpp#L5-L15) | virtual MIDI listing fixed in lab; owner live retest pending |
| `midi.to_cv` | Yes | — | R3 unit/protocol assertion; [abi2_midi_to_cv_tests](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/native/modules2/midi_to_cv/tests.cpp#L18-L27) | owner Windows pitch/gate #724 |
| `essentials.mixer` | Yes | `scene-01-hollow-chapel.json` | T0.11 measured pcm intervention | none named |
| `essentials.noise` | Yes | `basics-05-random-melody.json` | T0.11 measured pcm intervention | none named |
| `essentials.output` | Yes | `basics-01-first-tone.json` | T0.11 measured pcm intervention | buffer-change silence gap (engine-level) |
| `essentials.scale_offset` | Yes | `basics-08-clocked-groove.json` | T0.11 measured pcm intervention | none named |
| `essentials.slew` | Yes | `scene-02-breathing-walls.json` | T0.11 measured pcm intervention | none named |
| `essentials.quad_vca` | Yes | `quad-vca-01-lpg-plucks.json` | T0.11 measured pcm intervention | none named |
| `essentials.vca` | Yes | `basics-01-first-tone.json` | T0.11 measured pcm intervention | basics-04 silence with high VCA (unverified) |
| `essentials.vcf` | Yes | `basics-02-fm-filter-lfo.json` | T0.11 measured pcm intervention | none named |
| `essentials.vco` | Yes | `basics-01-first-tone.json` | T0.11 measured pcm intervention | none named |
| `example.random_source` | Yes | `basics-05-random-melody.json` | T0.11 measured pcm intervention | none named |
| `example.step_sequencer` | Yes | `basics-04-sequencer-and-quantizer.json` | T0.11 measured pcm intervention | none named |
| `sound.blend` | Yes | `scene-06-dust-reactor.json` | T0.11 measured pcm intervention | none named |
| `sound.spectral` | Yes | — | T0.11 measured audio bypass intervention | none named |
| `fx.delay` | Yes | `basics-03-echo-and-reverb.json` | T0.11 measured pcm intervention | Echo knob clicks |
| `fx.reverb` | Yes | `basics-03-echo-and-reverb.json` | T0.11 measured pcm intervention | none named |
| `sequencing.groove` | Yes | `basics-08-clocked-groove.json` | T0.11 measured pcm intervention | start/stop lag; Apply while stopped |
| `essentials.quantizer` | Yes | `basics-04-sequencer-and-quantizer.json` | T0.11 measured pcm intervention | none named |
| `osc.in` | Yes | — | R3 unit/protocol assertion; [abi2_osc_in_tests](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/native/modules2/osc_in/tests.cpp#L68-L95) | LAN consent #760; OSC row edits reload |
| `osc.out` | Yes | `osc-out-01.json` | bundled presence unverified; [abi2_osc_out_tests](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/native/modules2/osc_out/tests.cpp#L127-L149) | panic phantom gate #759 |
| `monitor` | Yes | — | R3 unit/protocol assertion; [abi2_monitor_tests](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/native/modules2/monitor/tests.cpp#L25-L38) | event-path only; no PCM contribution proof |
| `essentials.chord` | Yes | — | T0.11 measured audio bypass intervention | none named |
| `essentials.notes_to_cv` | Yes | — | T0.11 measured audio bypass intervention | none named |

Sources (pinned measurement and tests): [T0.11 34-row inventory at source revision 919f047](https://github.com/kalharbi11/wirescape-lab/blob/919f047b3c9f64eebbd04e0f3b072f5cb5f2049f/facts/dsp/coverage/README.md) (measurement facts may have been published later; see [current facts](https://github.com/kalharbi11/wirescape-lab/blob/main/facts/dsp/coverage/README.md)); [known-issue snapshot](https://github.com/kalharbi11/wirescape-lab/blob/main/docs/context/KNOWN_ISSUES.md); [generated palette](https://github.com/kalharbi11/wirescape-lab/blob/main/apps/studio/public/wirescape_modules.json). Six event-path modules have no verified PCM contribution; their direct unit/protocol assertions are separate evidence. No new test, render, or device observation was performed.
