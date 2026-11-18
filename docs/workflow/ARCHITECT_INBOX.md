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

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A6 | 2026-11-17 | #219 S7.4: old Macro non48-rejection integration test; non48 pitch/Ir evidence | **Granted, bounded** (M7 r1.1). Rewrite only the Macro off-rate block of `qt_free_patch_coverage_tests.cpp` to assert load + render OK at 44.1/96 kHz (finite, 0 allocations, 0 faults); keep the failed-load-leaves-graph-renderable check with another genuine refusal cause. Writer: whoever the lead hands the one file to (B4 by default). Evidence packet for B2 approved; no synthetic values. See CURRENT. |
| A7 | 2026-11-17 | #190: encoded fixture + bounded unpack wiring for the frozen ABI2 capture | **Granted, bounded.** Raw binary (A1) stays first choice; the encoded route is equal if the decoded bytes match. Existing `zlib9+b64` entry shape and `decode_case` checks; new file under `native/tests/fixtures/abi2/`; old corpus untouched. Bytes come only from artifact 14352740696. Transport (403/503 in cloud) is not solved by this; owner or a local session fetches. See CURRENT. |
