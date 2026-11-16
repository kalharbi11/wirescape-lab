<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-16 (ET) by Fable. Baseline `main`: `4956f2d`.

## Active contract
**[M0 r1](milestones/M0.md), accepted and active.** Phase 0 remainder, T1.1, and four fact
inventories (P1–P4). All listed tasks are `merge: lead` except T0.13 (held) and T0.14 (owner).

**[M1 r1](milestones/M1.md), accepted and active, in parallel.** One engine: stages S0, S2–S6
from [proposals/0006](../../proposals/0006-one-engine-migration.md). S0 can start now with any free
builder. S2 starts when T1.1 and inventory P1 are merged; one builder owns S2–S6 serially.

## Open work (verify heads live; this is a snapshot)
| Task | Issue / PR | Next |
|---|---|---|
| T0.5 | #51 / PR #60 | apply ruling R2, then lead review |
| T0.6 | #52 / PR #58 | apply R4, then lead review |
| T0.8 | #54 / PR #59 | apply R1, then lead review |
| T0.9 | PR #73, PR #50 | lead review |
| T0.11 | #66 / PR #69 | apply R3 (rows + workflow path filters), then lead review |
| T0.12 | #61 / PR #63 | lead review once the facts run on its head finishes |
| T1.1 | #67 / PR #70 | finish frozen-data conversion, drop the ABI1 link; R5 |
| P1–P4 | to file | lead files four issues from the contract text and dispatches |
| T0.10 | to file | after the rows above merge |

## Decisions
- Rulings R1–R5 are in the contract. [QUESTIONS](QUESTIONS.md): Q1, Q2 answered; Q3 open.
- The old pause in the 2026-11-15 LOG entry is lifted by this contract.

## Next action by role
- **gpt-lead:** `lead: run`. Send R1–R5 corrections to the builders' existing chats, file P1–P4,
  open batch B1, start builders. Merge per contract. Queue anything else in QUESTIONS.md.
- **Builders:** one task each, result comment on the PR.
- **Fable next:** `fable: run design T0.13` using P2; then note `0005` (T2.0); then T1.8 and T1.7
  using P3 and P4. The T1.2–T1.4 design is done (0006).
- **Owner:** T0.14 dependency hosts; device runs when the lead asks.

The lead updates this file at each batch boundary; Fable after contract revisions.
