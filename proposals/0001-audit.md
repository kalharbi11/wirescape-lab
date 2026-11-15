<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0001 — Audit of Wirescape at the snapshot

**Author:** Fable · **Date:** 2026-11-15 (ET) · **Lab commit read:** `7b334e5` · **Status:** for the owner

This is a judgement of the app, so it lives in `proposals/`. Every finding names the fact file it rests
on. Numbers are from hosted CI (lab `7d3842d`, 48 kHz) and from the two owner device runs filed so far.
**The Pi 60-minute run, the Windows 15-minute run and the cross-tool runs had not landed when this was
written** (`facts/device/results/` holds four folders, none of them those), so the performance section
is provisional. The plan built on this audit is `proposals/0002-plan.md`.

How it was produced: I read the context docs and FACT_PACK §0–§2 myself; five subagents digested the rest
of `facts/`; I re-checked the numbers quoted below against the JSON and the two code points marked
"checked" against the source. Code readings in `facts/code/FACT_PACK.md` are LLM readings of the source,
not executions; where a finding rests only on a reading it says "reading".

## Summary

| Area | Verdict | Biggest item |
|---|---|---|
| Engine core | Sound design, healthy realtime path, carrying a second engine | ABI1 is linked into every build and typed into every interface |
| Live editing | The mechanism exists but most edits bypass it | Config edits, undo, restore and every modulation-amount step rebuild the graph |
| Sound quality | Uneven, and barely measured | Cable modulation is unsmoothed; CHAOS oscillators are naive; no module is oversampled |
| Performance | Engine is cheap; the app around it is not measured where it matters | Electron tree ≈ 700–775 MiB vs engine 14–19 MiB; no Pi long run yet |
| Module authoring | The class format is short; everything around it is not | 6 core-file edits per module; out-of-tree build fails at configure |
| Portability | Claimed, not demonstrated | No Daisy/plugin adapter exists; the Cortex-M7 compile check is parked |
| Protocol and app | Works; drifted from its spec; three copies of patch logic | ~35 spec/implementation mismatches; `v: 0` |
| Module UIs | Generic and tidy, closed to extension | New pane kinds need edits in three TypeScript places; no per-module UI package |
| Measurement | Good skeleton, holes in the important places | Half the patch soaks, all denormal probes and all Windows DSP/perf are "unavailable" |

## 1. Engine core

**What is good.** The render path was read as free of allocation, locks, syscalls and logging
(FACT_PACK §A3.2, reading), and the measurements agree: 0 allocations and 0 page faults in every module
CPU row and every soak row (`facts/perf/ci-linux-*/module_cpu.json`, `patch_soak.json`). Denormals are
flushed for the whole render call on x64 and AArch64 (X1). Release events have a reserved budget and a
priority ring (R6). Panic is two atomics (X10). The scheduler (SCCs with explicit feedback delay) is
deterministic. Engine overhead is small: an 8-voice graph costs 64 µs mean per 256-frame block on x64
CI and 73 µs on arm64 CI, 1.2–1.4 % of the period (`engine_cpu.json`, `abi2_poly8`).

**What is wrong.**
- **Two engines in one binary.** The ABI1 library is linked by 18 CMake targets, the sidecar among them
  (through `wirescape_app_engine`; `facts/repo/ci-linux-x64/cmake-targets.csv`). Every `AppEngine`,
  including each patch load, creates an ABI1 engine it never uses (RESIDUE §1; FACT_PACK Part A item A2).
  The scheduler carries about 15 ABI1 branches (RESIDUE §1; 37 `legacy` mentions in `engine2.cpp`,
  checked). The catalogue, the patch loader's port and parameter lookup, the engine config type and the
  host-event type are all ABI1 structs. 789 ABI1 symbol references remain in the tree
  (`residue_by_file.csv`). ABI1 itself measures no faster or slower in a way that matters (7.5 µs vs
  8.3 µs mono per block, x64), so nothing of value is kept by it.
- **`legacy_index` is a live hazard, not only residue.** Saved parameter values are applied through the
  ABI1 numeric id, first match wins; two parameters sharing a `legacy_index` (the helper's default is 0)
  would silently misroute (X15). A new module author hits this by default.
- **Module-specific code in the core.** `runtime_module_config.h` is one 375-line function with
  cyclomatic complexity 223, holding config adapters for chord, groove, osc_in, osc_out and midi_cc_to_cv
  (`complexity_top30.csv`; `facts/code/capability_map.md` §3). Telemetry taps, MIDI ingress, OSC buses and
  pitch handling are keyed on module IDs inside `engine2.cpp`, `telemetry_taps.h`, `midi_host.cpp` and
  `session.cpp`. A new module of the same kind cannot get these services without editing the core.
- **Transport is not connected.** Nothing calls `Engine::transport()`; every module sees 120 BPM, playing,
  4/4 (X8, reading). LFO sync locks to a tempo the user cannot set; Groove keeps its own.
- **Each module instance is created twice on load** (`add_node` runs setup, `prepare` runs it again;
  A-Q8, reading). Per-event packets are ~1.6 KiB and copied several times (A-Q27, reading; cost unmeasured).
- **Code shape.** `process_node` has complexity 135 in 178 lines; `Session::apply` is 320 lines; 220
  native lines exceed 200 characters (`complexity_top30.csv`, `native_long_lines.csv`). The core is hard
  to review, which matters more than style: it is where the realtime guarantees live.
- **Small defects found in readings:** `route` returns `routed?okay:okay` (§1.3); non-atomic latency fields
  are written while render runs (X7); a NaN in recursive module state silences that module until a reset
  (X6); `setup` leaves `pitch.enabled` out of replan carry-over (A-Q7).

**Settled during the audit (checked in source):** the SDK wrapper calls `reset()` after `prepare()`
(`native/sdk/wirescape_sdk.h:205`), so X5's worry about reverb and four other modules starting from
uninitialised memory does not apply. Recorded in `facts/code/audit_checks.md`.

## 2. Live editing (KNOWN_ISSUES A2)

The engine has a real live path: parameters are events, and `replan` swaps topology in a one-block fade
while keeping the instances of unchanged modules. Measured: `setParam` p99 0.10–0.16 ms; connect and
disconnect p50 5.3–5.5 ms, which is one 256-frame block (`facts/app/ci-*/protocol.json`).

The restart behaviour comes from four separate causes, and they need different fixes:

1. **A module whose config bytes changed is treated as a new module** by `replan`, with no state carried
   (§A4.2). The call that does carry state, `reconfigure`, only works while audio is stopped.
2. **Too much is "config".** Groove steps, length and tempo, CC map rows and OSC rows are config blobs, so
   editing musical data is a structural edit.
3. **The UI sends whole documents.** `loadGraph` always takes the stop-swap-fade path and resets the ID
   namespace, MIDI worker, OSC hosts and keyboard state (B §A11, SE:704-847). Studio sends it for undo,
   redo, snapshot restore and whenever it is unsure of engine state (KNOWN_ISSUES; RE:377-386).
4. **Modulation amount is a topology edit.** Each drag step of a modulation depth builds a candidate
   engine (S:114; reading).

Related gaps: a buffer-size change produced 546 ms of silence and a panic 306 ms on the Pi
(`facts/device/results/pi5/2026-11-14-b1d92be-quick/review.json`); the documented swap gap budget is
150 ms. The client has one edit in flight at a time, drops queued edits on a session change without
rollback, and has a race where a load can discard an unsent edit (B-Q17, B-Q18, readings).

No test measures audio continuity across an edit. Until one exists, "never restarts" cannot be verified.

## 3. Sound quality

Measured so far (`facts/dsp/ci-linux-*`, 48 kHz only; x64 and arm64 agree to float noise):

| Item | Number | File |
|---|---|---|
| VCO sine non-harmonic floor | −121.9 dBFS at 110–5000 Hz | `oscillators.json` |
| ADSR timing | attack 45 ms for 50 ms set; release 90 ms for 100 ms set | `envelopes.json` |
| VCF passband loss with resonance | −8.6 dB at res 0.5, −12.1 dB at res 0.9 | `filters.json` |
| Ladder resonance peak position | 527 Hz for a 1000 Hz cutoff at res 0.9; 2848 Hz for 5000 Hz | `filters.json` |
| Output above full scale, single module | resonator 1.046, reverb 1.099 | `module_outputs.json` |
| Bundled patches | peak 0.08–0.89, no clipping, no non-finite samples | `bundled_patches.json` |
| Pi 15-minute run | 8,652 samples at full scale, 83 click-like flags (heuristic) | `review.json` |

Findings (code readings unless a file is named):
- **Modulation is unsmoothed by design.** Base parameter changes ramp 5 ms; cable modulation and
  PARAM_MOD are added per sample with no smoothing (X2). Modules then differ: seven smooth again with
  `PortRamp`, most do nothing. MIDI CC through `midi_to_cv` is 7-bit and unsmoothed.
- **Aliasing.** VCO and LFO are sine only, so the clean number above says little. CHAOS uses naive saw
  and square with no band-limiting and is not in the oscillator measurement. No saturator (Ladder tanh,
  delay tanh, reverb clamp, soft clips) is oversampled.
- **Clicks.** CHOKE drops ADSR to zero instantly; VCO resets phase on CHOKE; Quad VCA mode switch is
  instant; delay tone bypass and reverb parameters are unsmoothed; the reverb's wet makeup (+15.6 dB)
  runs into a hard ±2 clamp.
- **Filters.** VCF loses up to 12 dB of passband with resonance and cannot self-oscillate (k ≤ 3.2). The
  Ladder's resonant peak sits well below the cutoff and moves with sample rate, the expected result of
  its one-sample feedback delay.
- **Sample-rate dependence.** Macro Oscillator refuses any rate but 48 kHz. Reverb constants, DC-blocker
  corners and LFO depth are not rate-scaled. Nothing is measured at 44.1 or 96 kHz.
- **NaN policy differs per module**; several recursive modules hold a NaN until reset.
- **Envelope timing is 10 % short** in the one case measured.

What cannot be said yet: aliasing of anything but a sine and Plaits; zipper noise with a baseline (the
step test's two largest values, noise.level 1.55 and vco.frequency 1.04, are the signal changing, not
zipper); click counts (the bundled-patch click metric reports up to 211,295 "outliers" on smooth tonal
patches, so it is not measuring clicks); denormal behaviour (all 33 probes unavailable); anything on
Windows.

## 4. Performance and footprint

- **Engine:** heaviest bundled patch that ran, `scene-05`, median 174 µs / max 222 µs per 256-frame block
  on x64 CI (4.2 % of the period), 208 / 240 µs on arm64 CI (4.5 %) (`patch_soak.json`). On the Pi 5 at
  48 kHz / 256 frames over USB audio the 15-minute scripted run reported engine CPU max 25 %, 0 dropouts,
  ack p99 0.76 ms (`review.json`). Costliest modules per sample, 1 voice, x64: spectral 244 ns, CHAOS
  160 ns, reverb 122 ns (`module_cpu.json`, p99, one run).
- **App:** launch to first paint 504 ms (x64 CI) and 669 ms (arm64 CI); Electron process tree 700–800 MiB;
  engine process 14–19 MiB (`facts/app/ci-*/startup.json`, `memory.json`). The shell is 40–50× the engine.
  Not measured on the Pi itself.
- **UI:** dragging a cable at 200 modules: p95 67 ms per frame on all three CI machines, max 100–233 ms;
  knob drag at 200 modules p95 50 ms on arm64 and Windows CI (`ui.json`). The 64-module patch limit
  hides this today.
- **Limits:** 64 modules and 128 connections per patch; a 16-voice poly graph of the test shape needs 96
  modules and is refused (`facts/compare/measured/wirescape_limits.md`).
- **Other tools:** no like-for-like numbers exist (`facts/compare/performance.md` says so itself). The
  nearest published Pi 5 figures are round-trip latencies of 3.6–6.5 ms at 64 frames and 6.3–10.1 ms at
  128 frames with ALSA. Wirescape has no round-trip measurement and runs at 256 by default.

There is no evidence that the stdio JSON protocol or the two-process design costs anything audible:
parameter latency is a tenth of a millisecond. The cost of the current design is memory and startup, both
Electron's.

## 5. Module authoring and portability

- The module class itself is short: the template is 22 lines, VCA's `dsp.h` 34 (FACT_PACK §D1.7).
- Around it: `module.json` repeats the C++ descriptor by hand with no consistency check; a new in-tree
  module edits 5 registration files plus the patch guide (`docs/MODULE_BUILD_GUIDE.md`); existing modules
  also appear in `FakeEngine.ts`, `panels/index.json` and others.
- **The out-of-tree route does not work.** The documented CMake snippet fails at configure on Linux and
  Windows (`Cannot find source file: ../../tests2/allocation_watch.cpp`), and the SDK folder does not
  contain `module2.h`, which it includes (`facts/code/out_of_tree_trial.md`).
- There is no loader for ABI 2 shared libraries in the product; modules are a compiled-in list (X16).
- There is no checker. Errors for a wrong module are `WS2_INVALID` return codes.
- **Portability is unproven.** No Daisy or plugin adapter exists. The workflow that compiled every module
  for Cortex-M7 is parked in `ci/from-main/portability.yml`. The ABI uses `double` and `size_t` in its
  structs; the SDK scans every output sample for non-finite values; a firmware host would need its own
  smoothing, modulation and scheduling because those live in the GPL engine, not the MIT SDK (FACT_PACK
  §D3, §D6).
- **GUTTR shows the category gaps** (`docs/context/future_modules/guttur/`): it keeps its own voice
  handling because host voice stealing would break its groups; it builds 17×8 tables itself in `prepare`;
  it runs a private 128-frame control clock; it has no way to publish per-voice telemetry; its worst block
  at 16 throats is 2,261 µs against a 2,667 µs period on an x86 container, above the 1,333 µs target for
  heavy modules, with no Pi number.

## 6. Protocol and app structure

- The protocol is still `v: 0`. Part B lists about 35 places where sidecar, Studio or Electron main differ
  from `ENGINE_PROTOCOL.md`, including missing client methods (`ccMap.set`, `setOsc`), refusals the client
  silently drops because they carry no session, and no heartbeat for a hung engine.
- Patch validation exists in Electron main, in the sidecar and in `runtime_patch`, beside Studio's own
  document model; the WASM build keeps a hand-mirrored copy of the sidecar's execution function
  (`native/web/DESIGN.md`).
- The control thread does device enumeration, stream restarts and file writes; while one blocks, no status
  or command runs (§B5c, reading).
- Tests: 108 CTest, 207 Python, 344 Studio Playwright, 24 desktop Playwright. Studio's suite takes
  385–545 s and is the longest CI job (10.3 min). **On Windows CI, CTest (exit 8) and desktop Playwright
  failed at `7d3842d`** with no detail recorded (`facts/tests/ci-windows-x64/tests.json`).

## 7. Module UI

Studio builds every panel from the catalogue descriptor plus an optional JSON override; `PanelBuilder.ts`
has no module-specific code. That is a good base. The limits: pane kinds are a closed TypeScript union
(a new one edits three places); Groove's editor is 1,098 lines wired through `App.ts`; OSC editors are
special-cased in `ModuleCard.ts`; a module folder cannot carry its own UI. Nothing like a VCV panel or a
plugin WebView editor can be added without editing Studio.

## 8. Holes in the facts

| Hole | Evidence |
|---|---|
| 12 of 24 bundled patches fail in the soak ("process exit nonzero"), incl. basics-01/02/03/06/07 | `patch_soak.json` |
| Soaks are 1 second long | same |
| Denormal probes: 33 of 33 unavailable | `denormal_spikes.json` |
| Windows: no DSP, perf, startup or memory facts; CTest and desktop tests failing | `ci-windows-x64/` |
| Chord has no CPU data; `Six_Essentials_Demo.json` is rejected as invalid | `module_cpu.json`, `protocol.json` |
| Click metric invalid; zipper metric has no baseline | `bundled_patches.json`, `parameter_steps.json` |
| No measurement at 44.1 / 96 kHz, no CHAOS aliasing, no filter self-oscillation or cutoff error | `facts/dsp/` |
| No round-trip latency, no Pi memory, no Pi run longer than 15 min | `facts/device/` |
| No audio-continuity-across-edit test; no golden render of the bundled patches at the lab commit | — |
| `facts/README.md` still lists everything as unmeasured | fixed in this PR with a pointer |

The first item matters most: the Fixed constraint "bundled patches keep sounding the same" cannot be
enforced by a harness that cannot render half of them.

Signed: Fable, 2026-11-15
