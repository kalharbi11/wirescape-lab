<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S8 — module parameters for the run-2 batch (scout, facts only)

Lab commit: `337d8e8`. Sonnet scout for the Claude Architect, 2026-11-26. Facts only.

Flag key (`sdk/include/wirescape/module2.h:27`): MOD = `WS2_MODULATABLE`, STEP = `WS2_STEPPED`, AUTO = `WS2_AUTOMATABLE`, PV = `WS2_PER_VOICE`, AR = `WS2_AUDIO_RATE_OK`. Sources are under `modules/<id>/`. Engine facts: a STEPPED param jumps to its target instead of smoothing (`engine/render.cpp:528`); `engine/tests/port_behavior_tests.cpp:50,75` assert, for the modules listed there (adsr, lfo, vca, vcf, vco), that every non-STEPPED param is MOD and every STEPPED param is not MOD. `ws::param(...)` last args `4, 1` = slot kind/stepped marker as written in source.

## chord
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | enable1 | Enable 1 | 0..1 | 1 | STEP, AUTO | no: read per note-on, `chord/dsp.h:141` | chord/dsp.h:24 |
| 1 | shift1 | Shift 1 | -24..24 st | 4 | STEP, AUTO | no: clamped transposition per note-on, `dsp.h:142` | chord/dsp.h:25 |
| 2 | enable2 | Enable 2 | 0..1 | 1 | STEP, AUTO | no (same loop) | chord/dsp.h:26 |
| 3 | shift2 | Shift 2 | -24..24 st | 7 | STEP, AUTO | no | chord/dsp.h:27 |
| 4 | enable3 | Enable 3 | 0..1 | 0 | STEP, AUTO | no | chord/dsp.h:28 |
| 5 | shift3 | Shift 3 | -24..24 st | 12 | STEP, AUTO | no | chord/dsp.h:29 |
| 6 | enable4 | Enable 4 | 0..1 | 0 | STEP, AUTO | no | chord/dsp.h:30 |
| 7 | shift4 | Shift 4 | -24..24 st | -12 | STEP, AUTO | no | chord/dsp.h:31 |
- All 8 params share `kStepped = WS2_STEPPED | WS2_AUTOMATABLE` (`dsp.h:22`); none is MOD. Values are read with `b.param(i).value(0, e.offset)` at each incoming note-on event offset (`dsp.h:141-142`), not once per block.
- Fixed output capacity: `int keys[kNotes]` (root + 4) in `note_on` (`dsp.h:137`); the enables choose which of the 4 slots emit, they do not size anything.

## cv_to_notes
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | legato | Legato | 0..1 | 0 | STEP, AUTO | no: tested `>= .5` per sample at note decision, `cv_to_notes/dsp.h:103` | cv_to_notes/dsp.h:25 |
- Only parameter. Inputs pitch (WS2_PITCH), gate, velocity (poly); output `notes` event. Experimental per `module.json` description.

## groove
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | run | Start | 0..1 | 0 | STEP, AUTO | no: edge-detected control, `groove/dsp.h:342-346` | groove/dsp.h:43 |
| 1 | stop | Stop | 0..1 | 0 | STEP, AUTO | no (edge) | groove/dsp.h:44 |
| 2 | reset | Reset | 0..1 | 0 | STEP, AUTO | no (edge) | groove/dsp.h:45 |
| 3 | mute | Mute | 0..1 | 0 | STEP, AUTO | no | groove/dsp.h:46 |
| 4 | t1_run | T1 Start | 0..1 | 0 | STEP, AUTO | no (edge) | groove/dsp.h:47 |
| 5 | t1_stop | T1 Stop | 0..1 | 0 | STEP, AUTO | no (edge) | groove/dsp.h:48 |
| 6 | t1_mute | T1 Mute | 0..1 | 0 | STEP, AUTO | no | groove/dsp.h:49 |
| 7 | t2_run | T2 Start | 0..1 | 0 | STEP, AUTO | no (edge) | groove/dsp.h:50 |
| 8 | t2_stop | T2 Stop | 0..1 | 0 | STEP, AUTO | no (edge) | groove/dsp.h:51 |
| 9 | t2_mute | T2 Mute | 0..1 | 0 | STEP, AUTO | no | groove/dsp.h:52 |
- All 10 params are transport-like switches; none is MOD. Step data, loop bounds and per-track `div` live in the pattern (`pattern.tracks[t].div`, `dsp.h:338`), not in params; `module.json` has no pattern entry.
- Existing sample-and-hold: `module.json` description "two sample-and-hold modulation lanes"; outputs `t1_mod1/t1_mod2/t2_mod1/t2_mod2`. Inputs: `clock`, `run`, `reset` (signal). Per-track clock divider exists as pattern data `div` (`dsp.h:338,340`), not a param.

## host_keyboard
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | voices | Voices | 1..16 | 8 | STEP, AUTO | yes: voice count, `host_keyboard/dsp.h:98` and `change_configuration` at `dsp.h:100`; output channel count set from `core.allocator().voice_count()` at `dsp.h:140` | host_keyboard/dsp.h:13 |
| 1 | mode | Mode | 0..3 | 0 | STEP, AUTO | yes: allocator policy (`policy` clamp 0..3), `dsp.h:99-100` | host_keyboard/dsp.h:14 |
| 2 | octave | Octave | -3..3 | 0 | STEP, AUTO | no: added to pitch output, `dsp.h:145` | host_keyboard/dsp.h:15 |
- `module.json` is one line (`id` host.keyboard) with no description; outputs pitch/gate/velocity/notes. No inputs.
- `dsp.h:135` checks `b.param(0).constant() && b.param(1).constant()` to decide whether config can change inside a block, so the code already anticipates non-constant values for params 0 and 1.

## midi_in
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | channel_filter | Channel (0 = Omni) | 0..16 | 0 | STEP, AUTO | yes (filter): value clamped 0..16 at `midi_in/dsp.h:27`; a change emits NOTE_CHOKE for known sources (`dsp.h:29`) | midi_in/dsp.h:10 |
- Only parameter. No inputs; output `midi` event. A filter change chokes held notes.

## midi_to_cv
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | voice_count | Voices | 1..16 | 4 | STEP, AUTO | yes: `wanted.max_voices`, `midi_to_cv/dsp.h:74`; `core.resize(...)` at `dsp.h:82` | midi_to_cv/dsp.h:21 |
| 1 | allocation_mode | Mode (rotate/reuse/reset/mono) | 0..3 | 0 | STEP, AUTO | yes: `wanted.mode`, `dsp.h:75`; a mode change rebuilds the allocator (`dsp.h:78-93`) | midi_to_cv/dsp.h:22 |
| 2 | steal_policy | Steal (oldest) | 0..0 | 0 | STEP, AUTO | no: range is a single value; no `b.param(2)` read found in dsp.h | midi_to_cv/dsp.h:23 |
| 3 | mono_priority | Priority (last/low/high) | 0..2 | 0 | STEP, AUTO | yes: `wanted.mono_priority`, `dsp.h:76`; part of the reconfigure test at `dsp.h:78` | midi_to_cv/dsp.h:24 |
| 4 | legato | Legato | 0..1 | 0 | STEP, AUTO | yes: `wanted.legato`, `dsp.h:76`; part of the reconfigure test | midi_to_cv/dsp.h:25 |
| 5 | sustain | Sustain (ignore/hold) | 0..1 | 1 | STEP, AUTO (slot 6) | no: `hold` flag, `dsp.h:95` | midi_to_cv/dsp.h:26 |
| 6 | pitch_bend_range_semitones | Bend range | 0..48 st | 2 | STEP, AUTO (slot 7) | no: scales bend per sample, `dsp.h:117` | midi_to_cv/dsp.h:27 |
| 7 | apply_bend | Apply bend to pitch | 0..1 | 1 | STEP, AUTO (slot 8) | no: per sample, `dsp.h:117` | midi_to_cv/dsp.h:28 |
| 8 | channel_filter | Channel (0 = Omni) | 0..16 | 0 | STEP, AUTO (slot 9) | yes (filter): `requested_filter`, `dsp.h:77`, applied at `dsp.h:93` | midi_to_cv/dsp.h:29 |
- All 9 use local `stepped = WS2_STEPPED | WS2_AUTOMATABLE` (`dsp.h:19`); none is MOD. `param(5..7)` are read with `value(0, i)` per sample; the rest only at `value(0, 0)` (first sample of block).
- Outputs: pitch, gate, velocity, aftertouch, pressure, bend, mod, notes, last_note, trig. Input: `midi` event.

## notes_to_cv
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | voices | Voices | 1..16 | 4 | STEP, AUTO | yes: `cfg.max_voices`, `notes_to_cv/dsp.h:38-42`; `core.resize` at `dsp.h:46` (two paths: `dsp.h:38` and `dsp.h:102`) | notes_to_cv/dsp.h:21 |
- Only parameter. Mode is fixed `Rotate` (`dsp.h:41`). Outputs pitch, gate, velocity, trig; input `notes` event.

## quantizer
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | scale | Scale | 0..13 (13 = `kCustom`) | 1 | STEP, AUTO | no: selects a mask table, `quantizer/dsp.h:163,33` | quantizer/dsp.h:23 |
| 1 | root | Root | 0..11 | 0 | STEP, AUTO | no | quantizer/dsp.h:23 |
| 2 | shift | Shift | -7..7 | 0 | STEP, AUTO | no: `cfg.shift`, `dsp.h:164` | quantizer/dsp.h:24 |
| 3 | octave | Octave | -3..3 | 0 | STEP, AUTO | no: `cfg.octave`, `dsp.h:165` | quantizer/dsp.h:24 |
| 4-15 | n0..n11 | C..B (custom note on/off) | 0..1 each | C,D,E,F,G,A,B=1; others 0 | STEP, AUTO | no: bits of a custom mask, `dsp.h:169` | quantizer/dsp.h:25-30 |
- All 16 built by `stepped()` helper (`dsp.h:11-13`); none is MOD. Values read once per block via `param(i, lo, hi)` (`dsp.h:160-169`, `b.param(i).value(0, 0)`).
- Inputs pitch, trigger (poly); outputs pitch, changed. Description says it has sample-and-hold via the trigger input.

## function_envelope
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | rise | Rise | 0.0001..30 s | 0.01 | MOD, AUTO, PV, AR (`port_flags`) | no: sets stage length in samples per gate edge, `function_envelope/dsp.h:11` | function_envelope/dsp.h:8 |
| 1 | fall | Fall | 0.0001..30 s | 0.1 | port_flags | no | function_envelope/dsp.h:8 |
| 2 | curve | Curve | -1..1 | 0 | port_flags | no | function_envelope/dsp.h:8 |
- No trigger/gate-mode parameter and no delay parameter exist today. Shape is gated AR: gate rising edge starts rise, falling edge starts fall (`dsp.h`, `if(high!=v.high)`); gate threshold `>= .5`. One input (`gate`), one output (`envelope`, WS2_CV_UNI), 16 voices.
- Rise/fall are latched into the stage at the gate edge (`length = llround(seconds*rate)`); curve is latched too (`latched_curve`). Saved state validates length up to 11520000 samples (`load_state`).
- `module.json` says "Single-channel gated AR function generator"; code processes `b.channels()` channels (per-voice).

## lfo
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | rate | Rate | 0.01..20 Hz, linear | 1 | MOD, PV, AR, AUTO | no | lfo/dsp.h:12 |
| 1 | depth | Depth | 0..1 | 1 | MOD, PV, AR, AUTO | no | lfo/dsp.h:13 |
| 2 | offset | Offset | -1..1 | 0 | MOD, PV, AR, AUTO | no | lfo/dsp.h:14 |
| 3 | sync | Tempo sync | 0..1 | 0 | STEP only (no AUTO, no MOD) | no: selects free-run vs transport phase per sample, `dsp.h:27,35` | lfo/dsp.h:15 |
| 4 | beats | Beats/cycle | 0.125..16, log | 1 | AUTO, MOD (no PV, no AR) | no | lfo/dsp.h:16 |
- Single shape: `std::sin(phase)` (`dsp.h:32`); no shape parameter. No inputs (`inputs` is an empty array, `dsp.h:9`); so no reset or sync input. Outputs: `control` (CV_BI, sin*depth+offset) and `phase` (CV_UNI, 0..<1).
- Sync mode derives phase from `b.transport()->beat` divided by `beats` (`dsp.h:28-30`); it does not use the `rate` param. 16-voice phase array of doubles.

## clock
| # | id | name | range / options | default | flags | sets allocation or structure? | source |
|---|---|---|---|---|---|---|---|
| 0 | bpm | BPM | 20..300 | 120 | MOD, AUTO, PV, AR (`port_flags`) | no: smoothed with a 5 ms `PortRamp`, `port_state.h:17-18` | clock/dsp.h:9 |
| 1 | ticks_per_beat | Ticks per beat | 1..24 | 1 | port_flags | no: rounded `floor(x+.5)` when value changes (`clock/dsp.h:14`) | clock/dsp.h:9 |
| 2 | duty | Duty | 0.01..0.99 | 0.5 | port_flags | no | clock/dsp.h:9 |
| 3 | run | Run | 0..1 | 1 | port_flags (MOD) | no: tested `>= .5` | clock/dsp.h:9 |
| 4 | sync | Sync | 0..1 | 0 | STEP, AUTO | no: mode chosen once per block from `value(c,0)`, `dsp.h:12-13` | clock/dsp.h:9 |
- One output `clock` (WS2_GATE pulse train, phase < duty). One input `reset` (gate; rising edge sets phase 0). There is no divided or multiplied output: multiplication is `ticks_per_beat` (1..24 integer, applied to the phase increment); division below 1 tick per beat does not exist in the range.
- Sync mode (`process_synced`): phase = frac((transport.beat + i*step) * ticks); output 0 when transport not playing or run < .5; `bpm` is ignored for the phase (it is still ramped). `module.json` description: "Sample-rate patchable control pulse oscillator".

## Search for batch modules among existing modules
Searched `modules/*/module.json` names and descriptions (35 module folders): adsr, blend, chaos_lite (CHAOS), chord, clock, cv_to_notes, delay, function_envelope, groove, host_keyboard, ladder, lfo, macro_oscillator, midi_cc_to_cv, midi_in, midi_to_cv, mixer, monitor, noise, notes_to_cv, osc_in, osc_out, output, poly_merge, poly_split, quad_vca, quantizer, resonator, reverb, scale_offset, slew, spectral, vca, vcf, vco.
- Random (CV random / stepped random / S&H module): none exists. Closest: `noise` ("Fixed-seed white noise", one `level` param, AUDIO output, `noise/dsp.h:8`); `chaos_lite` has `roughness`, `drift`, `jitter` params but is an oscillator voice; quantizer and groove have sample-and-hold behaviour inside them.
- Clock divider/multiplier: none exists as a module. Clock has `ticks_per_beat` (multiply); groove has per-track `div` in pattern data.
- Macro: no control-macro module. `macro_oscillator` (name "Macro Oscillator") is an oscillator with 24 models (`macro_oscillator/dsp.h:28`), not a macro-control module.
- Rhythmic modulator / trigger-pattern module (other than groove): none found. Slew, scale_offset and midi_cc_to_cv exist as CV utilities (not read in detail).

## Notes
- `midi_to_cv/module.json` parameter slots skip 5 (legato=4, sustain=6); code declares sustain at slot 6 as the 6th array entry. `steal_policy` has range 0..0 and no read in `dsp.h`.
- `chord`, `cv_to_notes`, `host_keyboard`, `midi_in`, `midi_to_cv`, `notes_to_cv`, `quantizer` and `groove` have no param with MOD; all are STEP|AUTO. The engine tests that assert STEP implies not MOD cover only adsr, lfo, vca, vcf, vco (`port_behavior_tests.cpp:48`).
- `lfo` has mixed flag sets: `sync` STEP without AUTO; `beats` MOD without PV/AR; first three include PV and AR.
- `clock` params 1 and 3 (`ticks_per_beat`, `run`) are MOD although the code rounds/thresholds them (integer ticks; run `>= .5`).
- `function_envelope` module.json description says "Single-channel" but code is 16-voice per-channel.
- `quantizer` `Info` declares version 1 (`dsp.h:17`), `module.json` has `abi_version` 2 (other modules use `Info{...,2}`).
- `module.json` has no `description` for lfo, midi_in, midi_to_cv and host_keyboard; lfo's has no `license` field either.
