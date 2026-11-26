<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S7 — User docs, patches and tools (scout)
Lab commit: 11a68c2 (2026-11-25). Read-only scout; facts only. Dates = last commit touching the path.
Note: `native/` in this lab copy holds only CMakeLists.txt and README.md (no native/include, native/examples, native/src).

## 1. User-facing docs (path | lines | last commit | audience | content | staleness)
- docs/ARCHITECTURE.md | 363 | 2026-11-14 | devs/agents | "Architecture today" after M0 clean-copy migration (:1-4) | names missing: PLAN.md, STATUS.md, native/include/wirescape/{engine,module,module2}.h, native/src/engine.cpp, native/examples/Six_Essentials_Demo.json (now host/examples/), native/sidecar/DESIGN.md, native/voice/note_to_cv.h, tools/ci/guard.py, tools/capture/README.md, ../apps/studio/IMPORT.md, module_catalog.h
- docs/BENCHMARKING.md | 82 | 2026-11-14 | devs | device-free measurements via `tools/dev.py build --headless` / `test` (:1-3) | names build_reports/abi2/benchmark.json (output path, not in tree)
- docs/CONTROLLERS.md | 46 | 2026-11-14 | owner/users | OSC controller setup, Pico defaults table, ESP32/Pico W sketch | device wording :8,:10,:14-17,:19,:27,:31,:34,:37-38; names native/io/osc/codec.h (missing)
- docs/INSTALL.md | 295 | 2026-11-25 | owner/users | "Install Wirescape 1.0 from source", Windows, Pi 5, launch, patch_roundtrip (:226) | :189 "+ LAN OSC (ESP32)"; no missing paths found
- docs/MODULE_BUILD_GUIDE.md | 112 | 2026-11-14 | owner + builders | one-page checklist to add a module (five registrations) | names native/control/module_catalog.h, module.json/dsp.h etc. (relative to module folder)
- docs/PATCH_DESIGNER_GUIDE.md | 884 | 2026-11-23 | patch designers/agents | owner fast-lane authorization (#426) for patch data + module/patch design reference | :59 "owner M8 sessions" (M8 = a milestone/meeting? ambiguous with milestone M8), :552-610 Pico/TouchOSC; names docs/tasks/done/CHAOS_LFO_SHAPES_532.md (missing), slow-glass-pad.json (missing); quad-vca-*.json exist in apps/studio/patches
- docs/PI_APP_SMOKE.md | 61 | 2026-11-14 | owner/lead | Pi ARM64 Electron device-off smoke (#446) on private pi5 runner | refers summary.json (output)
- docs/PI_FRESH_INSTALL.md | 6 | 2026-11-25 | users | stub pointing to INSTALL.md#raspberry-pi-5 | none
- docs/PI_SETUP.md | 6 | 2026-11-25 | users | stub pointing to INSTALL.md#raspberry-pi-5 | none
- docs/PRODUCT_README.md | 67 | 2026-11-25 | public/users | "Wirescape™" v1.0 overview, Electron + Studio + engine | names CONTRIBUTING.md, docs/PLAN.md, docs/STATUS.md (not in docs/ or repo root checked: PLAN/STATUS absent)
- docs/RELEASES.md | 14 | 2026-11-20 | owner/lead | Owner Build releases; OB-0 accepted, tag owner-build-0 -> a440d71 | none checked
- docs/SDK_AUTHOR_GUIDE.md | 230 | 2026-11-14 | module authors | ABI 2 SDK guide v2, worked examples, porting (§15) | names missing: ../../sdk/examples/test_support.h, ../../tests2/allocation_watch.h, docs/PI_RUNNER.md, docs/tasks/done/J7_CHAOS_LITE.md, native/examples/chaos_two.json (now host/examples/), native/io/midi/module_test_support.h, native/modules2/midi_to_cv/dsp.h
- docs/WINDOWS_SETUP.md | 6 | 2026-11-14 | users | stub to INSTALL.md#windows-1011-x64; scripted path tools/windows/setup.ps1 | none
- docs/sequencer/README.md | 34 | 2026-11-14 | devs | sequencer lane index (:1-6) | :6 links AGENT_PROMPT.md which does not exist (dir has GROOVE.md, README.md, UI_DESIGN_BRIEF.md)
- docs/sequencer/GROOVE.md | 100 | 2026-11-14 | devs | Groove sequencer roadmap; baseline main 971d77668 (2026-11-08) | stale baseline by its own wording (:4-5)
- docs/sequencer/UI_DESIGN_BRIEF.md | 147 | 2026-11-14 | UI designer | Groove S1 UI handoff, "proposed", nothing implemented | status line :3

## 2. Device-specific wording (file:line; "M8" matches that are milestone M8 marked [ms])
- "M8" as device: docs/specs/ENGINE_PROTOCOL.md:144,291,292,298,338 (endpoint "M8 MIDI 1" / "M8:M8 MIDI 1" in examples); docs/PATCH_DESIGNER_GUIDE.md:59 ("owner M8 sessions", ambiguous)
- "M8" as milestone [ms]: docs/specs/ABI2_PLAN.md:428; docs/workflow/ROADMAP.md:64-67; milestones/M8.md:2, M9.md:18,20, M10.md:18-20, M11.md:16-36, M12.md:17, OB.md:69,98; PRIORITY.md:6,36; STANDING.md:79,121
- "pico1" addresses: docs/CONTROLLERS.md:8,14-17,37-38; docs/PATCH_DESIGNER_GUIDE.md:555,610; docs/workflow/WINDOWS_EVAL.md:20,59,68; docs/specs/COMMUNICATION_MODULES_PLAN.md:51,177,308,310; apps/studio/src/app/OscEditor.ts:17,154,297 (default row pattern `/pico1/knob/${n}`); apps/studio/src/engine/FakeEngine.ts:895; modules/osc_in/README.md:11,18
- "Pico" wording/functions: apps/studio/src/app/OscEditor.ts:21 `picoDefaults`, :33,:271,:283 preset 'Pico knobs 1–8' (id osc-preset-pico), :286 'Reset to Pico defaults' (osc-preset-reset); docs/CONTROLLERS.md:10,19,27; PATCH_DESIGNER_GUIDE.md:552,588-590; specs/COMMUNICATION_MODULES_PLAN.md:16,58,305,311; workflow/CURRENT.md:13, OB_PLAN.md:12,24 (Pico W 2)
- "TouchOSC": docs/CONTROLLERS.md:8; PATCH_DESIGNER_GUIDE.md:589; OscEditor.ts:284 (preset 'TouchOSC faders /1/fader1–8', id osc-preset-touchosc)
- "ESP32": docs/CONTROLLERS.md:27,31,34; docs/INSTALL.md:189
- modules/*/README.md: only modules/osc_in/README.md hits (above); no M8/ESP32/TouchOSC there.

## 3. Patches
Format key: all patch JSON carry `"format": "wirescape.native.patch"` and `"version"`: 2, except host/examples/Six_Essentials_Demo.json = version 1 (keys format,version,name,outputNode,modules,connections; no settings). Patches in apps/studio/patches/ have SPDX, name, description, format, version, settings. Types from `modules[].type`.
osc.in used by NO patch in either folder. osc.out used only by osc-out-01.json. midi.* used only by host/examples class_demo_1/2/3 and chaos_usb_midi.json.
apps/studio/patches/ (README.md: public library, deployed to web app "Starter patches"; README says Basics 1–7, Scene 1–8 but basics-08 and chaos-01..05, quad-vca-01/02 also exist):
- basics-01-first-tone | host.keyboard, essentials.{vco,adsr,vca,output} | simplest playable synth
- basics-02-fm-filter-lfo | + vcf, lfo | FM/filter/LFO
- basics-03-echo-and-reverb | + fx.delay, fx.reverb | echo+reverb
- basics-04-sequencer-and-quantizer | essentials.clock, quantizer, example.step_sequencer, fx.delay | sequencer + quantizer
- basics-05-random-melody | clock, noise, quantizer, resonator, example.random_source, fx.* | random melody
- basics-06-chaos-keys | essentials.chaos_lite, host.keyboard, fx.reverb | CHAOS keys
- basics-07-macro-keys | ports.macro_oscillator, lfo, host.keyboard | Macro keys
- basics-08-clocked-groove | sequencing.groove, scale_offset, clock, quantizer, delay | clocked groove (not in README list)
- chaos-01-ember-veil-pad, chaos-02-wireglass-lead, chaos-03-orbiting-iron-fx, chaos-04-radio-static-fx, chaos-05-moonlit-drift-pad | chaos_lite + adsr/lfo/clock/function_envelope/vca/random_source/fx.* | CHAOS pads/leads/FX
- osc-out-01 | osc.out, host.keyboard, vco, adsr, vca, lfo, clock, output | sends LFO, clock gate, notes to 127.0.0.1:9001 (README)
- quad-vca-01-lpg-plucks | essentials.quad_vca, vco, adsr, host.keyboard | LPG plucks
- quad-vca-02-four-gate-mix | quad_vca, vco, lfo (no keyboard) | four-gate mix
- scene-01-hollow-chapel | chaos_lite, ladder, lfo, mixer, fx.reverb | cinematic scene
- scene-02-breathing-walls | + clock, noise, slew, random_source | scene
- scene-03-black-ice-choir | chaos_lite, adsr, vca, host.keyboard, fx.* | scene
- scene-04-vowel-apparitions | ports.macro_oscillator, vcf, host.keyboard | scene
- scene-05-glass-cathedrals | macro_oscillator, ladder, mixer, slew | scene
- scene-06-dust-reactor | sound.blend, vco, vcf, ladder, resonator, noise, mixer | scene
- scene-07-witching-hour | example.step_sequencer, quantizer, vco, vcf | scene
- scene-08-neon-elegy | example.step_sequencer, ladder, macro_oscillator, quantizer | scene
host/examples/:
- Six_Essentials_Demo.json (v1) | noise, vcf, ladder, vca, output, clock, function_envelope, slew | all six imported modules (README:1-5)
- chaos_two.json | chaos_lite x, mixer, output, host.keyboard | two CHAOS instances (tools/chaos_two_probe.py target)
- chaos_usb_midi.json | chaos_lite, mixer, midi.in, midi.to_cv (has `dev` key) | CHAOS from USB MIDI
- class_demo_1_chaos | chaos_lite, mixer, midi.in, midi.to_cv, midi.cc_to_cv | CC 21–28 class demo
- class_demo_2_subtractive | vco, vcf, adsr, lfo, vca, midi.* | CC 21–28 subtractive
- class_demo_3_macro | ports.macro_oscillator, vcf, adsr, vca, midi.* | CC 21–28 macro
host/examples/README.md: Six Essentials demo text (:1-5); "Class demos (native v2; devices off until owner launches playback)" (:7+): 48 kHz/256 frames, 4 MIDI voices, CC 21–28 omni, `devices: []` filled by Pi demo launcher; per-patch CC tables; VCO CC27 sweeps freq multiplier; controller travel sections.

## 4. Tools (devices needed? = needs --confirm-* or hardware)
- tools/dev.py | build/test/check/accept/doctor/snapshot/report/benchmark/render/launch (:532-569); docstring "Native build/evidence tools and the Electron development launcher" | `launch` needs --confirm-audio/--confirm-midi/--confirm-lan (INSTALL.md:189); others no
- tools/patch_library.py | validate patch JSON (`check`) or copy (`install`) to chosen folder; --dest, --replace, --shared (48k/stereo/no-device profile) (:129-133) | no
- tools/patch_roundtrip.py | "OB-a1 real Studio codec + device-free native runtime load/save/load evidence"; --renderer (required), --dir, --report, --source-sha (:280-284) | no
- tools/golden.py | same-build offline hash assert; cross-build hashes recorded only | no
- tools/gen_ui_catalogue.py | generate native identities + UI presentation; refuses identity mismatch | no
- tools/module_cpu_probe.py | offline Pi CPU acceptance, any built-in module, 2 instances 48 kHz/128 | no
- tools/chaos_two_probe.py | offline Pi acceptance for two 4-voice CHAOS-lite | no
- tools/owner_record.py | owner-run device-off test record, Windows and Pi | no (owner-run)
- tools/sidecar_edit_soak.py | bounded device-free sidecar edit soak | no
- tools/examples/osc_in_sender.py | send OSC float or 50 Hz sweep to OSC In | LAN/localhost socket only
- tools/examples/osc_out_receiver.py | stdlib OSC receiver for OSC Out | localhost socket
- tools/examples/osc_loopback_check.py | OSC In -> OSC Out check against built wirescape-engine | no devices
- tools/examples/test_osc_examples.py | known-answer OSC tests | no
- Subfolders: bench/ (abi2_cost, abi2_foundation, compare_bench), capture/, ci/ (changed_scope, dev_run, static_checks, ...), cloud/, diagnostics/, experiments/, foundation/, module/ (wsmod build/check/render/matrix), pi/ (app_smoke, demo.sh, autostart installers, preflight), protocol/ (generate.py, sidecar checks), render/, windows/.
- wirescape_render: target defined tools/render/CMakeLists.txt:3 (`add_executable(wirescape_render main.cpp)`); docs use `build/native/wirescape_render` (INSTALL.md:226); tools/render/{evidence,library_smoke}.py drive it (evidence.py:2,153; library_smoke.py:4,90). Source main.cpp under tools/render.

## 5. controllers/
controllers/WirescapeOSC/WirescapeOSC.ino only (277 lines): Arduino sketch for ESP32-S3 / Pico W WiFi OSC controller (pots GPIO 4/5/6, button GPIO 15; docs/CONTROLLERS.md:27-38). CONTROLLERS.md:31 says not compiled on ESP32 yet.

## 6. bench/ (README.md:3-14: offline/ and device/ tracks; results under results/<machine>/...)
- compare/ measure.py, analyse.py, generate_scaling.py, OWNER_RUN.md | comparison measurements
- continuity/ capture.py, engine.py, DESIGN.md, cost/ | continuity capture design
- device/ CMakeLists, CODEX_RUNBOOK, OWNER_RUN, analyse.py | owner-run device bench (needs --confirm-audio)
- evidence/ macro_non48, reverb_s72, s7_1_193 | stored evidence folders
- gate/ compare.py, instructions.py + tests | gate comparison/instruction counts
- golden/ compare.py, experiment.py, coverage_manifest.json, event_path_evidence.json | golden hash tooling
- io/ soak.py, gate_snapshot_witness.{py,md}, test_counter_evidence.py | IO soak/counters
- m1/ paired.py, links.py, keyboard_attribution.py + tests | M1 paired measurements
- offline/ choke_listening.py, ci_stage_facts.py, electron_startup.cjs, T7_0_CAPTURE.md | offline track
- owner_eval/ windows/ | owner evaluation material
- patches/ coverage, owner | bench patch sets
- portability/ probe.py, tests | portability probe
- reference/ freeze.py, unpack.py + tests | reference freeze/unpack
- sdk/ out_of_tree_trial.py | SDK out-of-tree trial
- ui/ ob_f1_capture.cjs, ob_f1_metrics.cjs + test | UI capture metrics
- module_sets.json at top level
