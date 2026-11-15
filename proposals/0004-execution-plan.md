<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0004 — Execution plan: tasks, owners and what can run without Fable

**Author:** Fable · **Date:** 2026-11-15 (ET) · **Status:** live; Fable edits it, others read it.
Phases and goals: `0002`. Module design: `0003`. This file is the task list a new Fable session or a Codex
lead works from.

## Name
The rebuilt engine is **Wire** (the owner's name, 2026-11-15; changeable until
task T1.4 lands). "Wirescape" stays the product. Use: *Wire engine* (`wire/engine`), *Wire modules*,
*Wire module API* (what `0003` calls "module API v3"), header `wire/module.h`, tool `wirescape module …`.
ABI1, "ABI 2", `engine2`, `modules2` and Qt are the experiments that came before.

## Who may do what
| Class | Meaning |
|---|---|
| **A** | Safe without Fable. Touches only `bench/`, `facts/`, advisory workflows under `.github/workflows/`, `docs/context/LOG.md`. A Codex lead may assign it, review it against its issue and **merge on green CI**. |
| **B** | A builder may build it from a written issue; **only Fable merges** (it touches the product tree). A Codex lead may assign it and check CI, then leave it labelled `status/review`. |
| **C** | Fable only (engine design, realtime code, protocol, module API, proposals, CONSTRAINTS, AGENTS/CLAUDE). |

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

Phase 3 onward: `0002` and `0003`; tasks are written when Phase 2's design exists.

## If Fable is unavailable
A Codex lead (`lead: run`, brief in `docs/context/CODEX_LEAD.md`) keeps class A moving and prepares class B.
It never starts class C. When Fable returns it reads the newest LOG entry and reviews everything labelled
`status/review`.

Signed: Fable, 2026-11-15
