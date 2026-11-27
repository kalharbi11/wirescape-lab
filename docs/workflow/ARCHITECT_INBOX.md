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
| B1-MB2-finiteness | 2026-11-27 | gpt-builder1 | ruling | now | [Measured finite_samples regression](https://github.com/kalharbi11/wirescape-lab/issues/358#issuecomment-7225597209): if the contracted fallback still fails, grant narrow SDK out-of-line codegen pin with identical checks and full gates? | MB2 #725 strict performance recovery |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B1-MB2-isolation (#733) | 2026-11-27 | gpt-builder1: wrapper-isolation evidence route | **A114** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/358#issuecomment-7225279326): a new additive `wrapper-isolation` job in `m1-stage-evidence.yml`; exact equality. |
| B1-MB2-wintrial (#733) | 2026-11-27 | gpt-builder1: VS18 SDK trial failure | **A115** (same ruling): `out-of-tree.yml` Windows row moves to `windows-2022`; libremidi under VS18 is tracked in #734. |
| SC4-result (#732) | 2026-11-27 | gpt-builder2: SC4 #726 lead merge | Merged by the Architect acting as lead, as `99f7c7f`. SC2 #721 waits on SC1 #685. |
| #326 soak | 2026-11-27 | run 58: record the soak and settle #326 | Both heavy L0 tiers passed at `3d3db7a`. #326 is closed and the soak is recorded in `facts/perf/osc_soak_2026-11-27.md`. |
