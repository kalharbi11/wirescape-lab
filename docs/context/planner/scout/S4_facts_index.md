<!-- SPDX-License-Identifier: GPL-3.0-only -->
# S4 — Facts index (scout)

Lab commit: `11a68c2a2cfea1e34390c5c6a8e20549152afaa3` (git HEAD of the lab repo, read 2026-11-26). Scope: facts/ (about 250 files incl. JSON/CSV; JSON read at summary level only). Facts only. Paths are relative to `facts/`. "CI" = GitHub-hosted runner (Xeon 6975P-C x64, Neoverse-N2 arm64, AMD EPYC/Family 25 Windows). All dates ET.
Note: the repo has `tests/` and `sound/` folders too (index below).

## 1. Index by folder

### top level
| path | date | commit | machine | result |
|---|---|---|---|---|
| README.md | 2026-11-14 | 660556f (L4 coverage table, superseded by CI rows at 7d3842d) | tool container, no checkout | Rules + layout; initial coverage table all "Unmeasured" |
| BASELINE.md | pinned 2026-11-16 | pin 042454d; facts keep own commits | mixed | Phase 0 targets vs observed (10 rows): abi2_poly8 64.2 us x64 / 73.4 us arm64 per 256f; cable drag p95 66.7 ms at 200 modules; 6 core files edited to add a module; out-of-tree build fails at CMake; 70/70 Cortex-M7 compile-only; 24/24 patches render; >=8 core files with module-ID matches |

### app/
| path | date | commit | machine | result |
|---|---|---|---|---|
| app/ci-{linux-x64,linux-arm64,windows-x64}/ui.json | 2026-11-14 | 7d3842d | CI x64 / arm64 / Win, Chromium rAF drags | 200 modules cable drag p95 66.7 / 66.6 / 66.7 ms; 200 modules knob p95 16.8 / 50 / 50 ms; 50-module p95 16.7-33.3 ms; max 99.9 / 233.3 / 150 ms (cable@200) |
| app/ci-*/protocol.json | 2026-11-14 | 7d3842d | CI x3, null-audio | setParam p50/p95 0.05/0.09 ms (x64), 0.11/0.12 (arm64), 0.11/0.14 (Win), n=1000; connect p95 5.75/5.79/5.6 ms; hello 6.6/7.8/25.9 ms; Six_Essentials_Demo loadGraph refused `invalid` on Linux (v1 file), accepted chaos_two on Win |
| app/ci-*/startup.json | 2026-11-14 | 7d3842d | CI x64, arm64 (Win: unavailable) | first paint median 504 ms (x64, max 538), 669 ms (arm64, max 694); engine hello median 84.6 / 99.3 ms; n=10 |
| app/ci-*/memory.json | 2026-11-14 | 7d3842d | CI | engine idle RSS 14300 KiB x64, 13588 KiB arm64; class_demo_1_chaos loaded RSS 19096 / 18028 KiB, loadGraph 23.2 ms; Electron RSS not captured |
| app/six_essentials_protocol_refusal_2026-11-14.md | 2026-11-14 | 7d3842d | CI x3 | v1 demo patch refused `invalid` (sidecar requires version 2) |
| app/ui-attribution-ci-linux-x64-2026-11-15.json | 2026-11-15 | — | CI linux x64 | UI attribution data (not read in detail) |
| app/ui_smoothness_2026-11-17.md | 2026-11-17 | df0e02c | CI linux x64, headless Chromium 131, real Release engine --null-audio | rAF p50 16.7 / p95 16.7-16.8 / max 16.8 ms for knob, module move, cable, telemetry (scene-06, 18 modules); setParam->reply p50 1.8 / p95 3.4 ms (31/31 ACKs); pointer-down to first ACK 18.1 ms |
| app/ui_cpu_rank_2026-11-20.md | 2026-11-20 | cde8602 | CI linux x64, Xeon 6975P-C | idle-only ranking of 24 bundled patches @48k/128 (period 2666.7 us): worst scene-03-black-ice-choir p95 107.0 us (4.01%), best quad-vca-02 p95 12.5 us (0.47%); rAF on winner p95 16.7 ms all four gestures |

### code/ (static readings, no execution unless noted)
| path | date | commit | machine | result |
|---|---|---|---|---|
| code/FACT_PACK.md | 2026-11-14 v0.2 | snapshot 44da1e4 | LLM reading | code readings (engine, protocol, DSP, SDK) |
| code/capability_map.md | 2026-11-14 | cd9a6a5 / 44da1e4 | static | module-ID matches in 8 native files (lower bound) |
| code/edit_paths.md | 2026-11-16 | cacf9ea | GitHub read-only | loadGraph = full replacement; setSampleRate/setBufferFrames restart stream |
| code/out_of_tree_trial.md | 2026-11-14 | a0e37c7 | CI Linux x64 + Windows x64 | 6 core files edited; out-of-tree build fails at step 3 (CMake, missing tests2/allocation_watch.cpp); 2 of 3 out-of-tree steps; null-sink loadGraph of trial.gain accepted |
| code/{abi1_removal_inventory, audit_checks, channel_literals, module_build_registry, module_census, native_v1_readers, protocol_disagreements, protocol_dispositions, protocol_groups, transport_paths}.md | 2026-11-14..16 | mostly 44da1e4 / cd9a6a5 | static | inventories; not read in detail |

### compare/
| path | date | commit | machine | result |
|---|---|---|---|---|
| compare/performance.md | 2026-11-14 | 660556f | desk research | published ARM/Pi audio numbers by other authors (e.g. Pi 5 RP1 TDM 32 frames = 0.667 ms period, nominal not measured) |
| compare/measured/wirescape_limits.md | 2026-11-14 | bb46912 | null-sink probe | limits: 64 modules max, refusal `limit` "Graph capacity exceeded" (96-module probe, 129 connections) |
| compare/{diy_quotes, export_pipelines, features, module_categories, pink_trombone, repo_layouts, sdk_shape, ui_systems}.md | 2026-11-14 | 660556f | desk research | quotes/inventories of other tools; no Wirescape measurements |

### device/results/ (owner-run; see section 2 for Pi detail)
| path | date | commit | machine | result |
|---|---|---|---|---|
| device/results/README.md | 2026-11-14/15 | — | — | index of runs |
| pi5/2026-11-14-cd9a6a5-device-off + device-off-2026-11-14-cd9a6a5.md | 2026-11-14 | cd9a6a5 | Pi 5, null sink | build/tests/app smoke/dry run; compare-null: 11 samples, CPU 0%, RSS max 14.2 MB, 34 module types |
| pi5/2026-11-14-b1d92be-quick | 2026-11-14 | b1d92be (cd9a6a5 + local MIDI patch) | Pi 5, ALSA pulse, 256f, USB audio | 27179 acks, ack p50/p95/p99 0.149/0.250/0.758 ms, CPU max 25.03%, engine dropouts 0, signal dropouts 2, clicks 83 |
| windows-laptop/2026-11-14-cd9a6a5-device-off | 2026-11-14 | cd9a6a5 | owner laptop, null/synthetic | device-off dry run + compare samples |
| windows-laptop/2026-11-15-842d682-validation | 2026-11-15 | 842d682 | owner laptop Win | builds/smoke PASS; null-audio scenario 23874 acks, 0 refusals; initial speaker check FAIL (silence), louder PASS, CPU snapshots 0.37-1.04%; 15-min real run SKIPPED |
| windows-laptop/2026-11-15-156af4b-quick-{128,256} | 2026-11-15 | 156af4b | owner laptop, MME Realtek | 128f: CPU max 63.97%, 22 signal dropouts (0 engine), 152 clicks, 27179 acks; 256f (W1): CPU max 81.46%, 25 engine dropouts, 154 clicks |
| 2026-11-15-device-session.md, 2026-11-15-pi-pulse-reruns.md | 2026-11-15 | ab7ce36 (Pi), 156af4b (Win) | Pi 5 + Win laptop | session summary tables (see section 2); original default-route Pi runs all failed (Sample format not supported / event queue full) |

### dsp/
| path | date | commit | machine | result |
|---|---|---|---|---|
| dsp/ci-*/{bundled_patches,envelopes,filters,module_outputs,oscillators,parameter_steps}.json, golden.json (linux-x64, linux-arm64, windows-x64) | 2026-11-14/15 | 7d3842d / 919f047 | CI x3 | offline sound measurements; golden fixtures per platform (Windows ci dir has only `unavailable.json`) |
| dsp/coverage/ | 2026-11-15 | 919f047 | CI x3, run 43785858733 | 24 bundled + 3 coverage fixtures render on all three platforms; module interventions 28/34 observed |
| dsp/m4_r2_verified_measurements_2026-11-16.json, ci-*/m4_verified_measurements | 2026-11-16 | PR #60 head 7ed7c54 | CI x64, arm64, 44.1/48/96k, 128f | 36 module/rate cases per metric; zero impulse NaN/Inf, zero tail nonfinite/subnormal/fault; ringmod2 3 cases not_built, 69 not_applicable |
| dsp/abi1_t11_capture_linux_{x64,arm64}_2026-11-15.json | 2026-11-15 | — | CI | ABI1 capture (not read in detail) |
| dsp/edit_continuity.{md,json} | 2026-11-16 | 4b6a45a | cloud Xeon 2.1 GHz, null sink, 48k/256f, 3 repeats | addModule/removeModule/connect: tone silence 0.02-0.04 ms, tail 47.1 ms; loadGraph identical: tone silence 6.04 ms, restarted=True |
| dsp/applygraph_continuity_measured.{md,json}, _pending.md | 2026-11-17 | 8eb7898 | hosted ubuntu-24.04, run 44031958143, 48k/256f | applyGraph identical: tone silence 0.0208 ms, tail 47.1 ms, subject restarted=False; 45 rows, 0 unsupported |
| dsp/m7_t7_0_baseline.json | 2026-11-17 | 1b36751 | hosted x64 + arm64 directional | M7 T7.0 baseline: 24/24 CHAOS and 4/4 stepped switch rows |
| dsp/t7_0b_switch_rows_2026-11-21.md | 2026-11-21 | 1a5dd85 | hosted device-off | paired switch/no-switch rows, 5 fixtures (incl. clocked Delay division); "before" observations for M7 r1.3 |

### perf/
| path | date | commit | machine | result |
|---|---|---|---|---|
| perf/ci-{x64,arm64}/engine_cpu.json | 2026-11-14 | 7d3842d | CI x64 Xeon / arm64, 48k/256f | mean ns: abi2_mono 8314/9467, abi2_poly8 64241/73384, abi2_eight_mono 65535/75957, abi2_modulated 14197/19403, vcf_constant 4687/5132 (x64/arm64) |
| perf/ci-*/instruction_cost.json | 2026-11-14 | 7d3842d | CI (callgrind) | Ir/block x64 / arm64: abi2_mono 64143/65138; abi2_poly8 487122/499950; quad_vca_lpg8 1484468/1445992 |
| perf/ci-*/module_cpu.json | 2026-11-14 | 7d3842d | CI x64, arm64 | 198 rows: 192 measured, 6 unavailable (Chord, probe passes no 4-byte config); 0 allocations, 0 faults |
| perf/ci-*/patch_soak.json | 2026-11-14 | 7d3842d | CI x64, arm64 | 72 rows: 36 measured, 36 unavailable (12 host.keyboard patches, exit 1, 1 s/patch) |
| perf/ci-*/denormal_spikes.json | 2026-11-14 | 7d3842d | CI | 33 rows all unavailable (probe cannot inject 1e-30 input) |
| perf/ci-windows-x64/unavailable.json | 2026-11-14 | 7d3842d | CI Win | perf collectors unavailable on Windows |
| perf/{linux-x64,linux-arm64}/instruction_baseline.json | 2026-11-14/15 | — | CI | 97-row instruction-cost baseline (2 Chord rows unavailable per BASELINE.md) |
| perf/offline_failure_evidence_2026-11-14.{md,json} | 2026-11-15 | 7d3842d (run 43675998104) | CI x64 | explains the 36 unavailable soak rows + 6 Chord rows |
| perf/offline_30s_ci_2026-11-15.json | 2026-11-15 | cfdd377 (run 43745119473) | CI x64 Xeon 8573C, arm64 | 30 s per patch/block, 72 rows/runner all measured (clock->step_sequencer source for keyboard patches); allocations 0, faults 0; late deadlines total x64=2, arm64=0 |
| perf/abi1_mono_final.md | 2026-11-17 | 309bf88 (S3) | CI x64/arm64/Win | abi1_mono @256f mean 10092 ns (x64), 10932 (arm64), 10291 (Win); Ir/block 87890 x64, 79168 arm64 |
| perf/ob_g1_linux_l0_advisory_2026-11-21.md | 2026-11-21 | base 2344369 | Python sandbox, no engine | OSC soak L0 BLOCKED / NOT RUN; no numbers |

### repo/
| path | date | commit | machine | result |
|---|---|---|---|---|
| repo/ci-{x64,arm64,windows-x64}/*.csv, repo.json, table_inventory.json | 2026-11-14 | 7d3842d | CI x3 | LOC by group/file (native product C++ 131 files, 21847 code lines in x64 loc_by_group), complexity/length top30, binary_sizes (e.g. libwirescape_engine.so 39472 B), dependencies, includes, residue |
| repo/cortex-m7/ | 2026-11-15 | 9d04963 | CI arm-none-eabi-g++ 14.2.1 | 70/70 compile-only (34 modules + 1 template, 2 FPU targets), .text/.data/.bss per module; heap refs column |
| repo/github_tree_inventory.json | 2026-11-14 | 660556f | GitHub tree API | tree metadata |

### sound/ and tests/
| path | date | commit | machine | result |
|---|---|---|---|---|
| sound/ob_d_patches.md | 2026-11-25 | OB0 a440d71 + PR heads | CI Linux x64 Golden | per-stage bundled-patch sound-change ledger (hashes, RMS delta); owner listening pending |
| tests/ci-*/{run_manifest,tests}.json | 2026-11-14 | 7d3842d | CI x3 | test inventory/runtimes |
| tests/ci_durations.md | 2026-11-14 | 0a58849 | CI | job minutes: linux-x64 4.68, linux-arm64 4.52, windows 5.48, sanitizers 9.58, studio 10.32 |
| tests/ci_durations_2026-11-16{,_ci1,_ci1_3}.md, ci_durations_2026-11-17_ci1_k8.md | 2026-11-16/17 | 320576c; 309bf88 (PR #159) | CI | job/step durations; sanitizer measurement (run 44028971243) |

## 2. Pi 5 measurements (real Raspberry Pi 5)
All owner-run, ALSA `pulse` desktop route to USB output (not exclusive hardware access). Sources: `device/results/2026-11-15-pi-pulse-reruns.md`, `device/results/2026-11-15-device-session.md`, `device/results/pi5/*`.
- 2026-11-14 b1d92be quick (256f): CPU max 25.03%, ack p95 0.250 ms, 27179 acks, 0 engine dropouts, 2 signal dropouts, 83 clicks. `device/results/pi5/2026-11-14-b1d92be-quick/report.md`.
- 2026-11-14 cd9a6a5 device-off null sink: CPU 0%, RSS max 14.2 MB. `device/results/pi5/2026-11-14-cd9a6a5-device-off/compare-null/report.md`.
- 2026-11-15 ab7ce36 reruns (P1-P4): P1 256f 59.990 min CPU max 26.19%, 0 engine dropouts, 10 signal candidates, 276 clicks, longest silence candidate 1110.7 ms; P2 128f 59.988 min CPU max 26.98%, 10 signal candidates, 270 clicks, silence candidate 1114.8 ms; P3 scene 0.583 min CPU 13.02%, 0 candidates; P3 chaos 0.583 min CPU 14.50%; P4 64f 0.583 min CPU 3.22%. Scenarios change buffer sizes internally, so not sustained at fixed buffer. Same dir, `*-full-128-pulse` etc.
- Same day, first (default-route) attempts P1-P4 all failed in ~0.2 min (Sample format not supported, event queue full); manifests in `pi5/2026-11-15-ab7ce36-{full-128,full-256,scene-128,chaos-128,basics-64}/` show CPU 0.0, no metrics.
- GUTTR benchmark (30000 blocks, 48k/128f, period 2666.667 us): 1 throat p50/p95/worst 44.594/46.483/73.873 us; 16 throats 346.249/352.620/440.047 us. `device/results/pi5/2026-11-15-ab7ce36-guttr/guttr-benchmark-pi5.jsonl`.
- Pi health during rerun log: max temp 59.3 C, throttle flags 0x0, max used memory 1862 MB (earlier session: 51.0 C, 1772 MB). `.../pi-health.log`.
- App memory (ARM64 Electron smoke, 5413 samples, engine seen in 1): Electron peak 444.39 MiB, engine peak 231.47 MiB; not sustained. `.../ab7ce36-app-memory/memory-summary.json`.
- Owner remark at P1: pop at beginning ("like plugging in an aux"). Loopback cable: not checked, so command-to-sound latency is device-only/unmeasured.
- No Pi 5 data in `perf/`, `dsp/`, `app/` (those are CI). No Pi OSC/MIDI soak, no Pi 100-edit acceptance, no Pi denormal/long-silence CPU.

## 3. Endurance / soak
- Pi 5 60-min P1/P2 (above): completed, exit 0, 0 engine dropouts, 10 signal candidates each. This is audio-route endurance only.
- Windows laptop: W1 256f 15 min planned (14.98 recorded): 25 engine dropouts, 18 signal candidates, 154 clicks, CPU max 81.46%; W2 128f 14.99 min: 0 engine dropouts, 22 candidates, 152 clicks, CPU max 63.97%. `device/results/2026-11-15-device-session.md`. 15-min run on 842d682 skipped.
- Offline patch soak (device-free, no audio): 30 s per patch x blocks 64/128/256, 24 patches, 72 rows per runner, all measured, 0 allocations, 0 faults; late deadlines x64 2, arm64 0. `perf/offline_30s_ci_2026-11-15.json`. Earlier 1 s run: 36/72 rows failed per runner. `perf/offline_failure_evidence_2026-11-14.md`.
- OSC soak: none. `perf/ob_g1_linux_l0_advisory_2026-11-21.md` is BLOCKED/NOT RUN (no engine binary); 60 s osc-gates/still L0 not performed; no packet counts, no drop counts.
- MIDI soak: none in facts/ (MIDI queue counters await OB-g2 per same file).
- I/O endurance (OB-g) hosted soaks: no result files in facts/; ob-g7 nightly parked per proposals/0022 line 31.
- Native-protocol stress: 27179-ack scenario on Pi/Win; 23874-ack null-audio scenario on Windows validation (0 refusals).

## 4. UI performance
- CI rAF (7d3842d, 2026-11-14), `app/ci-*/ui.json`: 50/100/200 modules, knob and cable: x64 cable@200 p95 66.7 ms (max 99.9), knob@200 p95 16.8; arm64 knob@200 p95 50, cable@200 p95 66.6 (max 233.3); Win knob@200 p95 50, cable@200 66.7 (max 150). 50-module cases 16.7-33.3 ms.
- OB-f1 (df0e02c, 2026-11-17), `app/ui_smoothness_2026-11-17.md`: scene-06 (18 modules): all four gestures p95 <=16.8 ms; telemetry 40 messages; setParam ACK p50 1.8/p95 3.4 ms (bridge included).
- OB-f1 rerun (cde8602, 2026-11-20), `app/ui_cpu_rank_2026-11-20.md`: scene-03 winner, same rAF p95 16.7 ms.
- Startup: first paint median 504 ms (x64) / 669 ms (arm64); hello 85 / 99 ms. Protocol latencies in app table above.
- All headless Chromium on hosted CI; no Pi or real-GPU UI measurement.

## 5. Engine CPU / DSP cost
- Per patch (offline, 48k/256f, CI 7d3842d): poly8 64.2 us x64 / 73.4 us arm64 mean; p99 82.6/76.3 us; vcf 4.7/5.1 us. `perf/ci-*/engine_cpu.json`.
- Per patch, 24 bundled @48k/128f, p95 render: 12.5 us to 107.0 us (0.47% to 4.01% of 2666.7 us); top: scene-03 107.0, chaos-01 105.4, scene-05 96.8 us. Idle only, one observation per patch. `app/ui_cpu_rank_2026-11-20.md`.
- Instruction counts: `perf/ci-*/instruction_cost.json`, `perf/*/instruction_baseline.json` (97 rows), ABI1 final `perf/abi1_mono_final.md`.
- Per module: `perf/ci-*/module_cpu.json` (192 measured per arch; Chord unavailable); `dsp/ci-*/m4_verified_measurements` (36 cases/metric, no NaN/subnormal).
- Pi 5 engine CPU: 3.2% (64f) to 27.0% (128f) max over windows; GUTTR 16 throats 346 us p50 of 2667 us period.
- Cortex-M7 size/compile: `repo/cortex-m7/` (compile-only; no execution).
- Denormal/long-silence CPU: unavailable (33 rows).

## 6. Missing / not present in facts/
- CMP-1 benchmarks: no CMP-1 file in facts/ (grep "CMP-1" matches only docs/workflow: CURRENT.md:36,75, OB.md:90, OB_PLAN.md:26, BUILDERS.md:40, ARCHITECT_INBOX.md:43). Task #589/#592: measured rebuild vs previous engine, paired same-job runs, import pin 44da1e4; route ruling A89 (workflow-only bootstrap PR, pinned dispatch, then facts on #592); #593 inbox-only.
- Pi acceptance: docs/workflow/OB_PLAN.md:46 requires owner Pi session with 100 edits at the owner's buffer size, zero xruns, no visible stutter, plus both CN cost rows and OB-f1 recheck; none exists. ROADMAP.md:9,52: Pi testing, PI-1 #369 and Pi soaks postponed to candidate.
- OSC soak: OB_PLAN.md:22 "No hosted osc-heavy result since #394/#433; nightly parked"; findings #326 (stuck gate), #494/A67 (enqueue refusals 2 Windows, 39/129 Linux) have no facts file. proposals/0022 line 139: OSC soak L3+ (4-12 h) on the Pi, CPU during long silence (denormals), none measured.
- OB_PLAN.md:106: wall-time "remains unmeasured" until actual (B1 A10 proof).
- Fixed-128-frame sustained 60-min heaviest-patch worst block time on Pi: device-only, absent (BASELINE.md).
- Command-to-sound / loopback latency: device-only, absent. Isolated live-edit audible gap on physical audio: absent.
- No Windows CI perf/dsp numbers (`unavailable.json`); no Windows startup; no Electron CI RSS.
- Active (sounding) per-patch CPU: stated unresolved in ui_cpu_rank (idle-only).
- No facts for OB-d owner listening (pending), OB-a2 real patch folder, install.
Signed: scout (Sonnet), 2026-11-26
