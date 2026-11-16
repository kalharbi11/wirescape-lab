<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

**Replacement local lead:** read [LEAD_STARTUP.md](LEAD_STARTUP.md) for chat IDs, tool route,
startup verification, cloud cache, current checkpoints and safe heartbeat takeover.

Updated: 2026-11-16 (ET) by gpt-lead. Last reviewed `main`: `cacf9ea`.

## Active contract
**[M0 r2](milestones/M0.md), accepted and active.** Phase 0 remainder, T1.1, and four fact
inventories (P1–P4). Tasks are delegated per the contract; T0.13a/b are released by R6 and T0.14 remains owner-owned.

**[M1 r2](milestones/M1.md), accepted and active, in parallel.** One engine: stages S0, S2–S6
from [proposals/0006](../../proposals/0006-one-engine-migration.md). S0 can start now with any free
builder. S2 starts when T1.1 and inventory P1 are merged; one builder owns S2–S6 serially.

**[M2 r2](milestones/M2.md), accepted and active, in parallel.** `applyGraph`: undo, redo, restore
and config edits stop restarting untouched modules. E0 (canonical config bytes, small, can start now), PV1 (protocol schema and generator, can start now), then E1a (sidecar), then E1b (Studio). Design and the
rest of Phase 2: [proposals/0005](../../proposals/0005-edits-without-restart.md).

**Changed in M0 r2:** T0.13 is no longer held. T0.13a (sidecar capture flag) and T0.13b (harness)
can be filed now; ruling R6.

**Sidecar ordering (M1 r2, M2 r2):** T0.13a, E1a, PV1's `native/sidecar/generated/` files and E0's
`native/document/` change merge before M1 S5a opens, or wait until S5b.

## Active batch B1

[Batch #82](https://github.com/kalharbi11/wirescape-lab/issues/82), coordination base `edb16274f0f7b456e3e17e33f1899a820661059c`.
Result-or-blocked checkpoint: **2026-11-16 05:30 ET**. Builder1 owns #67/#70 (R5),
builder2 #52/#58 (R4 plus lead correction round 1), builder3 P2/#79 after P1/#89 entered review,
builder4 #54/#59 (R1).
One task/branch/PR per builder; no automatic queue pickup. Existing WLAB chats are the dispatch
route; delivery/turn completion is checked separately. Cloud worker is environment/build support,
not another product writer. Focused independent reviewers checked #63, #69, #58 and the device facts.

The owner resumed work in the local lead chat and requested 15-minute scheduled review checks.
The thread heartbeat is active; unchanged results end promptly, with no duplicate dispatch or
expensive rerun. Usage limits remain shared. Preserve the local device-results branch and its
untracked captures; repository coordination uses separate GitHub branches.

Next dependency-ready dispatch: remaining inventories #79–#81, M1 S0/#84, M2 E0/#85 and PV1/#86,
then M0 T0.13a as writers free up. Do not dispatch queued tasks before the current result.
T0.5/#60 waits for builder1's current task to return to review; apply R2 before acceptance.
The M1 S5 sidecar ordering and all contract-review requirements remain in force.

## Current review findings

- #58: native module probe can print nonzero `faults` yet exit zero. Collector accepted the exit/Ir
  totals without checking that JSON. Round 1 requests bench-only validation and mocked fault,
  malformed/missing and healthy evidence tests, followed by real hosted evidence. No native change.
- #73/#75: both had green checks at review; preserve raw evidence and add required licensing metadata,
  place appended README rows inside the table, integrate #73 before #75. Never run devices here.
- Cloud worker received an isolated **baseline `cacf9ea`** checkout/build/test support package using
  existing tools and pinned public dependencies. No package installation or persistent setting change.
  Tool delivery is not build/start success; inspect its result separately.
- Actual starts were verified for all four builders. Inspect latest assistant activity before any
  new dispatch or retry. The startup guide records current corrections and the temporary reset-aware timer.

## Open work (verify heads live; this is a snapshot)
| Task | Issue / PR | Next |
|---|---|---|
| T0.5 | #51 / PR #60 | apply ruling R2, then lead review |
| T0.6 | #52 / PR #58 | round 1: reject module probe JSON faults/malformed evidence; keep R4 exceptions/thresholds; revalidate actual evidence |
| T0.8 | #54 / PR #59 | correction round 1: onset detector bias; S0/#84 paused until result returns review |
| T0.9 | PR #73, #75, #50 | #73/#75 factual review found no material inflation/privacy issue; fix README table placement and artifact SPDX metadata before merge |
| T0.11 | #66 / PR #69 | merged `cacf9ea`; reviewed head `44e31258e2e2784a1d1dc8d301dd3f248e2d982b`, 3-platform Golden and 7-job Lab CI passed |
| T0.12 | #61 / PR #63 | merged `2a02874`; reviewed head `c9da84bd23ac20ed4a1de55327447d01117c7e7c`, all four workflows passed |
| T1.1 | #67 / PR #70 | finish frozen-data conversion, drop the ABI1 link; R5 |
| P1–P4 | #78, #79, #80, #81 | #89 lead addendum head f94b324 requires fresh CI; #79 active; #80/#81 queued |
| T0.10 | to file | after the rows above merge |

## Decisions
- Rulings R1–R6 are in M0. [QUESTIONS](QUESTIONS.md): Q4/Q5 open for Fable.
- The old pause in the 2026-11-15 LOG entry is lifted by this contract.

## Next action by role
- **gpt-lead:** `lead: run B1`. Verify dispatch/results for #82, review changed heads and merge per
  contract. Queue design exceptions in QUESTIONS.md; dispatch inventories when builders return.
- **Builders:** one task each, result comment on the PR.
- **Designed, not yet contracted (Fable contracts each when its dependency is near):**
  [0007](../../proposals/0007-engine-file-split.md) engine split T1.6 (after M1 S5b);
  [0008](../../proposals/0008-transport.md) transport T1.7 (after M1 S5b);
  [0009](../../proposals/0009-module-build-and-registry.md) module build T1.8 (after M1 S6);
  0005 sections 5–7 (after T1.6); [0010](../../proposals/0010-protocol-v1.md) protocol v1 stages PV2–PV5.
- **Fable next:** `fable: run questions` when the queue has entries; `fable: run accept M0`;
  Wire module API details (0003) once M1 is through S5.
- **Owner:** T0.14 dependency hosts; device runs when the lead asks.

The lead updates this file at each batch boundary; Fable after contract revisions.

Signed: gpt-lead, 2026-11-16
