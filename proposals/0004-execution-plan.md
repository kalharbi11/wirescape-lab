<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0004 — Execution plan: tasks, owners and what can run without Fable

**Author:** Fable · **Date:** 2026-11-15 (ET) · **Status:** live; Fable edits it, others read it.
Phases and goals: `0002`. Module design: `0003`. This file is the task list a new Fable session or a Codex
lead works from.

## Name
The rebuilt engine is **Wire** (the owner's name, 2026-11-15; changeable until
task T1.4 lands). "Wirescape" stays the product. Use: *Wire engine* (`wire/engine`), *Wire modules*,
*Wire module API* (formerly "module API v3"; `0003`), header `wire/module.h`, tool `wirescape module …`.
ABI1, "ABI 2", `engine2`, `modules2` and Qt are the experiments that came before.

## Who may do what
| Class | Meaning |
|---|---|
| **A** | Safe without Fable. Touches only `bench/`, `facts/`, advisory workflows under `.github/workflows/`, `docs/context/LOG.md`. A Codex lead may assign it, review it against its issue and **merge on green CI**. |
| **B** | A builder may build it from a written issue; **only Fable merges** (it touches the product tree). A Codex lead may assign it and check CI, then leave it labelled `status/review`. |
| **C** | Fable only (engine design, realtime code, protocol, module API, proposals, CONSTRAINTS, AGENTS/CLAUDE). |

A/B/C classify task *risk*. **Merge authority is set per task by the accepted active milestone
contract in `docs/workflow/milestones/`; without an accepted contract, the table above applies.**
A contract may delegate eligible work to the lead but cannot override the owner's Fixed constraints
or Fable-reserved architecture and measurement decisions.

Rules for every task: one issue, one PR, `Closes #n`; main stays green; the golden render gate (#47/#55)
shows 24 identical unless the PR declares a sound change; no force-push; devices off.

## Phase 0 — measurement floor
| ID | Task | Class | Issue | Depends | Done when |
|---|---|---|---|---|---|
| T0.1 | Offline soak repair, 30 s soaks | A | #41 (PR #48) | — | 72 soak rows measured or specifically explained |
| T0.2 | Windows facts collection | A | #42 ✔ merged | — | publish the hosted facts into `facts/` (run facts workflow on main) |
| T0.3 | Golden renders | A | #43 ✔ merged | — | — |
| T0.4 | Golden gate: base vs head in one job, declared sound changes | A | #55 | T0.3 | no-op native PR shows 24 identical on 3 platforms |
| T0.5 | Sound metrics (clicks, zipper, aliasing, rates, denormals, filters) | A | #51 | T0.1 | regenerated DSP facts, each metric unit-tested |
| T0.6 | Instruction-count gate | A | #52 | T0.4 | baseline committed, deliberate slowdown trips it |
| T0.7 | Cortex-M7 compile facts | A | #53 | — | table for all 34 modules |
| T0.8 | Round-trip latency tool | A | #54 | — | unit-tested, runbook step written |
| T0.9 | File Codex device results (Pi, Windows) | A | results PR | runs done | small files in `facts/device/results/`, README rows |
| T0.10 | `facts/BASELINE.md`: one table, every target row of `0002` with its current number and source file | A | to file | T0.1–T0.9 | every row filled or marked device-only |
| T0.11 | Coverage patches: one small patch per module and per module pair that no bundled patch exercises, under `bench/patches/coverage/`, added to the golden set | A | to file | T0.4 | each of 34 modules appears in ≥1 rendered patch with non-silent output |
| T0.12 | UI frame-time profile at 50/100/200 modules: where the time goes (facts only) | A | to file | — | profile summary in `facts/app/` |
| T0.13 | Edit-continuity harness: capture engine output while applying each edit kind; report phase reset, silence, largest jump | C (design), then B | — | T0.4 | table for every edit in KNOWN_ISSUES A2 |
| T0.14 | Local native build in the cloud container (dependency download blocked) | owner | — | — | `python tools/dev.py build --headless` works for Fable |

## Phase 1 — one engine (Wire)
| ID | Task | Class | Depends | Done when |
|---|---|---|---|---|
| T1.1 | Freeze ABI1 reference data: run the ABI1-vs-ABI2 comparison tests once, store their expected outputs as data files the ABI2 tests read | B | T0.4 | comparison tests pass without linking the ABI1 library |
| T1.2 | Delete ABI1: `native/src`, `native/modules`, `native/tests` (ABI1), provider bridge, fixture, ABI1 headers; remove the shim branches in the scheduler | C | T1.1 | golden identical; instruction counts not worse; no target links `wirescape_engine` |
| T1.3 | Engine-native types: replace `ws_engine_config`, `ws_event`, `ws_meter`, ABI1 descriptor structs in facade, loader, sidecar, web, tools; engine reads patch v2 only; parameter lookup by string ID (no `legacy_index` in loader paths) | C | T1.2 | golden identical; v1 import only in Studio |
| T1.4 | Rename and layout to the `0002` tree with Wire names; no behaviour change | B (mechanical, one PR, Fable reviews) | T1.3 | golden identical; all CI green |
| T1.5 | Residue sweep: Qt wording, dead options, issue numbers and agent names in comments, stale docs | B | T1.4 | `residue_by_file.csv` counts for Qt/issue refs/agent names at 0 in product code |
| T1.6 | Format the core; split `process_node`, `Session::apply`, the config adapter into reviewable units | C (Opus subagent drafts, Fable reviews) | T1.3 | no function over complexity 40 in engine/host; golden identical |
| T1.7 | Transport connected: tempo and play/stop from the app reach modules | C | T1.3 | LFO sync follows a tempo set over the protocol; test |
| T1.8 | Each module its own library target; generated registry replaces the hand lists; drop a folder in → it builds and appears | C design, B build | T1.4 | adding the template module edits 0 files outside its folder |
| T1.9 | "Reload engine" action in the app (developer loop level 1) | B | T1.8 | engine restarts and reloads the open patch; UI stays |
| T1.10 | Owner checkpoint: Pi run by Codex + owner listens | owner | T1.2–T1.7 | owner confirms by ear |

## Phase 2 — edits never restart (design first)
| ID | Task | Class | Depends |
|---|---|---|---|
| T2.0 | Design note `0005`: edit operations, state-carrying replace, module data, protocol v1 schema | C (Opus subagent drafts sections) | T0.13 |
| T2.1 | Undo/redo/restore as document differences sent as ordinary edits (owner: move early if cheap) | C design, B Studio work | T2.0 |
| T2.2 | State-carrying module replace with crossfade | C | T2.0, T1.3 |
| T2.3 | Module data blocks; Groove edits while running; CC map and OSC rows live | C engine, B per-module | T2.2 |
| T2.4 | Modulation amount as a live parameter | C | T2.0 |
| T2.5 | Protocol v1 from one schema; generated TS types and C++ validation; client queue fixes; heartbeat | C design, B generation | T2.0 |
| T2.6 | Device/buffer change keeps graph and state | C | T2.2 |

**Contracts for Phase 1 and 2 (2026-11-16).** The tables above are history. The live task lists
are the contracts: M1 (T1.2–T1.4), M2 (T2.1 step 1, PV1), **M3** (T1.5–T1.9, native v1 removal),
**M4** (T2.2–T2.4, T2.6: gapless swaps, module data, replace with state, device changes),
**M5** (T2.5: protocol v1). Order between them: `docs/workflow/STANDING.md` SR16.

## Phase 3 to 6 — task list (written 2026-11-16)
"Contract" says where the task is, or will be, contracted. "Design" names the note it needs;
a task with a design that is not on `main` does not start. Classes as above.

### Phase 3 — module format, SDK and tools
| ID | Task | Class | Depends | Design | Contract |
|---|---|---|---|---|---|
| T3.1 | Module tools v0 on today's header: `check`, `test`, `render` for one folder, no author test code, plain errors | B | — (new paths only) | `0003` §5 | **M6**, starts now |
| T3.2 | Wire module header frozen: `wire/module.h`, capabilities, tiers, data slots, `adopt`, telemetry records, fixed-width fields, descriptor list entry | C | M4 E4b | `0012` | M8 |
| T3.3 | Declared config schema (field table); the per-module adapter in `runtime_module_config.h` is deleted | C | T3.2, M4 E3a | `0012` | M8 |
| T3.4 | Host services by declared capability (MIDI device, OSC bus, transport, tables, telemetry); module IDs leave core code | C | T3.2 | `0012` | M8 |
| T3.5 | SDK helpers so a basic module is its arithmetic (host smoothing, voice iteration); port the 34 modules, one PR per group of similar modules | B after one C exemplar | T3.2 | `0012` | M8 |
| T3.6 | Outside-folder discovery (`WIRESCAPE_MODULE_DIRS`), self-contained SDK folder, out-of-tree trial green on three platforms | B | M3 MB2, T3.2 | `0009`, `0012` | M8 |
| T3.7 | ID alias table in the loader; `essentials.chaos_lite` → `chaos`; GUTTR adapter updated and dropped in with 0 core edits | B | T3.2 | `0002` D9 | M8 |
| T3.8 | Tools final: `wirescape module new`, tier check enforced, `bench`; the CLI entry point | B | T3.1, T3.2 | `0003` §5 | M8 |
| T3.9 | Developer loop level 2: `module dev`, in-place swap of a rebuilt module library, "update library" action | C engine and loader, B tool | M4 E5, T3.6 | `0003` §4 | M9 |

### Portability and ecosystem (protected now, built in steps)
| ID | Task | Class | Depends | Design | Contract |
|---|---|---|---|---|---|
| T3.10 | Portable tier in CI: every portable-tier module compiles for Cortex-M7 with the banned-symbol check | A | T3.2 | `0012` | M8 |
| T3.11 | Thin adapters, build-only in CI: one portable module in a minimal Daisy firmware, one as a CLAP plugin | B | T3.5 | `0013` | M10 |
| T6.1 | Patch intermediate form: a flat, ordered, typed description of a patch that the engine loader and a compiler both read | C design, B build | M5 PV2b | `0013` | M10 |
| T6.2 | Strict patch-to-Daisy compiler: portable-tier modules only, deterministic output, refusal messages that name the module and the reason | B | T6.1, T3.11 | `0013` | M10 |
| T6.3 | Build page: place controls, bind to parameters, choose a board, get pin numbers and a wiring guide from a board description file | B | T6.2 | `0013` | later |

### Phase 4 — sound quality
| ID | Task | Class | Depends | Design | Contract |
|---|---|---|---|---|---|
| T4.1 | Module-local fixes in measured order, one module per PR with before and after | B | — | `0011` | **M7**, starts now |
| T4.2 | Host-level modulation smoothing policy; one NaN policy | C | M4 E4b, T3.2 | `0012` | later |
| T4.3 | Fixes that need the Wire header (rate adaptation for ported code, per-port smoothing declarations) | B | T3.5 | `0011`, `0012` | later |
| T4.4 | `ringmod2` sound metrics measured (the M0 exception) | A | M3 MB2 | — | lead may file (SR18) |

### Phase 5 — categories, capabilities, custom UIs
| ID | Task | Class | Depends | Design | Contract |
|---|---|---|---|---|---|
| T5.1 | Category: model-based multi-voice (GUTTR): voice-owner capability, per-voice modulation and telemetry, shared tables | C | T3.4 | `0014` | M11 |
| T5.2 | Category: ported library (Macro Oscillator): rate and block adaptation, third-party pin and licence handling | B | T3.5 | `0014` | M11 |
| T5.3 | Category: multi-part instrument (CHAOS): sections, internal routing, presets | B | T3.5 | `0014` | M11 |
| T5.4 | Stock modules that bring a capability, basic versions: Transport, Stereo Out and Bus, MIDI Out, Scope, Sampler, Wavetable, Logic and Math, Sub-patch, Recorder, and a device bridge for physical computing (OSC to the LAN with consent, serial to a microcontroller) | B each, C for the service each needs | T3.4 | `0014` | M11 |
| T5.5 | Panel package: `panel.json`, the HTML panel host API, sandbox; examples for CHAOS and GUTTR; Groove and OSC editors move onto it | C host API, B panels | T3.2 for telemetry; the declarative part needs nothing | `0015` | M12 |
| T5.6 | Developer mode layers 1 and 2 | B | T5.5, T3.9 | `0003` §4 | M12 |
| T5.7 | Raise the 64-module limit | B | T6.5 | — | later |

### Phase 6 — app, performance, release shape
| ID | Task | Class | Depends | Contract |
|---|---|---|---|---|
| T6.4 | Engine cost: profile the 8-voice reference graph, file where the time goes, then propose. The −20 % target of `0002` has no design yet | A facts, then C | M4 E4b | lead may file the facts part (SR18) |
| T6.5 | Studio rendering at 200 modules to the 20 ms target, from the T0.12 profile | B | M2 E1b | later |
| T6.6 | Pi and Windows runs against the targets, by the owner's device runbook | owner | M4 | — |
| T6.8 | Behaviour bugs listed in `docs/context/KNOWN_ISSUES.md` (MIDI to CV on Windows, ASIO list while playing, LAN OSC consent warning, panic and buffer-change gaps): one device-free regression test and fix each; the owner confirms on the device | B | M1 S6 | later; lead may file the regression tests as facts (SR18) |
| T6.7 | Packaged build and installer; AudioWorklet web demo on the shared engine path | B | M3 MB2 | later |

Design notes `0011` to `0015` are on `main` (Fable, 2026-11-16, runs 1 and 2). Contracts:
**M8** (T3.2–T3.8, T3.10), **M9** (T3.9), **M10** (T3.11, T6.1, T6.2 and the facts of `0013` §8,
which start now), **M11** (T5.1–T5.4; the GUTTR drop-in of T3.7 is M11 C1), **M12** (T5.5, T5.6).
Not contracted: T6.3 build page, Sub-patch (needs its own note), T4.2, T4.3, T5.7, T6.4–T6.8.
Where a contract differs from a row above (for example M8 H1 waits for M4 E3a), the contract wins.

## Contract-driven delivery and fallback
Follow the active revision named by `docs/workflow/CURRENT.md` in
`docs/workflow/milestones/`. The gpt-lead delivers the assigned milestone, starts builders
and merges only the tasks explicitly delegated in that contract. Escalations go to
`docs/workflow/QUESTIONS.md` with evidence and a proposed resolution.

If no Fable-accepted milestone contract is active, the "Who may do what" table above is the
fallback: the lead cannot merge class B or start class C. The lead must not infer authority
from a draft contract.

Signed: Fable, 2026-11-15
