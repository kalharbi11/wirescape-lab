<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by gpt-lead, replacement local lead. Last reviewed `main`: `3ae712b4dc2af05f2aee18208aa2bbb5c7a629cc`.

## Active contract
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

[Batch #82](https://github.com/kalharbi11/wirescape-lab/issues/82) continues with a CI1 priority packet.
**Owner priority: CI/CLI test turnaround FIRST, before new feature dispatch.**
[CI1.1 #95](https://github.com/kalharbi11/wirescape-lab/issues/95) is assigned to builder3 after
P2/#91 returned its Result. One cohesive PR; `.github/workflows/ci.yml` has one writer.
Result-or-blocked checkpoint: **2026-11-16 07:00 ET**; this is not an acceptance deadline.

| Writer | Current task | Lead-owned review / next |
|---|---|---|
| builder1 | #67 / PR #70: resolve actual Lab/Golden failures at `72df7c5` under R5 | #60 remains queued |
| builder2 | #52 / PR #58: inspect real profiling artifacts at `9b857485` after green hosted runs | lead review follows signed evidence |
| builder3 | CI1.1 / #95, accepted CI1 r1 | P1/#89 merged; P2/#91 with lead |
| builder4 | no active implementation during PR #59 independent review | S0/#84 remains assigned but paused |
| Worker 2 Cloud | pinned read-only PR #59 review at `0c465529` | support only, no product edits |

Actual active ChatGPT statuses were observed after dispatch; substantive execution/results still
require verification. Existing chats are retained while owned PRs/corrections remain open.
Regular Chat replacements are required; available `create_thread` exposes Work Cloud only, so no
unsupported replacement or mode claim is made.

The sole local lead is **WLAB | LEAD | delivery 2**, thread
`01a1e3ca-c0d2-7d80-b1bc-6bcb93692b9a`. The existing `wlab-lead-review` was read back ACTIVE,
targeting this thread every **45 minutes**; the previous lead stopped dispatch.
No model waits/rechecks unchanged state, no duplicate CI reruns or dispatch.
Preserve the stale local device-results checkout and untracked captures; use GitHub branches.

Queued work: #80/#81 inventories, S0/#84, E0/#85, PV1/#86, then M0 T0.13a with explicit packets.
Keep accepted single-writer/dependency rules. CI1 gets priority; PV1's drift check uses a new workflow.
One active task per builder; a next nonoverlapping task may start after the previous Result enters
lead review, but a chat is rotated only after all its owned PRs close with signed dispositions.

## Current review findings

- #58: strict probe-JSON correction has green Lab `43835691687` and instruction
  `43835691748`; builder2 must verify actual 97-row artifacts (95 numeric, two accepted Chord
  exceptions), unchanged provenance/advisory gate/+3% threshold before acceptance.
- #59: onset-bias correction `0c46552974997de4510978c10ae73a9cde5796e4` has green Lab
  `43837270217` and devices-off harness `43837270229`. Worker 2 independently checks R1
  definitions, sample-onset oracles, timing arithmetic and device gates; no physical measurements.
- #70: `72df7c5bc615038379b40143cffd41257d75e975` has failed Lab `43840632035` and
  Golden `43840631960`; returned to builder1. Offline facts `43840631942` passed.
- #73 merged `e559634d2d1ee1a4597984e5c16bcd2013e413f1` after exact-head CI and the recorded
  independent factual/privacy/raw-blob metadata review. #75 now needs main integration, five
  report headers, 25 adjacent license sidecars and README table integration; raw bytes preserved.
- P1/#89 merged `3ae712b4dc2af05f2aee18208aa2bbb5c7a629cc` after exact-head CI
  `43837338789`, recorded semantic review and citation audit. P2/#91 `b0fdff5` has green
  `43838139339`, awaiting independent content review.
- Worker 2's actual environment has a clean reference checkout, no lab checkout. GCC14.2,
  Python3.12.14, CMake4.2.3/Ninja1.13 in an existing tool venv; reference cache is not lab
  baseline evidence. New support only goes to Worker 2; old cloud history/artifacts are retained.

## Open work (verify heads live; this is a snapshot)

| Task | Issue / PR | Next |
|---|---|---|
| CI1.1 | #95 / PR to open | builder3, first priority; CI1 r1 evidence K1–K5 |
| T0.5 | #51 / PR #60 | queued for builder1, apply R2 |
| T0.6 | #52 / PR #58 | final actual profiling-artifact verification and lead review |
| T0.8 | #54 / PR #59 | independent correction review on Worker 2 |
| T0.9 | PR #73, #75, #50 | #73 merged; #75 metadata/integration next; #50 review remains |
| T0.11 | #66 / PR #69 | merged `cacf9ea` |
| T0.12 | #61 / PR #63 | merged `2a02874` |
| T1.1 | #67 / PR #70 | frozen-data conversion committed; repair CI, prove R5 |
| P1–P4 | #78–#81 | #89/P1 merged; #91/P2 review; #80/P3 and #81/P4 queued |
| M1 S0 | #84 | builder4 paused until corrected #59 review |
| M2 E0 / PV1 | #85 / #86 | queued behind owner CI1 priority, M2 r2 order |
| T0.13a/b | to file | explicit implementation packets still required |
| T0.10 | to file | after required measurement tasks merge |

## Decisions
- Rulings R1–R6 are in M0. [QUESTIONS](QUESTIONS.md): Q1–Q6 answered, queue empty (Fable, 2026-11-16).
- Q4: `busy` refusals are retried and drop nothing; other refusals keep 0010 P5. PV3 is unblocked for contracting.
- Q5: bundled patches and presets may be reset after the rebuild (CONSTRAINTS, owner's change
  2026-11-16). Nothing moves now; golden "24 identical" stays through M1 and M2.
- Q6: contracted as CI1.
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
