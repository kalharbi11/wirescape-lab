<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Lab log (newest first)

## 2026-11-16 — questions Q4–Q6 answered, CI1 contracted (Fable)
**Done:** Q4: `busy` refusals retry and drop nothing, other refusals keep the simple drop; `0010` P5
amended. Q5: owner's patch and preset reset recorded in CONSTRAINTS; no file moves and the golden
gate is unchanged through M1 and M2; the six Macro Oscillator `patches/` files are build-time source
diffs, not sound patches. Q6: one-task contract `milestones/CI1.md` from
`facts/tests/ci_durations_2026-11-16.md`; compiler cache and target trimming held back until measured.
**Not measured here:** every CI saving is an estimate until CI1.1 files its after-table.
**Next:** lead dispatches CI1.1; owner answers Q5 point 7; Fable contracts PV3.
Signed: Fable, 2026-11-16

## 2026-11-16 — Phase 2 designed: 0005, M2 contracted, T0.13 released (Fable)
**Done:** `proposals/0005` from a read of the engine's render/replan/reconfigure code and the sidecar's
commit path. Findings: the live replan already keeps unchanged instances, but `loadGraph` never uses
it, and every replan is a master dip of at least three blocks because routing lives inside `Node`.
Design: `applyGraph` on the existing replan now (M2); then topology moved into an immutable layout
adopted at a block boundary, per-edge ramps, module data slots, instance replacement with a realtime
`adopt` hook or ring-out. T0.13 harness designed (0005 section 4, M0 r2 ruling R6). M1 r2: sidecar
ordering only.
Also designed, not contracted: `0007` engine file split (T1.6), `0008` one transport (T1.7; found
`Engine::transport` is never called and races with render), `0009` module build and generated registry (T1.8),
`0010` protocol v1 (schema-generated, pipelining with a poisoned queue, convergence through `applyGraph`,
heartbeat); its first stage PV1 is in M2.
**State of main:** no product change. **Next:** lead runs M0, M1, M2. Fable: questions, M0 acceptance, protocol v1.
**Open for the owner:** none new.
Signed: Fable, 2026-11-16

## 2026-11-16 — M1 contracted: one-engine design 0006 (Fable)
**Done:** design note `proposals/0006` (ABI1 removal and engine-native types in serial stages plus the
rename, invariants I1–I8, evidence per stage) and contract `M1 r1`. `legacy_index` stays in
`module2.h`; native v1 patch reading is held. Written from grep-level reading; assumptions A1–A4 are
for the builder to verify against inventory P1 first.
**State of main:** no product change. **Next:** lead runs M0 and M1 S0 now, S2 after T1.1 and P1.
Signed: Fable, 2026-11-16

## 2026-11-15 — workflow v2 active, M0 r1 accepted (Fable)
**Done:** reviewed and accepted WP1 (policy, lead brief, CURRENT, QUESTIONS, templates). M0 contract
r1 accepted with rulings R1–R5 (latency quantities, impulse/tail under engine FTZ/DAZ, coverage rows,
instruction-count baseline, T1.1 merge criteria) and four inventories P1–P4 for the next design blocks.
**State of main:** no product change. The builder pause in the entry below is lifted.
**Next:** lead delivers M0 r1. Fable after reset: T0.13 design, T1.2/T1.3 note, `0005`.
**Open for the owner:** T0.14 dependency hosts.
Signed: Fable, 2026-11-15

## 2026-11-15 — owner-requested pause after builder round and review
**Status:** handoff-ready; owner is deploying a new workflow. Do not resume builders, dispatch new
tasks, or continue the 15–20-minute in-chat checks until the owner resumes/replaces this workflow.
No recurring app automation was created. Active builders were told to finish their current run only;
builder1 saved its final checkpoint and stopped. Builder3's last run ended with a system error after
saving its draft/facts; do not restart it automatically. Builder4 completed its read-only review.

| Work | Head reviewed | Review / remaining work |
| --- | --- | --- |
| #66 / PR #69 (class A) | 66a1f1b | Three-machine source facts at 919f047 show 28/34 causal contributions, not full acceptance. Six MIDI/OSC/monitor paths need Fable instrumentation/coverage decisions. Current-head CI queued at inspection. |
| #67 / PR #70 (class B) | 0aa4683 | Allowed test/reference/fixture/CMake/facts scope. Linux x64/ARM64 each have source-attributed 983-case captures; frozen-data conversion is unfinished and integration still links ABI1. Only Fable reviews technical acceptance/merges. Current-head checks pending/queued. |
| #61 / PR #63 (class A) | c9da84b | Implementation and corrected-parser facts reviewed; committed measurement JSON exactly equals source 87aa3ec's hosted summary. Lab CI, UI advisory and Offline facts passed; latest full facts run still running, so no merge. |
| #51 / PR #60 | 6556a2a | Corrected sweep evidence retained; exact impulse and production-FTZ decay timing remain Fable-owned blockers. |
| #52 / PR #58 | cf46a0d | Real 97-row architecture baselines, two explicit unavailable Chord rows; native config/event probe decision needed. |
| #54 / PR #59 | ed7db5f | Uncalibrated command-to-ADC diagnostic only; no accepted calibrated round-trip measurement. |

**Peer review finding to fix under the new workflow:** #69's golden workflow lacks
bench/patches/coverage/** in both pull-request and main-push path filters. A future fixture-only change
can avoid the gate. Builder4 posted the signed finding on PR #69 (comment 6905029767); lead recorded
the follow-up without starting another implementation round. Keep PR #69 draft.

**CI queue action:** verified PR/branch/head/workflow identity and cancelled only obsolete #63 full-facts
run 43781482187 at 87aa3ec, releasing current-head run 43784223829. Accepted profiler capture
43781482219 / artifact 14187674511 was separate and preserved. Cancelled old runs are not passes.
Running/queued hosted jobs may finish while agents are paused; inspect exact heads when resuming.

**Merged this oversight session:** #64/#55 as 76ec785; log handoffs #65 as c8335a0 and #68 as 71daa1c.
Earlier lead merges #48/#41 b8190f9 and #57/#53 7914070 remain on main. No class B/C merge,
engine/DSP implementation change, real-device test, gate weakening, role-file edit or history rewrite.

**Local setup preserved:** ignored .tools/lead-review has pinned synthetic reviewer suites (golden
13/13 and UI CPU/timeline tests passed), plus a metadata-only inventory separating one completed
Windows run from two aborted attempts. It opens no recordings/devices; the active device-test branch
and untracked result folders were not changed.

Signed: gpt-lead, 2026-11-15

## 2026-11-15 — periodic lead oversight: golden gate merged, next work dispatched
**Owner instruction:** continue authorized setup work and recheck builders about every 15–20 minutes.
This is in-chat oversight, not a recurring app automation. Existing class A/B/C authority is unchanged.

**Done:** reviewed #64 integrity fixes at `128e5b6`; all 13 comparator tests and all 24 bundled
same-runner comparisons passed on Linux x64, ARM64 and Windows. Each current-head uncommitted DSP
experiment detected sample 2/frame 1, peak delta 0.027496248483657837, then declared it; all seven Lab CI
jobs passed. Squash-merged #64/#55 as `76ec785`. Merged previous handoff #65 as `c8335a0`.

**Next assignments dispatched directly:**
- #66 / gpt-builder3: T0.11 deterministic coverage fixtures for all 34 runtime modules. New coverage
  inputs must be identical for both tested engine revisions, with separate input/engine provenance;
  bundled/owner missing-fixture failures remain intact. Bench/facts/advisory workflow only, class A.
- #67 / gpt-builder1: T1.1 freeze live ABI1 reference outputs, then independent ABI2 comparison tests.
  Class B, only Fable merges; relevant test/fixture/CMake wiring only, no engine/DSP/shim deletion.
  #51/#60 retains its exact-impulse and production-FTZ-tail instrumentation blockers.
- gpt-builder4: #63 parser fixes reviewed; the corrected-parser head `87aa3ec` completed all 36
  CPU/trace captures with explicit markers in advisory run 43781482219. Refresh committed facts from
  that real source/artifact (14187674511), then validate the resulting exact head. Latest Lab CI passed,
  including Windows; retain the prior native-test failure and cancelled rerun history.
- #52/#58: corrected 97-row baselines and osc.out source audit are recorded and exact-head workflows
  passed at `cf46a0d`. Two chord rows remain unavailable because the native direct probe supplies no
  required four-byte config tag. Keep draft; Fable owns the native probe/config/event-stimulation decision.
- #54/#59 remains blocked for Fable's calibrated output/input clock/timestamp design.

**Local reviewer setup:** isolated ignored scratch contains pinned golden comparator and UI parser
copies. Existing bench-venv Python 3.12.10 has NumPy/SciPy; no package installation was needed.
Local golden synthetic suite: 13/13 passed. Local UI CPU/timeline known-answer suite: passed.
These checks open no audio/MIDI devices, native engine processes or LAN sockets; active device-test
branch and its untracked results were left untouched.

**Bootstrap observations for Fable (read-only):** cloud setup already has a git-source fallback and
headless build warmup. The documented HTTPS allowlist omits codeload.github.com, although native
FetchContent URLs use it. git_deps.py enumerates five pinned repositories (json, eurorack, stmlib,
alsa-lib, libremidi); attachment/access and toolchain preparation must survive a fresh cloud task.
No session permissions, tools/ files, product code, role instructions or protected constraints changed.

Signed: gpt-lead, 2026-11-15

## 2026-11-15 — Codex lead follow-up: soak repair merged, gate integrity review
**Done:** merged the previous lead handoff #62 as `5b040ee`. Reviewed all eight changed paths in #48,
including the main-integration diagnostic tests and the two 72-row, 30-second Linux fact projections.
Current-head Lab CI passed 7/7; Offline facts and Generate device-off facts passed. Squash-merged #48
at `40748f5` as `b8190f9`; #41 closed. Original and derived keyboard-graph measurements remain distinct.

**Reviewed, not merged:** #64/#55 now has successful same-runner golden jobs on Linux x64/ARM64 and
Windows x64, plus green Lab CI. All three hosted mutation experiments detected sample 2/frame 1 with
peak delta 0.027496248483657837, then reported the change declared. Source review found two false-pass
paths: declarations could excuse a missing patch, and equal JSON hashes could hide different A/B WAVs.
Builder3 is fixing those with CLI/known-answer tests; the new head must be revalidated before merge.

**Builder follow-ups sent directly and recorded on GitHub:**
- Builder1: #48 is complete; continue #51/#60 corrected sweep evidence from full run 43774561958.
  Exact impulse and engine FTZ/zero-input tail timing remain native instrumentation questions for Fable.
  Keep the concrete interface proposal in issue/PR discussion, rather than a builder-authored design
  proposal committed under bench/.
- Builder2: #58's corrected 97-row run 43774054913 passed, but old 95-row baselines are incomplete.
  Refresh actual x64/ARM64 measurements; keep unavailable chord rows visible and escalate product/probe
  changes. Check osc.out runs devices-off, with no LAN sockets.
- Builder3: finish #64 comparator integrity fixes, then exact-head acceptance/CI; no committed DSP edits.
- Builder4: #63's UI profiler run passed, but Windows Lab CI failed in
  abi2_sidecar_audio_recovery_tests ('OSC works before ASIO device loss'). Investigate; one failed-job
  rerun is appropriate only with evidence of an unrelated transient, without loosening native tests.
  Refresh head-pinned UI facts. Fix empty CPU captures being marked measured and the aggregate
  top-self undercount caused by truncating each trial before aggregation.

**State / next:** #58/#59/#60/#63/#64 remain draft; #50 remains outside this merge pass (draft,
not requested for merge). Review builders' new commits/evidence before any readiness transition.
Fable still owns #54 calibrated device-timing design, #51 exact impulse/tail instrumentation, T0.14
dependency access and T0.13/T2.0 design. Broader delegation is not assumed. No devices, product-tree
changes, class B/C merges, gate weakening or history rewrite in this lead run.

Signed: gpt-lead, 2026-11-15

## 2026-11-15 — interim Codex lead: builder review and next assignments
**Done:** owner asked gpt-lead to coordinate existing builders while Fable prepares broader delegation.
Reviewed all six open PRs and their exact-head workflow results (all passed at inspection). Independently
reviewed #57 (class A), reconstructed its original hosted PORTABILITY_CHUNK JSON and verified exact
equality with committed facts (35 translation units, two FPUs, 70 compiled objects). All seven Lab CI jobs
and current-head portability workflow passed. Squash-merged #57 as `7914070`; #53 closed. This is
compile-only translation-unit evidence, not link/runtime proof. Post-merge main workflow verification
remains next.
Sent task follow-ups directly to all four existing builder chats and recorded lead notes on issues
#41, #51, #52, #54 and #55. Filed #61 (T0.12 UI frame-time attribution), assigned to gpt-builder4.

**State:** product tree unchanged by this lead run. No device tests, force-pushes, class B/C merges,
or changes to Fable's execution plan. #48 was ready/green but non-mergeable at inspection; #50 remains
draft and explicitly not requested for merge. #58/#59/#60 remain draft with acceptance gaps.

**Next (builder ownership):**
1. gpt-builder1: merge current main into #48 without rewriting history, preserve original/derived-graph
   provenance, revalidate exact head; then #51/#60 actual hosted facts, exact impulse and denormal-tail
   timing. If native instrumentation is needed, send Fable the smallest concrete proposal.
2. gpt-builder2: #52/#58 inspect successful x64/ARM64 runs, stage actual baselines with real provenance,
   check missing/failed-row handling and reconcile the 33-versus-34 module inventory; respect #55 dependency.
3. gpt-builder3: #57 is merged; prioritize #55 same-runner golden gate. Preserve concurrent branch work,
   open the missing PR and supply all stated three-platform/no-op/declared-change acceptance evidence.
4. gpt-builder4: #54/#59 audit measurement meaning and timing bounds. Command-to-ADC estimates are not
   calibrated DAC-to-ADC latency; keep acceptance blocked if native timestamps are required. Proceed to
   #61 FakeEngine UI attribution while awaiting Fable. Avoid builder1's run_all.py; use separate files.

**Questions for Fable:** #54 needs a native timing reference or an explicit owner-approved change in
the required quantity; gpt-lead has not changed acceptance. #51 may need native impulse/tail instrumentation.
T0.14 cloud dependency access and T0.13/T2.0 design remain with Fable/owner. Existing role authority is
still class A merge / class B preparation / no class C; broader delegation is not assumed.

Signed: gpt-lead, 2026-11-15

## 2026-11-15 — task list, engine name, Codex lead brief (Fable) — START HERE
**Done:** `proposals/0004-execution-plan.md` (every task with class A/B/C, dependencies, done-when); engine
named **Wire**; `docs/context/CODEX_LEAD.md` and `lead: run` trigger for a stand-in that handles class A.
**State of main:** product tree unchanged. Phase 0 in progress through builders (#41/#48, #51–#55).
**Next for Fable (fresh session):** 1) review `status/review` PRs and the Codex device results; 2) T0.13
edit-continuity design; 3) T2.0 live-edit design note with an Opus subagent drafting; 4) Phase 1 from T1.1
once #55 is merged and T0.14 (local build) is solved.
**Open for the owner:** T0.14 (allow `add_repo` or choose another way to get the two libraries).
Signed: Fable, 2026-11-15

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
