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
| A31 | 2026-11-23 | owner | blocker (Pi) | later | wirescape-pi hosted jobs cannot run: (1) Actions minutes are used up until 2026-11-30; (2) the `WIRESCAPE_LAB_TOKEN` secret returns 401 and the owner replaces it; (3) the Pi runner may need re-registering. Keep this row Open until a `/pi-run` round-trip works. **Run 19b: [PI-1 #369](https://github.com/kalharbi11/wirescape-lab/issues/369) removes (1) and (2): dispatch and publish move to the lab, and the private repo needs no hosted minutes. It waits for the owner's token setup.** | Pi runs only (advisory, OB r2.4a) |
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A33 | 2026-11-23 | T1.6b #360 contract-review (CB1) | Approved and merged `7cc20c7` ([review](https://github.com/kalharbi11/wirescape-lab/pull/360#issuecomment-7107143632)). 2026-11-23 |
| A32 | 2026-11-23 | CB1 escalation on #333: LFO +1.9/+2.1 % on x64 from SDK-wrapper inlining in the catalogue TU | Run 16: SDK pinning only moves the cost, so CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358) gives one TU per module. #333 merges with a bounded exception (two LFO rows, x64, up to +2.5 %, expires at CAT-1). [`0020` §7](../../proposals/0020-note-tools-and-gate-delay.md). 2026-11-23 |
