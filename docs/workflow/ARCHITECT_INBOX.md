<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

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

## Open
| ID | Date ET | From | Kind | Urg | Ask (link) | Waits |
|---|---|---|---|---|---|---|
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |
| A4 | 2026-11-17 | Architect | cleanup | later | #186 old succession docs PR: close or refresh after #215 lands. | nothing |
| A10 | 2026-11-17 | gpt-lead | oracle ruling | now | #223: six OB-c gap/click/lag oracles remain unanswered. Former lead A8 carried here because Architect reused A8 for190. B1 source inventory available on214; no invented thresholds. | six-case207 acceptance |
| A11 | 2026-11-17 | gpt-lead | stage release | now | #199:190/S4 merged8c72722 at reviewed26c749d, all checks green. Release scoped S5a; B4 parked. claude-review/architect applied. | S5a implementation |
| A12 | 2026-11-17 | gpt-lead | reserved measurement meaning / scope | now | #230 pinned53317f0 measures2127bde1ee; define pitch applicability for noise/inharmonic models without invented zeros. Dispose of Claude Medium212 wider8–192k supported-rate finding. Exact criteria/comment on230; claude-review/architect applied. | affected S7.4 numeric acceptance |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A8 | 2026-11-17 | owner | check | now | #190: why it isn't merged | **Architect side done** at `26c749d`: the fixture bytes match exactly and every assertion stays. Merge waits on `facts` ×3 green plus the independent M1 review; then the lead merges. See CURRENT 21:50. |
