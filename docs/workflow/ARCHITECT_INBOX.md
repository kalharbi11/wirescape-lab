<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

The Claude Architect performs all independent and Claude contract reviews under the owner's
2026-11-24 direction. Give each ready review an Open inbox row and `needs/architect`. Keep
`review-required` while it gates a merge. Pin full tested base/head SHAs, invariants and evidence
on the PR. Architect independence and all contract gates still apply. The owner or lead may
apply `architect-ready` once on one linked ready issue at the end of a verified batch. That
wake serves the whole inbox. The owner may also run `architect:run` manually.

Builders add or update one inbox row for a merge-ready review, ruling or Architect question.
Use a docs PR, identify the exact head and the task that waits, and preserve the pinned Result.
Only the owner or delivery lead applies an Architect trigger label.

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
| A31 | 2026-11-23 | owner | blocker (Pi) | **postponed to OB1 candidate** (OB r2.6) | wirescape-pi hosted jobs cannot run until the private repo's Actions minutes return (2026-11-30), the runner is re-registered, and PI-1 [#369](https://github.com/kalharbi11/wirescape-lab/issues/369) (lab-side dispatch/publish, owner token `PI_BRIDGE_TOKEN`) lands. **Interim (run 44):** Pi evidence comes from owner-run `tools/owner_record.py` zips uploaded to [#590](https://github.com/kalharbi11/wirescape-lab/issues/590), plus hosted Linux arm64 CI. Keep this row Open until a `/pi-run` round-trip works. | Pi runs only (advisory, OB r2.4a) |
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | MT2 T11 option-metadata grant. MT2 is parked in the lab (0023 §7.1; module tooling grows in `wirescape-test`); PR #176 was closed in the run-44 cleanup (branch kept). Re-rule when it is reopened. | MT2 only |

| B5-X1-review (#762) | 2026-11-28 | gpt-builder5 | Claude contract review | soon | A120 deterministic CPU probe; exact head `7352de45b6b9a2b83f7b058e9945783a25c0532f`, [signed Result + all row deltas](https://github.com/kalharbi11/wirescape-lab/pull/762#issuecomment-7239806491); all gates green; confirm attribution/boundary suffices | X2 #760 |


## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B1-SDK1-review (#731) | 2026-11-28 | gpt-builder1: SDK-1 Architect review at `49db5f7` | [Approved](https://github.com/kalharbi11/wirescape-lab/pull/731#issuecomment-7239495073); merged `869e088` (run 60). **M3 accepted.** One Low (restore cross-field checks). |
| B6-MB3-catalogue (#742) | 2026-11-27 | gpt-builder6: presentation-overlay proof for MB3 | **A122** [ruling](https://github.com/kalharbi11/wirescape-lab/pull/764#issuecomment-7239497613): confirmed; #764 merged as lead `6d50a9f`. |
| SC2-Linux-wake (#763) | 2026-11-28 | gpt-builder2: Linux ASan wake-only soak failure | **A121** [ruling](https://github.com/kalharbi11/wirescape-lab/pull/763#issuecomment-7239499352): not SC2; SR5 fact + X3 [#776](https://github.com/kalharbi11/wirescape-lab/issues/776); SC2 integrates main, fresh full run. |
