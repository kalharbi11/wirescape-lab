<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

A planned review condition goes on the task with `review-required`. Open an Architect-only
review row when its request is ready to dispatch. **Do not add `review-ready` to it** (that starts the regular
cloud reviewer); the lead dispatches it with `architect-ready`. Routine independent review uses
`review-ready` and a pinned PR request naming the eligible reviewer, without an inbox row.

A row and its labels record the decision or review request. When the item is ready, the delivery lead adds
[`architect-ready`](README.md#architect-dispatch-architect-ready) to the most urgent one (one per lead run); that
starts an Architect run, which clears every ready Open row. The Architect removes the label when done.

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
| A31 | 2026-11-23 | owner | blocker (Pi) | **postponed to OB1 candidate** (OB r2.6, owner 2026-11-23) | wirescape-pi hosted jobs cannot run: (1) Actions minutes are used up until 2026-11-30; (2) the `WIRESCAPE_LAB_TOKEN` secret returns 401 and the owner replaces it; (3) the Pi runner may need re-registering. Keep this row Open until a `/pi-run` round-trip works. **Run 19b: [PI-1 #369](https://github.com/kalharbi11/wirescape-lab/issues/369) removes (1) and (2): dispatch and publish move to the lab, and the private repo needs no hosted minutes. It waits for the owner's token setup.** **Interim, allowed (owner question, 2026-11-23):** an agent running on the Pi as `wsci` may run `ci/sandbox.py` (CURRENT run 10c command), which keeps lab code inside podman. It posts `result.json` as a lab comment through its own app connection, with the SHA, Pi and date. The agent never runs lab code outside the sandbox and never gets the Pi user's own credentials. | Pi runs only (advisory, OB r2.4a) |
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |

| A38 | 2026-11-23 | gpt-lead | contract-review | now | [TR1e #385 signed Result](https://github.com/kalharbi11/wirescape-lab/pull/385#issuecomment-7118746129) at `5d2d78b432179687a1d9bab11ad1dc1ab3938f38`. Architect review M3 TR1e, ER1 and 0008 K1/K2/K4. | TR1e merge and E6 release |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A37 | 2026-11-23 | S7.7 #380: frozen S4 whole-graph reference; VCF cost vs the 1 % rule | [M7 r1.5](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7118689012): retire only the S4 ABI1 bound (all other assertions stay); VCF-containing rows fall under the +5 % task cap with `Cost-change:`; other rows stay at 1 %. 2026-11-23 |