<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S1 — Module inventory (scout, 2026-11-26)
Lab commit: 11a68c2 (`git rev-parse --short HEAD`). Facts only. Paths.

## 1. Registration (today)
- `engine/control/module_catalog.h:3-39`: one hand-written `#include "../../modules/<m>/dsp.h"` per module (plus `../../sdk/examples/random_source/dsp.h` :38, `step_sequencer` :39).
- `engine/control/module_catalog.h:44-48`: `static const std::vector<const ws2_descriptor *> modules{ #define WS_APP_MODULE(Class) ws::Module<Class>::descriptor(), #include "module_catalog.inc" ...`
- `engine/control/module_catalog.inc:2-38`: one `WS_APP_MODULE(<ns>::<Class>)` per module (37 lines, e.g. `:2 WS_APP_MODULE(ws2ports::Vco)`, `:30 groove::Sequencer`).
- `engine/CMakeLists.txt:122-125`: `foreach(module vco lfo vcf adsr vca clock function_envelope ladder mixer noise output scale_offset slew)  add_library(ws2_${module} SHARED ../modules/${module}/module.cpp)` (no per-module test target here).
- `engine/CMakeLists.txt:113-120`: same pattern for `osc_in osc_out monitor` plus `abi2_${module}_tests` from `../modules/${module}/tests.cpp`.
- `engine/CMakeLists.txt:104-107`: `ws2_groove`, `ws2_host_keyboard` listed individually; `:262` `add_subdirectory(../modules/macro_oscillator ...)`; `:353-365` `add_subdirectory(../modules/<x> <x>)` for chaos_lite blend resonator spectral delay reverb quantizer quad_vca notes_to_cv cv_to_notes poly_merge poly_split chord.
- midi_in/midi_to_cv/midi_cc_to_cv are in the catalog (.inc:22-24) and included in .h:15-17; their CMake wiring is under `add_subdirectory(../host/midi midi_io)` (`engine/CMakeLists.txt:261`), not checked further.
- `docs/MODULE_BUILD_GUIDE.md:65-67` lists 3 manual edits per new module: engine CMake `add_subdirectory`, `module_catalog.h` include, `module_catalog.inc` line.

## 2. Module table (36 folders incl. `port_state.h` file; 35 module folders)
Ports `id:kind` (kinds as WS2_*; poly/first/sum modes omitted). Params `id min–max =default flags`. M=MODULATABLE S=STEPPED A=AUDIO_RATE_OK V=PER_VOICE. `PF` = port_flags (modules/port_state.h:22) = M+V+A. Source: dsp.h line cited by `ws::param`/`ws::port` lines. "tests"/"cmake" = own `tests.cpp` / own `CMakeLists.txt` in the folder (module.json, dsp.h, README.md all present unless noted; DESIGN.md/LICENSE not tracked here).

| folder | id | inputs | outputs | params | tests | cmake |
|---|---|---|---|---|---|---|
| adsr | essentials.adsr | gate:GATE, notes:EV_NOTES | envelope:CV_UNI | attack .0001–30 =.01 MV; decay .0001–30 =.1 MV; sustain 0–1 =.7 MVA; release .0001–30 =.2 MV; mode 0–1 =0 S; hold 0–30 =0 MV (dsp.h:9-12) | y | y |
| blend | sound.blend | a:AUDIO, b:AUDIO, switch:TRIGGER | audio:AUDIO | mode 0–(kModes-1) =Crossfade MS; balance 0–1 =.5 M; seg_a .01–2 =.22 M; seg_b .01–2 =.22 M; fade .001–.2 =.01 M; jitter 0–1 =.3 M (dsp.h:21-26) | y | y |
| chaos_lite | essentials.chaos_lite | pitch:PITCH, gate:GATE, velocity:CV_UNI, fm:CV_BI | left,right:AUDIO | 27 params (dsp.h:18-47): M: shape_a 0–2, shape_b 0–2, detune ±60, level_a/b 0–1, pan_a/b ±1, depth, body_tune ±2, feedback 0–.92, damping 0–.99, body_mix, roughness, rough_rate 1–150, drift, jitter, fall, lfo_rate .02–12, lfo_depth, lfo_self, cutoff 20–20000, level; S: octave_a/b ±3, route 0–2, lfo_target 0–2, lfo_shape 0–3 | y | y |
| chord | essentials.chord | notes:EV_NOTES | notes:EV_NOTES | enable1-4 0–1 S; shift1-4 −24–24 S (defaults 4,7,12,−12) (dsp.h:24-31) | y | y |
| clock | essentials.clock | reset:GATE | clock:GATE | bpm 20–300 =120 PF; ticks_per_beat 1–24 =1 PF; duty .01–.99 =.5 PF; run 0–1 =1 PF; sync 0–1 =0 S (dsp.h:8) | y | n |
| cv_to_notes | essentials.cv_to_notes | pitch:PITCH, gate:GATE, velocity:CV_UNI | notes:EV_NOTES | legato 0–1 =0 S | y | y |
| delay | fx.delay | left,right:AUDIO, clock:TRIGGER | left,right:AUDIO | time .001–2 =.375 M; division 0–7 =5 S; feedback 0–1 =.4 M; tone −1–1 M; mode 0–1 S; mix 0–1 =.35 M (dsp.h:28-33) | y | y |
| function_envelope | essentials.function_envelope | gate:GATE | envelope:CV_UNI | rise .0001–30 =.01 PF; fall .0001–30 =.1 PF; curve −1–1 =0 PF | y | n |
| groove | sequencing.groove | clock:TRIGGER, run:GATE, reset:TRIGGER | t1/t2_{pitch:PITCH, gate:GATE, mod1:CV_BI, mod2:CV_BI, notes:EV_NOTES}; t{1,2}_pos, _loop_lo, _loop_hi:CV_BI; t{1,2}_fired:GATE (18 ports, dsp.h:23-40) | run, stop, reset, mute, t1_run/stop/mute, t2_run/stop/mute: all 0–1 =0 S (dsp.h:43-52) | n | n |
| host_keyboard | host.keyboard | – | pitch:PITCH, gate:GATE, velocity:CV_UNI, notes:EV_NOTES | voices 1–16 =8 S; mode 0–3 S; octave −3–3 S | y | n |
| ladder | essentials.ladder | audio:AUDIO | audio:AUDIO | cutoff 20–20000 =1000 PF; resonance 0–1 PF; drive 0–2 PF | y | n |
| lfo | essentials.lfo | – | control:CV_BI, phase:CV_UNI | rate .01–20 =1 MVA; depth 0–1 =1 MVA; offset −1–1 MVA; sync 0–1 =0 S; beats .125–16 =1 M (dsp.h:12-16; rate/depth/offset flags M+V+A) | n | n |
| macro_oscillator | ports.macro_oscillator | pitch:PITCH, model_cv,fm,harmonics_cv,timbre_cv,morph_cv:CV_BI, trigger:GATE, level:CV_UNI, gate:GATE | main,aux:AUDIO | model 0–23 S; coarse ±48; harmonics,timbre,morph .5; fm_amount,timbre_amount,morph_amount ±1; decay .5; lpg_colour .5 (all non-model: MV) (dsp.h:28-37) | y | y |
| midi_cc_to_cv | midi.cc_to_cv | midi:EV_MIDI | cc1..cc8:CV_BI | none (dsp.h:12) | y | n |
| midi_in | midi.in | – | midi:EV_MIDI | channel_filter 0–16 =0 S | y | n |
| midi_to_cv | midi.to_cv | midi:EV_MIDI | pitch,gate,velocity,aftertouch,pressure,bend,mod,notes,last_note,trig | voice_count 1–16 =4; allocation_mode 0–3; steal_policy 0–0; mono_priority 0–2; legato; sustain =1; pitch_bend_range_semitones 0–48 =2; apply_bend =1; channel_filter 0–16 (all S) (dsp.h:21-29) | y | n |
| mixer | essentials.mixer | a,b:AUDIO | audio:AUDIO | level_a 0–2 =.5 PF; level_b 0–2 =.5 PF | y | n |
| monitor | monitor | events:EV_MESSAGE, in1,in2:ANY | – | none | y | n |
| noise | essentials.noise | – | audio:AUDIO | level 0–1 =.2 PF | y | n |
| notes_to_cv | essentials.notes_to_cv | notes:EV_NOTES | pitch:PITCH, gate:GATE, velocity:CV_UNI, trig:GATE | voices 1–16 =4 S | y | y |
| osc_in | osc.in | – | row1..row8:CV_BI, messages:EV_MESSAGE | none | y | n |
| osc_out | osc.out | row1..row8:CV_BI (FIRST), notes:EV_NOTES | – | none | y | n |
| output | essentials.output | audio:AUDIO (SUM) | audio:AUDIO | none | y | n |
| poly_merge | essentials.poly_merge | in1..in8:CV_BI (FIRST) | out:CV_BI (POLY) | none | y | y |
| poly_split | essentials.poly_split | in:CV_BI (POLY) | out1..out8:CV_BI (FIRST) | none (no README.md in folder) | y | y |
| quad_vca | essentials.quad_vca | in1-4:AUDIO, cv1-4:CV_UNI | out1-4, mix:AUDIO | level1-4 0–1 =1 MVA; mode1-4 0–1 S; response 0–1 =.4 M (dsp.h:26-34) | y | y |
| quantizer | essentials.quantizer | pitch:PITCH, trigger:TRIGGER | pitch:PITCH, changed:TRIGGER | scale 0–13 =1; root 0–11; shift −7–7; octave −3–3; n0..n11 0–1: all S (dsp.h:12-14,25-31) | y | y |
| resonator | essentials.resonator | audio:AUDIO, pitch:PITCH, strike:TRIGGER | audio:AUDIO | tune ±24; structure 0–3 (MVS); decay .05–20 =1.5; damping; strike_tone; strike_level; mix =1; level =.7 (others MV) (dsp.h:18-25) | y | y |
| reverb | fx.reverb | left,right:AUDIO | left,right:AUDIO | size, decay .2–20, damping, predelay 0–.25, width, motion, mix: M; freeze 0–1 S (dsp.h:45-52) | y | y |
| scale_offset | essentials.scale_offset | control:CV_BI | control:CV_BI | scale −2–2 =1 PF; offset −1–1 PF | y | n |
| slew | essentials.slew | control:CV_BI | control:CV_BI | rise 0–10 =.1 PF; fall 0–10 =.1 PF | y | n |
| spectral | sound.spectral | a,b:AUDIO | audio:AUDIO | mode (MS), size 0–3 (S), morph (M), curve (S), pitch (S), amount (M), smooth (M), b_level 0–2 (M), level 0–2 (M), chunk_a/b 1–64 =5 (MS), phase (S), bands 6–kMaxBands =24 (MS), flatten (M), release .005–.4 (M), noise (M) (dsp.h:53-69) | y | y |
| vca | essentials.vca | audio:AUDIO, gain_cv:CV_UNI | audio:AUDIO | gain 0–2 =1 MVA | n | n |
| vcf | essentials.vcf | audio:AUDIO | low12,low24:AUDIO | cutoff 20–20000 =1000 MVA; resonance 0–.95 MVA | n | n |
| vco | essentials.vco | pitch:PITCH, fm:AUDIO, notes:EV_NOTES | audio:AUDIO | frequency .01–20000 =220 MVA | n | n |

Notes: modules with `tests=n` have no `tests.cpp`; `modules/adsr/README.md:4` says shared tests live in `tests/native/abi2/module_tests.cpp` + `integration_tests.cpp` (adsr README:17 also references nonexistent `native/modules2/adsr`; lfo README:4 references `native/tests2/...`). `modules/port_state.h` is a header, not a module.

## 3. Modules with NO WS2_MODULATABLE parameter
chord, cv_to_notes, groove, host_keyboard, midi_in, midi_to_cv, midi_cc_to_cv (no params), monitor (none), notes_to_cv, osc_in (none), osc_out (none), output (none), poly_merge (none), poly_split (none), quantizer. (Not listed: modules where only the stepped params lack M but another param has M, e.g. clock/delay/lfo.)

## 4. Behaviour notes (README / dsp.h quotes)
- **adsr**: gate cable wins over notes: "A connected nonzero-channel gate cable wins over all note events. Gates use >0.5 on / <0.25 off." (modules/adsr/README.md:6). `mode` Gate(0)/Trigger(1): "Trigger (1) runs one envelope cycle per rising gate edge or accepted NOTE_ON... NOTE_OFF and falling cable gates do not end the Trigger cycle" (modules/adsr/README.md:12). Trigger-mode hold param 0–30 s. No transport.
- **function_envelope**: gate-driven rise/fall; README: "No note-event or transport semantics are added." (function_envelope/README.md:3). Single gate input only; no notes input.
- **lfo**: sine only ("Sine control oscillator", lfo/README.md:6). Tempo sync: "Sync uses transport quarter-note position. When transport is missing, manual rate runs. Stopped sync holds phase; locate sets it directly." (lfo/README.md:8); code `lfo/dsp.h:28-29` uses `b.transport()->beat`, `bpm`; `beats` param .125–16 beats/cycle. No reset/trigger input, no other shapes in README.
- **clock**: gate output only; README: "Free-running double phase... No transport sync is added." (clock/README.md:3); yet params include `sync` (0–1 S, dsp.h:8) and `process_synced` (dsp.h:17) uses `b.transport()` bpm/beat when playing; `ticks_per_beat` 1–24 integer rounded; reset input rising >=0.5 edge. No swing, no divisions beyond ticks_per_beat, no run/stop outputs.
- **noise**: README (noise/README.md:3) "Xorshift32 advances even while muted... No engine seed is read." Output audio only (white), single `level`; no colour/other outputs; no triggers.
- **slew**: rise/fall 0–10 s/unit; "Zero time jumps directly to the target." (slew/README.md:3). No gate/trigger/transport behaviour.
- **groove**: two-track step sequencer, 8/16/32/64 steps, `div` 1/2/4/8 sixteenths/step (README.md:14-20); chance/ab/first/not_first conditions (:20-23); clock input optional (TRIGGER), host tempo via `tempo_source` (config.h:42,44; dsp.h:439-446 uses `b.transport()` bpm when `TempoHost && !external_clock`). Rising-edge run/stop/reset/mute params (:41-48). README states lacks: "No live-edit, seamless Apply or physical listening is claimed." (:66); "Live per-step DSP editing remains deferred to S2." (:86); "seamless Apply and phase continuity are later work" (:78); only two tracks play (:16). Fresh load always stopped (:38).
- **osc_in**: "no inputs or parameter knobs" (osc_in/README.md:4); kinds cv/gate/trigger (:14); trigger fires >=1 ms (:15); no sockets in module, sidecar-owned (:5,:43); "No OSC networking exists in the web demo." (:49); transport: none mentioned.
- **osc_out**: "Eight CV/gate inputs (row1–row8) and a poly Notes-event input; no outputs or parameters" (osc_out/README.md:4); only channel 0 of signal inputs sent; gate transitions counted at sample precision; notes via 64-slot SPSC ring, drop counter when full; localhost only (127.0.0.1).

## 5. SDK
- `sdk/`: `LICENSE`, `fastmath.h`, `signals.h`, `simd.h`, `wirescape_sdk.h`, `include/` (wirescape/module2.h etc.), `template/`, `examples/`.
- `sdk/template/`: DESIGN.md, README.md, module.cpp, module.json, tests.cpp.
- `sdk/examples/`: `random_source/` and `step_sequencer/` (each DESIGN.md, README.md, dsp.h, module.cpp, module.json, tests.cpp) plus `test_support.h`. Both included in catalog (`module_catalog.h:38-39`).
- `docs/MODULE_BUILD_GUIDE.md` references `native/` paths; `native/` today contains only `CMakeLists.txt`, `README.md`. Also referenced: `../modules2/<name>`, `../tests2/allocation_watch.cpp` (:56), neither exists (`modules2/`, `tests2/` absent).
- Referenced and MISSING: `native/control/module_catalog.h` (real: `engine/control/module_catalog.h`), `native/control/module_catalog.inc` (real: `engine/control/module_catalog.inc`), `native/engine2/CMakeLists.txt` (real: `engine/CMakeLists.txt`), `native/modules2/quantizer[/CMakeLists.txt]` (real: `modules/quantizer/`), `native/modules2/vca` (real: `modules/vca/`), `native/sdk/examples/random_source`, `native/sdk/examples/step_sequencer`, `native/sdk/template` (real: `sdk/examples/...`, `sdk/template`), `../../tests2/allocation_watch.cpp` (real: `tests/native/abi2/allocation_watch.cpp`).
- Referenced patterns (no match): `native/modules2/<name>[/README.md]`, `native/include/wirescape/*.h` (real: `sdk/include/wirescape/`), `native/sdk/*.h` (real: `sdk/*.h`).
