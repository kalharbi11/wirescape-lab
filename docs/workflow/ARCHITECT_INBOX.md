<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

A planned review condition goes on the task with `review-required`. Open an Architect-only
review row when its request is ready to dispatch. Routine independent review uses
`review-ready` and a pinned PR request naming the eligible reviewer, without an inbox row.

A row and its labels record the decision or review request. Only the delivery lead sends
a separate [intentional Architect wake](README.md#intentional-architect-wake) when urgency
or a ready batch justifies it: comment `/architect-run` on [#265](https://github.com/kalharbi11/wirescape-lab/issues/265), then add `architect-wake`. The Architect reads the newest command and clears the label when done.

## How to add a row
- Append to **Open**, newest last. One row per ask. Keep the cell short; the link holds detail.
- `Urg`: **now** = blocks a critical-path task (OB0, or the OB1 serial chain) ·
  **soon** = needed within ~2 days · **later** = parked or P3 work.
- `Waits` names the single task that stops (SR19: everything else keeps running).
- Long questions still go in [QUESTIONS.md](QUESTIONS.md); the row links to them.

## How the Architect clears rows
The Architect answers (in QUESTIONS, the PR, or a contract), moves the row to **Cleared** with
the answer's link and date, removes the `needs/architect` label, and updates CURRENT.
Cleared rows older than one run are deleted (git history keeps them).

## Historical lead queue sync — 2026-11-18 19:33 EST

Reviewer #246 instructions read and applied. A14/A16 remain cleared; no new design ruling.
PR #242 now needs independent **reviewer-level** Claude review at
`fd413424197cec2f4ae04c7c866636d4483e41ed`, base
`004a1b469c6d87fb7886f53ca8ac8f4c273eb6d8`; all five recorded workflows completed green.
The queue is its `claude-review/reviewer` label, not a new Architect-only Open row.
The Architect may fulfill that review, or the owner may run claude-reviewer.
B1/B2 test wiring is released under SR8 and needs no Architect ruling.
A3/A4 below retain their original waits. No cleared ruling is reopened.
Lead actions and exact next runs are in CURRENT's Cloud-1 delivery sync.

Signed: codex-lead, 2026-11-18, 19:33 EST

## Open
| ID | Date ET | From | Kind | Urg | Ask (link) | Waits |
|---|---|---|---|---|---|---|
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |
| A29 | 2026-11-21 | gpt-lead | handoff | soon | [OB-g1 #312](https://github.com/kalharbi11/wirescape-lab/pull/312) `445123b31c2a061f0c888cf3fb20508fd59484f4` landed; OB-g4 Pi draft can start under r2.4a. Owner retains merge. **Long run needed** (run 7): the session must add `wirescape-pi`; next long Architect run. | none |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A30 | 2026-11-22 | S6 contract-review; module PRs #325/#333/#334 blocked on frozen S0 catalogue, 34-module counts and Ir | #295 approved and merged `25b1a82`; M1 accepted; [`0020` §7](../../proposals/0020-note-tools-and-gate-delay.md) module-gate ruling. See CURRENT run 7. |
