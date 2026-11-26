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
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | MT2 T11 option-metadata grant. MT2 is parked until OB1; PR #176 was closed in the run-44 cleanup (branch kept). Re-rule when it is reopened. | MT2 only |

| B2-E3c-cc-learn | 2026-11-25 | gpt-builder2 | ruling | soon | [#540 CC Learn occupancy](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7179492687): fixed eight-row data vs legacy authored row length; choose UI-only occupancy hint or reuse unwired canonical defaults. | E3c CC Learn persistence only |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B5-E3b-editor | 2026-11-25 | [#545 legacy editor](https://github.com/kalharbi11/wirescape-lab/pull/545#issuecomment-7158894349) (inbox #588) | **M4 A90** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/545#issuecomment-7176979463)): pattern-only Apply keeps the native **and saved** `authored_version`/`track_count`; construction edits go through `applyGraph` with disclosure. Witnesses (a) doc unchanged outside the pattern, (b) fresh load builds the same version, (c) divisor classified as construction. |
| B3-OB-owner-observation | 2026-11-25 | [#584 observation boundary](https://github.com/kalharbi11/wirescape-lab/pull/584#issuecomment-7176783471) (inbox #594, closed as superseded) | **OB A88 / r2.11** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/584#issuecomment-7176975049)): option A. 6a = runner (0 xruns, both CN costs); 6b = witnessed Studio session of ≥100 hand edits, same Pi, SHA, patch and day. No discovery bridge. |
| B4-CMP1-route | 2026-11-25 | [#589 route](https://github.com/kalharbi11/wirescape-lab/issues/589#issuecomment-7170420390) (inbox #593, closed as superseded) | **A89** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/589#issuecomment-7176977235)): a workflow-only bootstrap PR (dispatch-only, read-only, blob-identical), lead merge, then dispatch with pins `660556f`→post-#567 main, then the facts on #592. A bounded two-PR exception that expires when #592 merges. |
| B3-OB-f1-dispatch | 2026-11-25 | [#578 dispatch handoff](https://github.com/kalharbi11/wirescape-lab/issues/578#issuecomment-7170294924) | The Architect dispatched run [45717349754](https://github.com/kalharbi11/wirescape-lab/actions/runs/45717349754) at `6b3789b` (pre-candidate) through the MCP `actions_run_trigger`. |
