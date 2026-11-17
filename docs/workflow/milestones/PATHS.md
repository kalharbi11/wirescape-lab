<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Path inventory for M3, M4 and M5 task issues

For the lead, when writing task issues: which files each task touches, by reading the tree at
`b02db25` (Opus helper for Fable, 2026-11-16). It is a starting point, not authority: the contract's
"Allowed paths" cell decides, with STANDING SR7 for forced mechanical extras. Verify line numbers live.

Read-only inventory at `main` `b02db25` (2026-11-16 ET). Line numbers are for that commit. M1 S2 (#111) has
not merged, so ABI1 is still in the tree (`native/control/app_legacy_fixture.cpp` and `add_abi1` are present).

**Post-S6 column.** The mapping comes from `0002` "Target layout" (D2) and `0006` S6. What is written:
`native/engine2` + `native/control` → `engine/`; `native/modules2/<m>` → `modules/<m>`; `native/sdk` and the
module API header → `sdk/`; sidecar, audio, midi, osc and the patch document (`native/sidecar`, `native/io/*`,
`native/document`) → `host/`. **The subfolder names under `host/` are not written.** `native/web` → `targets/web`.
`apps/`, `tools/`, `bench/`, `facts/`, `docs/` stay where they are. What is **unknown** (not written anywhere):
`native/tests2`, `native/engine2/tests`, `native/voice`, `native/tools/render`, `native/include/wirescape/{engine,
linear_ramp,output_policy}.h`, `native/third_party`, `native/examples`, `native/cli` (S4 may delete it),
`native/CMakeLists.txt`, and the top-level `tests/protocol/`.

## T1.6 a/b/c engine file split (0007)
| Item | Path:line evidence | Post-S6 |
|---|---|---|
| Monolith | `native/engine2/engine2.cpp` 1271 lines; anon ns `:24-180`; `Node` `:99-143`; `Edge` `:172-176`; `Impl` ~`:182-273`; `process_node` `:554-731`; `render` `:850-947`; `reconfigure` `:1029-1105`; `replan` `:1118-1270` | `engine/` (file names from 0007) |
| Public API (unchanged) | `native/engine2/engine2.h` (103 lines) | `engine/engine2.h`? name not written |
| New files | `native/engine2/{types.h,instance.h,layout.h,build.cpp,render.cpp,edit.cpp}` | `engine/` |
| CMake | `native/engine2/CMakeLists.txt:34` `add_library(wirescape_engine2 STATIC engine2.cpp)` | `engine/CMakeLists.txt` |
| **Outside: second compile list** | `native/web/CMakeLists.txt:40` `add_library(web_core STATIC ${native}/engine2/engine2.cpp …)`. PR (c) must add the new .cpp files here or the web build breaks | `targets/web/CMakeLists.txt` |
| Outside: probe include path | `bench/offline/r2_probe.py:49` `-I native/engine2` (a header-only include; not verified that it survives a type move) | unchanged |
| Outside: complexity scope | `bench/offline/repo_facts.py:128` hard-codes `native/engine2/`, `native/control/`, `native/sidecar/` (rule 4 measures this) | must follow S6 |
| Tests (includes only) | `native/engine2/tests/*.cpp` (17 files), `native/tests2/*.cpp`; 25 files include `engine2.h`. None includes `engine2.cpp` | unknown |
| Other `engine2/` includes | `native/io/midi/midi_service.cpp:3`, `native/modules2/midi_in/dsp.h:4` include `../../engine2/midi_release.h` (unaffected unless moved) | — |

## TR1 / TR2 / TR3 transport (0008)
| Task | Files that change (evidence) | Post-S6 |
|---|---|---|
| TR1 engine | `native/engine2/engine2.h:16` (`bpm`, `playing` in Config), `:77` `transport()`; `engine2.cpp:989` direct writes (race); `collect()` `:460-515`; critical ring `:68,478`; `enqueue` `:825-838` takes a node, so a host-addressed packet needs a new route; process-time transport `:647-653`; beat advance `:872`, `:929`. Beat is reset in `Engine::reset` `:979`; the beat is carried in `reconfigure` `:1102`; `replan` keeps `old.cfg`, so bpm and playing already survive a replan (`:1118-1270`, `cfg` is never swapped) | `engine/` |
| TR1 ABI | `WS2_TRANSPORT_EVENT` already exists (`native/include/wirescape/module2.h:30`); `ws2_transport` `:60-63`. No header edit needed (not verified for the payload layout) | `sdk/` |
| TR1 sidecar | `native/sidecar/session.cpp` `apply()` `:969-1294` (new `setTransport` branch near `setParam` `:1203`, which enqueues through `app_engine_native(active_).enqueue` `:1219`); `hello()` capabilities `:1373-1386` (list `:1375-1376`); `status()` `:1388-1432`; `session.h` | `host/` |
| TR1 document | `native/document/runtime_patch.cpp:40-46` reads `settings.*` (add `transport`); `runtime_patch.h`; `native/document/runtime_patch_tests.cpp` | `host/` |
| TR1 outside: spec and schema | `docs/specs/ENGINE_PROTOCOL.md` (command table); `docs/specs/patch_v2_draft.schema.json:13-21` (`settings`, `additionalProperties: true`); **once PV1 merges:** `docs/specs/protocol.schema.json`, regenerated `apps/studio/src/engine/generated/protocol_v0.ts`, `native/sidecar/generated/protocol_v0.hpp`, `tools/protocol/generated/command_error_tables.md` (the PV1 drift check validates the sidecar protocol tests) | unchanged / unknown |
| TR1 outside: fixtures | `native/sidecar/protocol_tests.py:463` asserts the **exact** capability list; `tests/protocol/golden_v0.ndjson` (2 capability lines); `native/sidecar/testdata/s0_status.ndjson` (the S0 snapshot changes when `status.transport` is added); `apps/studio/tests/mock-bridge/bridge.ts` (hello/status mock) | unknown for `tests/` |
| TR1 outside: web | `native/web/web_engine.cpp:193-261` is a second, hand-written command dispatcher (no `setTransport`). `apps/studio/src/web/WebBridge.ts:12-13` drops device commands. Whether the web needs it is not stated in 0008 | `targets/web/` |
| TR1 facade | `native/control/app_engine.{h,cpp}` only if the packet goes through the facade; the sidecar already calls `app_engine_native()` directly | `engine/` |
| TR1 T0.13 row | `bench/continuity/` (row "setTransport bpm change") | unchanged |
| TR2 Clock | `native/modules2/clock/dsp.h:8` parameter table (4 parameters, the last `ws::param` argument is `legacy_index` 0..3; appending `sync` needs index 4), `module.json`, `tests.cpp`, `README.md`/`DESIGN.md` | `modules/clock/` |
| TR2 Groove | `native/modules2/groove/config.h:35,60,94,114` (`bpm` parse and validate), `dsp.h:90-95,378-410`; **Groove has no `tests.cpp`**: its tests are `native/document/groove_runtime_tests.cpp`, `groove_observation_tests.cpp`; config branch `native/document/runtime_module_config.h:66` | `modules/groove/`, `host/` |
| TR2 outside | `apps/studio/public/catalogue-presentation.json:14` (Clock entry; the generator requires parameter-ID equality), regenerate `apps/studio/public/wirescape_modules.json` (`tools/gen_ui_catalogue.py`); `native/sidecar/testdata/s0_catalogue.ndjson` changes (I7 snapshot); `apps/studio/public/panels/essentials.clock.json`; `docs/PATCH_DESIGNER_GUIDE.md`; `tools/foundation/tests/test_ui_catalogue.py` (not verified that it needs an edit) | unchanged |
| TR3 Studio | `apps/studio/src/system/StatusBar.ts:28,55,133-136` (Clock BPM and RUN/STOP button); `apps/studio/src/app/App.ts:226-229` (`onClockToggle`), `:1008`, `:1375-1380` `toggleClock` (sets the Clock module's `run`); `src/engine/EngineClient.ts:74` `clock?: {bpm,running}` (the type of `status.clock`); `src/engine/RealEngine.ts` (status parse, new method); `src/engine/FakeEngine.ts:823` (the only producer of `status.clock`); default of decision 8: `src/groove/pattern.ts:61` `defaultConfig`, Clock params on add (`App.ts:1240-1248`) | `apps/` |
| TR3 tests | `apps/studio/tests/*.spec.ts` (Playwright), `tests/mock-bridge/` | `apps/` |

## MB1 / MB2 / MB3 module build and registry (0009). The "Today" list checked against the tree
| # | 0009 claim | Tree at b02db25 |
|---|---|---|
| 1 | `module_catalog.h` has 34 lines of `#include` | 36 `#include` lines: 32 modules2 `dsp.h` + 2 SDK examples + others (`native/control/module_catalog.h:3-45`; `.inc` included at `:42`). **Confirmed with a different count** |
| 2 | `.inc` has 35 lines | 34 `WS_APP_MODULE` entries (`module_catalog.inc:2-35`). Confirmed (35 lines with the header) |
| 3 | `engine2/CMakeLists.txt:90-111, 147-152, 162, 254-255` | **Lines moved:** `:80-86` SDK examples, `:90,92` groove and host_keyboard, `:99-106` osc_in/osc_out/monitor, `:108-111` 13 modules, `:147-152` and `:191-195` legacy-pair tests, `:236` `add_subdirectory(../io/midi)`, `:237` macro_oscillator, `:329-338` ten `add_subdirectory`, `:319` `WS_KNOWN_MODULE_IDS`. **Also** `native/io/midi/CMakeLists.txt:59-65` builds midi_in, midi_to_cv, midi_cc_to_cv (not named in 0009) |
| 4 | `module.json` read by `tools/gen_ui_catalogue.py` | Confirmed: `gen_ui_catalogue.py:14` globs `native/modules2/*/module.json` |
| 5 | `catalogue-presentation.json` | Confirmed; **also read by CMake** at configure time to generate the sidecar category header (`native/CMakeLists.txt:156-172`) |
| 6 | `known_module_ids.txt` | Confirmed; 33 IDs, **`osc.out` absent**; read by `native/engine2/CMakeLists.txt:319` and `bench/gate/instructions.py:163-180` |
| 7 | `runtime_module_config.h` branches | Confirmed: `native/document/runtime_module_config.h:59,65,66,210,291,376,384,439` |
| 8 | "14 references" to module IDs in core | **Count differs:** grep of non-test core sources finds 38 literal-ID occurrences: `sidecar/session.cpp` 9, `control/app_engine.cpp` 6, `control/midi_host.cpp` 2, `osc_host.cpp` 1, `osc_out_host.cpp` 2, `monitor_capture.h` 3, `engine2/engine2.cpp:146` 1, `document/runtime_module_config.h` 8, `document/telemetry_taps.h` 6. The method behind 0009's "14" is not stated |

| Stage | Files that change | Outside the obvious directory | Post-S6 |
|---|---|---|---|
| MB1 | new `wire-describe` tool (location not written); `tools/gen_ui_catalogue.py`; generate `tools/foundation/fixtures/known_module_ids.txt`; test vs every `module.json` (32 under modules2 + `native/sdk/examples/{random_source,step_sequencer}/module.json`) | `tools/foundation/tests/test_ui_catalogue.py:17-184`; `native/control/app_engine_tests.cpp:22-35` (≥33 IDs); `bench/gate/instructions.py:163-180` and `bench/gate/compare.py:29-44` (add `osc.out` by hand); the CI job that runs `--check` (ci.yml `:51` runs `unittest discover tools/foundation/tests`) | `modules/`, `tools/` |
| MB2 | delete `native/control/module_catalog.{h,inc}`; rewrite the `foreach` lists in `native/engine2/CMakeLists.txt` and `native/io/midi/CMakeLists.txt:59-65`; ten `native/modules2/*/CMakeLists.txt` and `macro_oscillator/CMakeLists.txt`; delete 34 `module.json` | **Includers of `module_catalog.h`:** `native/control/app_engine.cpp:4`, `app_engine_tests.cpp:4`, `native/engine2/tests/module_cpu_probe.cpp:8`, `native/tests/golden_render.cpp:2` (S4 removes it). **Readers of `.inc`/`module.json`:** `bench/golden/inventory.py:18`, `bench/portability/probe.py:26`, `bench/gate/instructions.py:169-171`, `bench/sdk/out_of_tree_trial.py:35-38,162-166`. Workflow `.github/workflows/portability.yml:79` parses `macro_oscillator/CMakeLists.txt`. Docs: `docs/MODULE_BUILD_GUIDE.md:65`, `docs/SDK_AUTHOR_GUIDE.md:36`. `native/web/CMakeLists.txt:18-50` (compiles the catalogue). Catalogue order (L4): `native/sidecar/testdata/s0_catalogue.ndjson` | `engine/`, `modules/`, `targets/web/` |
| MB3 | CI check that copies `native/sdk/template` | new workflow file, or `.github/workflows/out-of-tree.yml` + `bench/sdk/out_of_tree_trial.py` + `facts/code/out_of_tree_trial.md`; not stated which. `ci.yml` is CI1-owned (see the end of this file) | `sdk/template` |

## T1.9 "Reload engine" (0004: "engine restarts and reloads the open patch; UI stays")
Most of the mechanism exists today.
| Piece | Evidence |
|---|---|
| Spawn and supervision | `apps/desktop/main.ts:219` `engineExecutable()`, `:226-267` `startEngine()` (`spawn` `:233`, crash budget `:258-265`), `:269` `stopEngine()` (stdin EOF, kill after 2 s), `:281-289` `restartEngine(resetFailures)`, `:290` `showEngineFailure()` |
| Existing IPC | renderer→main: command `app.restartEngine` (`main.ts:200-204`, reply `{re,ok,gen:'0'}`); main→renderer: `app.engineExited` (`main.ts:257`), `app.menu*` intents (`:501-503`); IPC channels `wirescape:ready/escape/send/open/save` (`main.ts:558-569`); preload `checkedCommand` (`preload.ts:10-50`), clears `lastHello` on `app.engineExited` (`:51`), `exposeInMainWorld('wirescape')` `:63` |
| Existing menu item | `main.ts:512` "Restart engine" → `restartEngine(true)` |
| Studio side | `RealEngine.restartEngine()` `apps/studio/src/engine/RealEngine.ts:161-176`; on a new `hello` with `wasRunning`, it re-sends `loadGraph(currentDocument())` (`:232-270`), so the open patch is reloaded today; the only caller is `App.ts:1133` (CC Learn recovery). `EngineClient` has no `restartEngine` and FakeEngine has none (App uses `real!`) |
| Tests | `apps/desktop/tests/shell.spec.cjs:53-115` (restart, crash loop), `tests/stub-engine.cjs`; `apps/studio/tests/mock-bridge/{bridge.ts:108,real-engine.spec.ts:113-124,audio-recovery.spec.ts:53}`, `tests/system.spec.ts:207` |
| Dev-loop part (rebuild before restart) | not in the tree; depends on T1.8 |

## T1.5 residue sweep
- Sources: `docs/context/RESIDUE.md` §2–§4; `facts/repo/ci-{linux-x64,linux-arm64,windows-x64}/residue_by_file.csv`
  (164 rows each; commit `7d3842d`, 2026-11-14); generator `bench/offline/repo_facts.py:137-152`.
- **Scanner scope** (`repo_facts.py:145`): `native/`, `apps/`, `tools/` and only the suffixes `.cpp .h .hpp .py .ts .tsx .js .cjs .md .cmake`.
  **It does not count `CMakeLists.txt`, `.json`, `.html`, `.css`, `.sh`, `.mjs`, `docs/`, `bench/` or `.github/`.** The acceptance target "0 in product
  code" is measured only inside that scope.
- Re-run on b02db25 with the same regexes, in scope: 269 Qt/issue/agent hits in 106 files. By directory: `tools/foundation` 70, `apps/studio` 67,
  `native/modules2` 47, `native/document` 20, `native/sidecar` 18, `tools/golden.py` 9, `native/modules` 6 (S4 deletes it),
  `native/README.md` 5, `apps/desktop` 4, `native/control` 4, `native/io` 4, `native/sdk` 3, `native/tests` 2, `native/tests2` 2,
  `native/web` 2, `native/engine2` 1, `native/include` 1, **`native/third_party` 1** (`portaudio/portaudio.h`, vendor code), `native/voice` 1, `tools/cloud` 1.
- Hits outside the scanner's scope: `native/{,document/,engine2/,web/}CMakeLists.txt`, `native/document/ui_starters.json` (6 Qt), `tools/ci/codex_cloud_setup.sh`,
  `tools/foundation/fixtures/known_module_ids.txt`, Studio `.css`/`ui/*.html` (most `#NNN` hits there are probably colour codes; not verified), `docs/specs/*.md` (RESIDUE §4), `bench/**`.
- The regex `fable` counts agent names, so lab notes inside `tools/` or `apps/` that name Fable are residue too.
- Named items: `native/tests/golden_render.cpp:23`, `tools/golden.py --compare-renderer`, `apps/desktop/tests/app-e2e.spec.cjs:25` (`-DWIRESCAPE_BUILD_UI=OFF`),
  `tools/dev.py:81` `qt_prefix`, `tools/pi/demo.env.example`, `.gitignore`, `apps/studio/tests/{review-35,review-artifacts}.spec.ts`,
  `tools/dev.py accept` and `tools/foundation/acceptance*.py`, `tools/foundation/tests/test_doc_links.py`, `ci/from-main/`.
- Evidence output: new `facts/repo/<machine>/residue_by_file.csv` from `bench/offline/repo_facts.py` (workflow `.github/workflows/offline-facts.yml`).

## E6 live modulation amount (0005 D8)
| Layer | Evidence |
|---|---|
| Sidecar | `native/sidecar/session.cpp:1256-1272`: `setModAmount` rewrites `connections[].amount` in a candidate, then `commit(candidate,false)` `:1293` → replan via `midi_->replan` `:735` (`native/control/midi_host.cpp:95-105` → `app_engine_replan` `native/control/app_engine.cpp:111-129` → `Engine::replan`) |
| Engine storage | `Edge::amount` `native/engine2/engine2.cpp:173`; used in `process_node` `:605` (`sum+=edge->amount*value`); **the amount is part of edge identity:** sort `:372`, `reconfigure` delay match `:1082`, `replan` key `:1153`. Set by `Engine::modulate` `:763-765` / `engine2.h:58`. 0005 §5 makes the identity exclude the amount |
| Document | `native/document/runtime_patch.cpp:73` (validates `|amount|≤1`, calls `graph.modulate`) |
| Outside | `native/web/web_engine.cpp:121,247-261` (second implementation); Studio `RealEngine.ts:453-454,521`, `FakeEngine.ts:241`, `EngineClient.ts:181`; spec `docs/specs/ENGINE_PROTOCOL.md` (apply class); protocol schema once PV1 merges |

## E4 layout/instance split and publication (0005 §5)
| Item | Evidence |
|---|---|
| Park state machine | `engine2.cpp:179` `enum Park`, `:198` atomic, `:201` `fade_in`, render `:870-876` (parked writes zeros), `:932-946` (fade-in, park request → fade-out → Parked), `reset` `:986-987`, `replan` `:1121`, `:1186-1197` (request and spin), `:1268` |
| **Second master fade (facade, the loadGraph D5 path)** | `native/control/app_engine.cpp:28-33` `master_fade` atomics, `app_engine_render_live` `:158-210`, `:212-238`; declared `app_engine.h:35-43`; used by `native/sidecar/session.cpp:486,798,829,863,1054,1084` and `d5_gap_deadline.h`; tested in `native/sidecar/protocol_unit_tests.cpp:406-442`. 0005 §5 removes only the engine one; whether this one stays is not stated |
| Routing inside Node | `Node` `:99-143`; swaps in `reconfigure` `:1083-1095` and `replan` `:1213-1225` |
| Render call site | `native/io/audio/callback_render.h`, `engine_slot.h` (render entry; not verified that they change) |

## E3 module data (0005 §6)
| Item | Evidence |
|---|---|
| ABI structs | `native/include/wirescape/module2.h:87-93` `ws2_process` (last field `transport`), `:94-108` `ws2_descriptor` (last field `latency_frames`); C99 check `native/engine2/tests/header_c99.c`; SDK `native/sdk/wirescape_sdk.h` (MIT); spec `docs/specs/ABI2_SPEC.md`. M1 forbids `module2.h` edits; E3 is `merge: fable` |
| Engine ingress/egress | `Packet` `engine2.cpp:39-45`, `Ring` `:47-66`, `Producer` `:67-70`; `Engine::enqueue` `:825-838` (node-addressed); `collect` `:460-515`; `pop_egress` `:949-965`, `Outgoing` `engine2.h:36` |
| Sidecar packing | config bytes `native/document/runtime_module_config.h` (Groove `:66`, OSC Out `:65,210,439`, OSC In `:291`, CC `:384`); `Session::execution` `session.cpp:634-701`; `commit` `:702`; `reconcile_graph` `:881` |
| `ccMap.set` | `native/sidecar/session.cpp:1273-1292` (writes `config.rows[row]`, ≤8 rows, then a replan). **Not handled by `native/web/web_engine.cpp`** (falls through to unknown) and **no client method** (`EngineClient.ts` has none) |
| **Hosts also read the same config** | OSC In routes are parsed from the document by `native/control/osc_host.cpp:34-52` (`config.rows`, ≤8); OSC Out by `osc_out_host.cpp:55-60`; MIDI by `midi_host.cpp:22`. Moving rows to data touches these hosts as well as the modules |
| Modules | `native/modules2/groove/{config.h,dsp.h,module.cpp}` (no `tests.cpp`; tests in `native/document/groove_*_tests.cpp`); `midi_cc_to_cv/{config.h,dsp.h,module.cpp,tests.cpp}`; `osc_in/{…,tests.cpp}`; `osc_out/{…,tests.cpp}`; their `module.json` until MB2 |
| Studio editors | Groove: `src/panels/widgets/GroovePane.ts:22,198`, `src/groove/{GrooveSession.ts,pattern.ts,editorHelpers.ts,chords.ts}`, `App.ts:203` (`setModuleConfig`); CC: `src/app/ccLearn.ts:64,105-126`, `src/canvas/ModuleCard.ts:484-513` (`ui.ccMap`); OSC: `src/app/OscEditor.ts`, `OscOutEditor.ts`, `oscCapture.ts`; doc `src/patch/PatchDoc.ts:243` `setConfig`; tests `apps/studio/tests/{groove-*,osc-*,midi-learn-ui}.spec.ts`, `tests/mock-bridge/groove-apply.spec.ts`, `tests-web/groove-io.spec.ts` |

## E5 replace with adopt (0005 §7)
- `Engine::reconfigure` `native/engine2/engine2.cpp:1029-1105`, declared `engine2.h:95`. **It has no production caller:** only
  `native/engine2/tests/engine_tests.cpp:181` and `staged_tests.cpp:127-173`.
- Replan's "different config → new instance" branch: `engine2.cpp:1145-1155` (the reuse test is `prior->d==n.d && prior->legacy==n.legacy && prior->config==n.config`;
  the else branch sets `born_revision`). Born-revision drop: `:483,503`.
- `adopt` and `replace_fade_ms` are new fields at the end of `ws2_descriptor` (`module2.h:94-108`). Same ABI files as E3.

## Device changes that keep state
| Command | Evidence |
|---|---|
| `setSampleRate`/`setBufferFrames` | `session.cpp:989-1090`: validate `:991-996`; `app_engine_panic` + `stop_audio` `:1041-1042`; **the engine is rebuilt** with `load_runtime_patch(patch_.dump(),…, next_config)` `:1050-1054`; rollback `:1076-1086`. No `save_state`/`load_state` |
| `selectAudioDevice` | `session.cpp:1091-1148`: `midi_->stop(); stop_audio(); device_=id; start_audio(); start_midi()` `:1124-1130`. The engine is **not** rebuilt here; `start_audio` `:361-469` rebuilds at `:482-486` only on its own path (not verified when) |
| Outside | `native/io/audio/portaudio_service.cpp`, `stream_lifecycle_tests.cpp`; `native/sidecar/audio_recovery_tests.cpp`; Studio `RealEngine.ts:244-247`, `App.ts:1454-1610` (settings), `WebBridge.ts:13` (ignored on the web) |

## PV2–PV5 protocol v1 (0010)
| Item | Evidence |
|---|---|
| Sidecar reader/writer/watchdog | `native/sidecar/protocol.cpp:107-111` starts three threads; `read()` `:116-168`; `next()` `:169`; `send()` `:191-203`; **the single stdout writer** `write()` `:204-248`; `monitor()` `:249-267`. `protocol.h:21` says "Reader never owns engine state. Writer alone serializes stdout." P9 (reader runs `panic`/`noteOff`) contradicts that comment |
| Executor | `native/sidecar/main.cpp:19-46`: one loop that does `reply`, then status every 100 ms, telemetry every 34 ms, device poll every 100 ms. Envelope `Session::base()` `session.cpp:1296` (`v:0`); `reply` `:1297-1342` |
| Electron | `apps/desktop/main.ts:125-188` (`decodeLine`, `handleEngineLine`, `drainLines`), `:190-218` `command()`; hung detection (P8) has no code yet; `preload.ts:10-50` validation |
| Studio | `RealEngine.ts:22-25` `Edit{mutation,inverse,rollback}`, `:66` `queue`, `:177-190` inverse attach, `:377-395` `enqueue`, `:399-425` dispatch (one at a time), `:232-271` hello/session, `:308-350` reply handling; `FakeEngine.ts` 836 lines (`implements EngineClient` `:33`); `EngineClient.ts` 208 lines |
| `protocol_disagreements.md` | **Not on main.** It is in open PR #105 (head `8c15a94`), together with `.github/workflows/protocol-v0-drift.yml`, `docs/specs/protocol.schema.json`, `tools/protocol/**`, `apps/studio/src/engine/generated/protocol_v0.ts`, `native/sidecar/generated/protocol_v0.hpp` |
| **v0 literals PV5 must remove** | `apps/desktop/{main.ts, tests/{pi-profile,refused-draft-files,shell,windows-setup}.spec.cjs, tests/stub-engine.cjs}`; `apps/studio/src/{engine/RealEngine.ts,web/WebBridge.ts}`, `tests/mock-bridge/{bridge.ts,golden-v0.spec.ts,real-engine.spec.ts}`, six `tests-web/*.spec.ts`; `native/sidecar/{session.cpp,audio_recovery_tests.cpp,golden_tests.py,protocol_tests.py,snapshot_tests.cpp,testdata/s0_*.ndjson}`; **`tests/protocol/golden_v0.ndjson`** (read by `native/CMakeLists.txt:186` and `apps/studio/tests/mock-bridge/golden-v0.spec.ts:17`); `bench/device/{probe_limits.py,run.py}`, `bench/offline/sidecar_probe.py`; `docs/specs/ENGINE_PROTOCOL.md`, `docs/design/ENGINE_TELEMETRY.md` |
| Outside: stub engine | `apps/desktop/tests/stub-engine.cjs` must emit `alive` once PV4 hung detection exists, or the desktop tests report it hung |
| Outside: web path | `WebBridge.ts` makes up `hello`/`session` in TypeScript and forwards to `wsw_command` (`native/web/web_engine.h:8-9`, `web_engine.cpp:193-261`); `apps/studio/public/web/ws-processor.js`. P7/P8 apply there too (not stated in 0010) |
| S0 coupling | `native/CMakeLists.txt:203-229` copies `session.cpp` into the S0 snapshot test at configure time (CURRENT line 39: reconfigure after `session.cpp` edits) |

## (a) Path overlaps (✓ = edits it)
| Path | T1.6 | TR1 | TR2 | TR3 | MB1 | MB2 | MB3 | T1.9 | T1.5 | E6 | E4 | E3 | E5 | Dev | PV2–5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `native/engine2/engine2.cpp` (+ split files) | ✓ |✓| | | | | | | ✓ |✓|✓|✓|✓| | |
| `native/engine2/engine2.h` | | ✓ | | | | | | | | ? | ✓ | ✓ | ✓ | | |
| `native/engine2/CMakeLists.txt` | ✓ | | | | ? | ✓ | ? | | | | | | | | |
| `native/web/CMakeLists.txt` | ✓ | | | | | ✓ | | | ✓ | | | | | | |
| `native/web/web_engine.cpp` | | ? | | | | | | | ✓ | ✓ | | ✓ | | | ? |
| `native/control/app_engine.*` | | ? | | | ✓ | ✓ | | | ✓ | | ? | | | | |
| `native/control/{osc_host,osc_out_host,midi_host}.cpp` | | | | | | | | | ✓ | | | ✓ | | | |
| `native/control/module_catalog.{h,inc}` | | | | | | ✓(del) | | | | | | | | | |
| `native/include/wirescape/module2.h` | | | | | | ? | | | | | | ✓ | ✓ | | |
| `native/sidecar/session.cpp` / `.h` | | ✓ | | | | | | | ✓ | ✓ | ? | ✓ | | ✓ | ✓ |
| `native/sidecar/protocol.{cpp,h}`, `main.cpp` | | | | | | | | | | | | | | | ✓ |
| `native/sidecar/protocol_tests.py` | | ✓ | | | | | | | | ✓ | | ✓ | | ✓ | ✓ |
| `native/sidecar/testdata/s0_*.ndjson` | | ✓ status | ✓ catalogue | | | ✓ order | | | | | | | | | ✓ |
| `native/document/runtime_patch.cpp` | | ✓ | | | | | | | ✓ | ✓ | | ? | | | |
| `native/document/runtime_module_config.h` | | | ✓ | | | | | | ✓ | | | ✓ | | | |
| `native/document/groove_*_tests.cpp` | | | ✓ | | | | | | ? | | | ✓ | | | |
| `native/modules2/{clock,groove}/` | | | ✓ | | ✓(json) | ✓ | | | ✓ | | | ✓ groove | | | |
| `native/modules2/{midi_cc_to_cv,osc_in,osc_out}/` | | | | | ✓(json) | ✓ | | | ✓ | | | ✓ | | | |
| `native/io/midi/CMakeLists.txt` | | | | | | ✓ | | | | | | | | | |
| `apps/studio/public/{catalogue-presentation,wirescape_modules}.json` | | | ✓ | | ✓ | ✓ | ✓ | | ✓ | | | ? | | | |
| `apps/studio/src/engine/{RealEngine,FakeEngine,EngineClient}.ts` | | | | ✓ | | | | ✓ | ✓ | ✓ | | ✓ | | | ✓ |
| `apps/studio/src/app/App.ts` | | | | ✓ | | | | ✓ | ✓ | | | ✓ | | | ✓ |
| `apps/studio/src/system/StatusBar.ts` | | | | ✓ | | | | ? | | | | | | | |
| `apps/studio/src/web/WebBridge.ts` | | ? | | | | | | | | | | | | | ✓ |
| `apps/studio/tests/mock-bridge/*` | | ✓ | | ✓ | | | | ✓ | ✓ | | | ✓ | | | ✓ |
| `apps/desktop/{main,preload}.ts`, `tests/stub-engine.cjs` | | | | | | | | ✓ | ✓ | | | | | | ✓ |
| `docs/specs/ENGINE_PROTOCOL.md` | | ✓ | | | | | | | ✓ | ✓ | | ✓ | | ? | ✓ |
| `docs/specs/protocol.schema.json` + generated files | | ✓ | | | | | | | | ? | | ✓ | | | ✓ |
| `tests/protocol/golden_v0.ndjson` | | ✓ | | | | | | | | | | | | | ✓ |
| `tools/gen_ui_catalogue.py`, `tools/foundation/fixtures/known_module_ids.txt`, `tools/foundation/tests/test_ui_catalogue.py` | | | ? | | ✓ | ✓ | ✓ | | ✓ | | | | | | |
| `bench/{gate,golden,portability,sdk}/*.py` | | | | | ✓ | ✓ | ✓ | | ✓ | | | | | | ✓(device/offline) |
| `bench/offline/repo_facts.py` | (scope) | | | | | | | | ✓ evidence | | | | | | |
| `.github/workflows/*` | | | | | ? | ✓ portability.yml | ✓ | | ? | | | | | | ✓ drift |
| `docs/MODULE_BUILD_GUIDE.md`, `docs/SDK_AUTHOR_GUIDE.md` | | | | | | ✓ | ✓ | | ✓ | | | ✓ | ✓ | | |

The heaviest contention is on `engine2.cpp` (T1.6, TR1, E3, E4, E5, E6) and `session.cpp` (TR1, E3, E6, Dev, PV2–5, T1.5).
`apps/studio/src/engine/*` is edited by TR3, T1.9, E3, E6 and PV4.

## (b) Paths needed by these tasks that active contracts own
| Path | Owner today | Rule |
|---|---|---|
| `native/engine2/`, `native/control/` | M1 r2 S2–S5 (S2 #111 open) | "No other task may edit … while S2–S5 are open." Blocks T1.6, TR1, E3–E6 and MB2 until S5b; S6 then moves both |
| `native/sidecar/` | M1 r2 (S5 only); M2 E1a merged; **PV1 PR #105 adds `native/sidecar/generated/`** | Sidecar tasks merge before S5a opens or wait until S5b. Blocks TR1, E3, E6, Dev, PV2–3, T1.5 |
| `native/document/`, `native/io/`, `native/web/`, `native/tools/render/` | M1 r2 S5a/S5b; Q15 added `native/document/runtime_patch.cpp` and `native/cli/play.cpp` to S2 | Same windows. Blocks TR1 (runtime_patch), TR2 (groove tests, runtime_module_config), E3, T1.6 (`native/web/CMakeLists.txt`) |
| `native/include/wirescape/module2.h` | M1 r2: "not edited in M1" | Blocks E3 and E5 until M1 closes |
| Whole tree | M1 r2 S6 (stop-the-world, moves only) | Every task here starts after S6 or is merged or parked before it |
| `native/modules2/**`, `native/CMakeLists.txt`, `tools/dev.py` | M1 S4 (CMake, `tools/dev.py`) and S6 | MB1/MB2/TR2 after S6 (0009 says so) |
| `apps/studio/` (client, `FakeEngine`, App call sites, tests) | M2 r3 E1b (#125 / PR #130, held; Q14 final packet) | Overlaps TR3, T1.9, E3 Studio, E6 Studio, PV4 |
| `docs/specs/protocol.schema.json`, `tools/protocol/**`, `apps/studio/src/engine/generated/`, `native/sidecar/generated/`, `.github/workflows/protocol-v0-drift.yml`, `facts/code/protocol_disagreements.md` | M2 r3 PV1 (PR #105, open) | PV2–PV5 and TR1's schema edit wait for the merge |
| `docs/specs/ENGINE_PROTOCOL.md` | M2 E1a (merged; additive) | Free now, apart from PV1's generated tables |
| `native/document/runtime_module_config.h` | M2 E0 (merged) and M1 S5a | M1 window applies |
| `.github/workflows/ci.yml` | **CI1 r3: CI1.4 merged, so CI1.3 (#109 / PR #129, `sanitizers` job only) is the sole owner, one open PR at a time** | Any task here that edits `ci.yml` (S6 path filters, MB3, T1.5, PV drift) waits for CI1.3 to merge. PV1's drift check is in its own workflow file, as CI1 allows. Other workflows (`portability.yml`, `golden-renders.yml`, `instruction-gate.yml`, `offline-facts.yml`, `out-of-tree.yml`) are not owned by CI1; they carry `native/**` and `native/modules2/**` path filters that S6 has to change |
| `tools/ci/` | CI1.2/CI1.4 (merged) | Free; `tools/ci/changed_scope.py` classifies paths and must follow S6 (not verified that its rules name `native/`) |

Not verified: whether `start_audio` rebuilds the engine on device select; whether the web target needs TR1, P7 or P8; `tools/ci/changed_scope.py` path rules; the payload layout of `WS2_TRANSPORT_EVENT`.
