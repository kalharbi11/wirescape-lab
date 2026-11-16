<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead, replacement local lead. Last reviewed `main`: `64c1c6b466ffb2d135c5b95dc72923712d815996`.

## Active contract
**Fable, 2026-11-16, questions run Q7–Q11 (read this first; the sections below predate it):**
- **CI1 is r2.** New CI1.2 (literal `linux-x64`, `linux-arm64`, `windows-x64` aggregate checks) is the
  next `ci.yml` writer and unblocks notes-only merges such as PR #97. CI1.3 (sanitizer `ccache`)
  follows CI1.2 and merges only if it saves 2.0 min warm. Nothing stops.
- **M0 is r3.** T0.13a (PR #104) adds a marks file to the capture; T0.13b (PR #106) locates edits
  from it and gets `.github/workflows/continuity.yml`. **Replan in #106:** drop the wall-clock
  edit location; keep the metric code and its tests. Both continue in their open PRs.
- **M2 is r3.** PV1 (PR #105) puts the request-ID rule in the schema with the one permitted
  `pattern`; D07 is resolved there. E1a and E1b are unaffected.
- No ruling here waives red CI. PR #98's Windows failure stays the lead's to diagnose; M1 S2 and
  PR #104 wait on it.

**[M0 r2](milestones/M0.md), accepted and active.** Phase 0 remainder, T1.1, and four fact
inventories (P1–P4). Tasks are delegated per the contract; T0.13a/b are released by R6 and T0.14 remains owner-owned.

**[M1 r2](milestones/M1.md), accepted and active, in parallel.** One engine: stages S0, S2–S6
from [proposals/0006](../../proposals/0006-one-engine-migration.md). S0 can start now with any free
builder. S2 starts when T1.1 and inventory P1 are merged; one builder owns S2–S6 serially.

**[M2 r2](milestones/M2.md), accepted and active, in parallel.** `applyGraph`: undo, redo, restore
and config edits stop restarting untouched modules. E0 (canonical config bytes, small, can start now), PV1 (protocol schema and generator, can start now), then E1a (sidecar), then E1b (Studio). Design and the
rest of Phase 2: [proposals/0005](../../proposals/0005-edits-without-restart.md).

**[CI1 r1](milestones/CI1.md), accepted and active, in parallel.** One task, CI1.1: shorter Lab CI
(build parallelism, three Studio shards, linked desktop suite dropped from Studio's `test`, notes-only
pull requests run `foundation` only). Dispatchable now to any free builder; owner wants it soon.
`.github/workflows/ci.yml` is single-writer for CI1.1 while its PR is open, so PV1's drift check
goes in a new workflow file. No task under M0, M1 or M2 stops or replans.

**Changed in M0 r2:** T0.13 is no longer held. T0.13a (sidecar capture flag) and T0.13b (harness)
can be filed now; ruling R6.

**Sidecar ordering (M1 r2, M2 r2):** T0.13a, E1a, PV1's `native/sidecar/generated/` files and E0's
`native/document/` change merge before M1 S5a opens, or wait until S5b.

## Active batch B1

[Batch #82](https://github.com/kalharbi11/wirescape-lab/issues/82) continues.
**Owner priority: CI/CLI test turnaround FIRST, before new feature dispatch.**
[CI1.1 #95](https://github.com/kalharbi11/wirescape-lab/issues/95) is builder3's one active task.
It exclusively owns `.github/workflows/ci.yml`. Baseline counts and K4 pre-edit source search
were returned, confirming substantive startup. Result-or-blocked checkpoint: **2026-11-16 07:00 ET**;
this is not an acceptance deadline. Existing baseline skips are unchanged, no new skips allowed.

| Writer | Current task | Lead-owned review / next |
|---|---|---|
| builder1 | #51 / PR #60 R2 metrics packet | #70 corrected `2c464fb`, signed Result; new CI/evidence pending |
| builder2 | #80 / P3 module build and registry inventory | #58 merged `64c1c6b` after root artifact audit |
| builder3 | CI1.1 / #95, accepted CI1 r1 | P1 merged; P2 corrected by lead, no concurrent builder edits |
| builder4 | #59 round2 returned `3e485dff`; no active implementation during review | S0/#84 remains assigned but paused |
| Worker 2 Cloud | PR #59 read-only delta review at `3e485dff` | earlier onset oracle and P2 source audit complete |

One task/writer; a next nonoverlapping task may start after the prior signed Result enters lead review.
A chat rotates only after all its owned PRs close with signed dispositions. Existing chats/history
are retained: regular Chat replacements are required, but supported create_thread only offers Work
Cloud, and list/read report backing kind without a Chat/Work mode field. No substitution/mode claim.
Active statuses after dispatch are separate from substantive execution proof; inspect actual results.

Sole local lead: **WLAB | LEAD | delivery 2**, thread `01a1e3ca-c0d2-7d80-b1bc-6bcb93692b9a`.
Existing `wlab-lead-review` read back ACTIVE, target this thread, **45-minute** interval; old lead
stopped dispatch. No duplicate schedules, model waits/rechecks of unchanged state or expensive reruns.
The local stale device-results checkout and untracked captures remain untouched.

Queued: #81/P4, S0/#84 paused, E0/#85, PV1/#86, then explicit T0.13a/b packets. CI1 first.
PV1's drift check uses a new workflow; respect M1 r2/M2 r2 sidecar ordering.

## Current review findings

- #58 merged `64c1c6b466ffb2d135c5b95dc72923712d815996`. Root reviewed bounded JSON validation,
  both-length call sites, mocks/comparator/advisory workflow and independently opened both actual
  profiling ZIPs. Each has 97 unique rows, 95 finite positive numeric measurements with exact
  two-length arithmetic and two reason-bearing Chord exceptions. ZIP/JSON hashes, historical
  baseline blobs and head/run linkage matched; zero numeric rows exceeded +3%. Lab `43835691687`
  and instruction `43835691748` passed. Main post-merge outcome remains to verify.
- #59: Worker2 accepted onset fix `0c465529` (16 tests, independent 720-pulse oracle), then found
  ignored callback status. Round 2 of 2 returned `3e485dffbd2ac79c334554b8a21fc53b90e0aa37`:
  refuse flagged capture, preserve diagnostic reasons, five mocked regressions. Fresh Lab
  `43847088024` and Device `43847088206` pending; Worker2 reviews only the delta. No hardware claim.
- #70 corrected `2c464fb378de1c1594d53cef565f7f76ed53b13c`: undeclared VERIFY in the frozen
  fixture header replaced with independent fatal integrity checks, comparison assertions unchanged.
  Signed Result awaits exact-head native/Golden/dependency evidence. Earlier Offline workflow
  conclusion masked failed build children and is not accepted native evidence. Lead owns review.
- #73 merged `e559634d2d1ee1a4597984e5c16bcd2013e413f1` after exact-head CI and recorded
  independent factual/privacy/raw-blob metadata review. #75 corrected
  `09a7cf3701db4cdd3bd9dcb559dbe00cca98061c`: main integrated, five headers/25 licenses/18-row
  table; all 25 raw blob SHAs unchanged. Fresh Lab `43846491720` / Device `43846491709` pending.
- P1/#89 merged `3ae712b4dc2af05f2aee18208aa2bbb5c7a629cc`, exact-head `43837338789`,
  recorded semantic/citation review. Worker2 audited P2/#91: 184 citations, 231 ranges, 25 source
  files, 19 commands. Root confirmed App.ts:505–508 and added refused-draft qualification plus an
  editorial reference fix in `38057f3`; fresh CI required. Builder3 stays on CI1.
- Worker2 has a clean reference checkout at44da1e4, no lab checkout; GCC14.2, Python3.12.14,
  existing tool-venv CMake4.2.3/Ninja1.13. Reference cache is not lab evidence. New support only goes
  to Worker2; old cloud history/artifacts retained. Tool messaging back is unavailable there.

## Open work (verify heads live; this is a snapshot)

| Task | Issue / PR | Next |
|---|---|---|
| CI1.1 | #95 / PR to open | builder3 first priority, K1–K5 evidence |
| T0.5 | #51 / PR #60 | builder1 active R2 packet |
| T0.6 | #52 / PR #58 | merged `64c1c6b`, post-merge workflow outcome pending |
| T0.8 | #54 / PR #59 | round2 `3e485dff`, delta review and fresh CI |
| T0.9 | PR #73, #75, #50 | #73 merged; #75 `09a7cf3` CI pending; #50 review remains |
| T0.11 | #66 / PR #69 | merged `cacf9ea` |
| T0.12 | #61 / PR #63 | merged `2a02874` |
| T1.1 | #67 / PR #70 | corrected `2c464fb`, lead review/new CI |
| P1–P4 | #78–#81 | P1 merged; P2 corrected `38057f3`; P3/#80 active; P4 queued |
| M1 S0 | #84 | builder4 paused until corrected #59 review |
| M2 E0 / PV1 | #85 / #86 | queued behind CI1, M2 r2 order |
| T0.13a/b | to file | explicit implementation packets needed |
| T0.10 | to file | after required measurement tasks merge |

## Decisions
- Rulings R1–R6 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q6 answered, queue empty (Fable, 2026-11-16).
- Q4: `busy` refusals are retried and drop nothing; other refusals keep 0010 P5. PV3 is unblocked for contracting.
- Q5: bundled patches and presets may be reset after the rebuild (CONSTRAINTS, owner's change
  2026-11-16). Nothing moves now; golden "24 identical" stays through M1 and M2.
- Q6: contracted as CI1.
- Q7–Q11 answered (Fable, 2026-11-16): CI1 r2, M0 r3 (R7), M2 r3. See [QUESTIONS](QUESTIONS.md).
- The old pause in the 2026-11-15 LOG entry is lifted by this contract.

## Next action by role
- **gpt-lead:** prioritize CI1/#95 and verify actual builder execution. Review changed results/heads
  under #82 and the live contracts; merge only exact-head evidence. Queue unresolved design exceptions
  in QUESTIONS.md, update this handoff at batch boundaries, preserve one 45-minute heartbeat.
- **Builders:** one task each, result comment on the PR.
- **Designed, not yet contracted (Fable contracts each when its dependency is near):**
  [0007](../../proposals/0007-engine-file-split.md) engine split T1.6 (after M1 S5b);
  [0008](../../proposals/0008-transport.md) transport T1.7 (after M1 S5b);
  [0009](../../proposals/0009-module-build-and-registry.md) module build T1.8 (after M1 S6);
  0005 sections 5–7 (after T1.6); [0010](../../proposals/0010-protocol-v1.md) protocol v1 stages PV2–PV5.
- **Fable next:** `fable: run questions` when the queue has entries; `fable: run accept M0`; contract PV3;
  Wire module API details (0003) once M1 is through S5.
- **Owner:** T0.14 dependency hosts; device runs when the lead asks. Q5 point 7: add the owner's own
  patches that must keep sounding the same to `bench/patches/owner/`, or say there are none.

The lead updates this file at each batch boundary; Fable after contract revisions.

Signed: gpt-lead, 2026-11-16
