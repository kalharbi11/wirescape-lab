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
| A14 | 2026-11-18 | gpt-lead | M2 acceptance | now | [#235](https://github.com/kalharbi11/wirescape-lab/issues/235): report232 mergedd048049 after reviewed48f913c notes CI; decide M2r4 criteria1–4/J1–J5 with all Q22/D08/D09 exceptions. claude-review/architect applied. | M2 milestone acceptance only |
| A15 | 2026-11-18 | gpt-lead | S5a path ruling | now | #234: config-only CLI main/play outside row; clarify Golden/soak test consumers and stale web CMake reference. Four-path exception exceeds SR7 limit; exact proposed grant in signed issue comment. claude-review/architect applied. | S5a full implementation |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A10 | 2026-11-17 | #223 six OB-c oracles | Per-case oracles, OB r2.1; CURRENT 23:40. Strict xfail until fixes after S6. |
| A11 | 2026-11-17 | #199 release S5a | **Released** to B4 with order rules; CURRENT 23:40. |
| A12 | 2026-11-17 | #230/#212 Macro pitch meaning + 8–192 kHz Medium | Defined-pitch rule from 48 kHz data, M7 r1.2; Medium non-blocking; CURRENT 23:40. |
| A13 | 2026-11-17 | Claude reviews #213, #184 | #213 approved `00664a1`; #184 High (damping fit at default only), M7 r1.2 S7.1. |
