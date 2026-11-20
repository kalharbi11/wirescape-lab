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
| A4 | 2026-11-17 | Architect | errata review | soon | #186 must **not** be closed: it carries 0017 §5 errata not on `main` (0012 load/rate, 0014 fallback/Transport, 0016 T1 ids/lazy metrics; M6 r3, M8 r2, M10 r2, M11 r2). **Long run needed:** OB0 is now accepted. Rule each erratum before any of MT4, H3a, CP1, K3 or K4 is dispatched; best during the S6 window, when no other product writer runs. | MT4/H3a/CP1/K3/K4 dispatch only |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A21 | 2026-11-20 | B3 #291: S7.5 Ir +12–16 % over M7's +3 % cap, ledger 2/2 | **Cap not raised.** Architect correction `cdf666c` (per-block mode paths, local voice state; bit-identical renders). Local Ir vs base −3.8 % to −20.7 % on all five rows. CI at `cdf666c`, D5 and an independent K1–K8 review are still needed. [Ruling](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7046424106), M7 r1.3(c). |
| A22 | 2026-11-20 | Architect finding: T7.0 switch rows hit the stimulus floor | M7 r1.3(a,b): click targets are also met at the no-switch floor (±0.1 dB). S7.5 is met (−38.443 = floor). T7.0b [#296](https://github.com/kalharbi11/wirescape-lab/issues/296) (B2) adds floor and excess, and a Delay window. **S7.6 waits for #296.** |
| A23 | 2026-11-20 | A20 follow-up: OB-f2 targets from OB-f1 (#216 merged `c6ae30a`) | OB r2.3: p95 ≤ 17.5 ms, max ≤ 33.4 ms per row, ACK p95 ≤ 5 ms. All already met on CI, so no OB-f2 fix task. Re-check at the OB1 candidate; the Pi session decides. |
| A24 | 2026-11-20 | A18 kit: W1 #293 / W2 #290 | W2 4/4 device-off round trip (blocked builder evidence supplied); W1 loadGraph-capability defect fixed (`4869218`), loopback PASS. Both merged (`c974ba5`, `9448843`). W3 audit read; W4 stays reserved. |
