<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Lab log (newest first)

## 2026-11-15 — builder PRs merged, next issues queued, API v3 design note (Fable)
**Done:** reviewed (subagents) and merged #45 speaker check, #46 Windows facts collection, #47 golden
renders (24 of 24 bundled patches, references for Linux x64, ARM64 and Windows). Filed #51 (sound metrics),
#52 (instruction-count gate), #53 (Cortex-M7 compile facts), #54 (round-trip latency), #55 (golden gate:
same-job base/head comparison, the gate Phase 1 will rely on). Wrote
`proposals/0003-module-api-v3-and-dev-loop.md` (interface changes, drop-in, developer loop levels, module
tools).
**State of main:** product tree unchanged. Open PRs: #48 (soak repair, draft), #50 (bench MIDI port names,
draft). Codex device runs in progress (Windows nearly done, Pi running).
**Blocked:** no local native build in the cloud container: the build downloads source tarballs from
`codeload.github.com`, which the session's GitHub proxy refuses for repositories not attached to the
session; attaching `nlohmann/json` and `celtera/libremidi` was denied by the permission system. Until the
owner allows that (or the build gets another source for them), engine work is built only by CI.
**Next:** review #48/#50 and the Codex results PR; revise the phase text in `0002` for the decisions; live
edit design note (`0004`); Phase 1 once #55 is in and a local build works.
Signed: Fable, 2026-11-15

## 2026-11-15 — decisions recorded, Codex device runbook (Fable)
**Done:** owner decisions on the plan recorded in `proposals/0002-plan.md` (yes to all, with changes: no
owner patches for golden renders; fast developer loop and developer mode for modules; developer test
scripts brought forward; device testing through Codex; undo/restore as small edits into block 2 if cheap;
Daisy/CLAP proofs first to postpone). `docs/context/CONSTRAINTS.md` carries the owner's devices-off change.
Wrote `bench/device/CODEX_RUNBOOK.md` v1 (Pi: full run at 256 and 128, heavy patches at 128, 64-frame
probe, GUTTR benchmark, app memory, health log; Windows: quick run at 256 and 128). The GUTTR benchmark
build and run was verified in the cloud container; the device commands are from `run.py`'s options and
were not executed.
**State of main:** product tree unchanged. Builder PRs open: #45 (ready), #46, #47, #48 (drafts).
**Next:** review and merge #45–#48; fold in device results when Codex files them; revise the plan's phase
text for the decisions; Phase 0, then Phase 1.
**Not covered by the runbook yet:** round-trip latency (no tool), device change during playback as an
isolated test, GUTTR voice counts between 1 and 16 (needs GUTTR in the tree).
Signed: Fable, 2026-11-15

## 2026-11-15 — audit and plan (Fable)
**Done:** read the brief, context docs and `facts/` (five subagent digests, key numbers re-checked).
Wrote `proposals/0001-audit.md` (findings by area, each tied to a fact file) and `proposals/0002-plan.md`
(12 owner decisions at the top, targets, Phases 0–6, block mapping). Added `facts/code/audit_checks.md`
(X5 settled: the SDK wrapper resets after prepare). Filed measurement-repair issues #41–#43 for the GPT
builders (bench only, optional). No product code changed.
**State of main:** product tree unchanged from the snapshot. Open issues: #36, #41, #42, #43.
**Device results:** Pi 60-minute, Windows 15-minute and cross-tool runs were not in `facts/` at `7b334e5`;
the audit's performance section and the plan's targets are provisional until they are.
**Next (after the owner answers D1–D4):** Phase 0 (harness holes, golden renders, edit-continuity test,
`facts/BASELINE.md`), then Phase 1 (delete ABI1, engine-native types, layout, transport). Fold new device
results into the audit first.
**Open for the owner:** decisions D1–D12 in `proposals/0002-plan.md`; drop saved patches into
`bench/patches/owner/` for the sound-equality gate; optionally run the GPT builders on #41–#43.
Signed: Fable, 2026-11-15

## 2026-11-15 — Fable takes over (Keel)
Owner: Fable leads the lab and decides its own process; GPT builder queue paused (open #36 stays parked).
BRIEF updated: audit and plan first, then stop for the owner; phases are goals, order is Fable's.
Signed: Keel, 2026-11-15

## 2026-11-15 — handover to Fable (Keel)
Brief written (`docs/context/BRIEF.md`); owner accepted CONSTRAINTS as is; vision statement added to
OWNER_WANTS. GUTTR: GPL-3.0-only, ID `guttr`, package in `future_modules/guttur/package/`. Open: lab #36
(gpt-builder3, speaker check). Pending owner runs: Pi 60-min, Windows 15-min, comparisons.
Signed: Keel, 2026-11-15

## 2026-11-15 — prep status (Keel)
**On main:** hosted CI (Linux x64/ARM64, Windows, full sanitizers); bench harnesses (offline, device,
cross-tool compare, out-of-tree SDK trial, facts workflow); ported fixes (OSC Out phantom gate, LAN warning,
Linux virtual MIDI inputs).
**Facts in:** `facts/code/` (FACT_PACK, capability_map, out_of_tree_trial); hosted CI measurements
(`facts/perf|dsp|repo|tests|app/ci-*`); `facts/compare/` (tools, SDKs, export pipelines, published performance,
UI systems, module categories, Pink Trombone); `facts/device/results/` (Pi + Windows device-off, Pi 15-min
quick on a patched build, Windows validation + speaker check).
**Pending (owner):** Pi 60-minute full run; Windows 15-minute quick run; cross-tool comparison runs; GUTTUR
licence and module ID; CONSTRAINTS.md review; the brief (`docs/context/BRIEF.md`, from OWNER_WANTS).
**Fable has not started.**
Signed: Keel, 2026-11-15

## 2026-11-15 — device results filed (Keel)
Done: removed the two owner-uploaded zips from `tests/` (21 MB, duplicates of the draft release
`bench-2026-11-14`; still in history at `6edc84a`). Unpacked the small files of the cd9a6a5 device-off
archives and the new Windows validation zip (842d682) into `facts/device/results/`, now laid out as
`<machine>/<date>-<sha7>-<scope>/` with an index `README.md`.
State of main: Pi 15-minute quick run done (b1d92be, local MIDI patch); Windows has build, dry run and
a speaker check only.
Next: Windows 15-minute quick run; Pi 60-minute full run; reference-tool comparisons.
Open for the owner: attach `windows-validation-2026-11-15-842d682.zip` to the draft release
`bench-2026-11-14`; upload future run zips to the release, not the repo.
Signed: Keel, 2026-11-15

## 2026-11-14 — setup (Keel)
Imported the product tree at the SNAPSHOT SHA; wrote AGENTS/CLAUDE, context docs, facts/bench skeleton.
Queued the first GPT issues (CI, fact pack, device harness, research). Fable has not started.
Signed: Keel, 2026-11-14
