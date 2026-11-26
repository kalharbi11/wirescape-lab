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
| B4-CMP1-retention | 2026-11-26 | gpt-lead | execution (no ruling) | soon | [#592 blocked Result](https://github.com/kalharbi11/wirescape-lab/pull/592#issuecomment-7189227965). **Run 47:** the GitHub MCP returns signed download URLs for artifacts `15106255348`/`15104379390` (run `45791608325`, expire **2026-12-10**), but this Architect session was not permitted to download them. **Owner step (2 min):** download both zips from the [run page](https://github.com/kalharbi11/wirescape-lab/actions/runs/45791608325) and attach them to #592 (or let an authenticated `gh run download 45791608325` session do it); B4 then verifies the 33 JSON digests against `raw-artifact-manifest.json` and retains them. If still blocked, B4 starts MB1 #363 first (0023 R3.1). | #592 (then #609) |
| B1-RS-modal | 2026-11-26 | gpt-builder1 | ruling | now | [#621 scope question](https://github.com/kalharbi11/wirescape-lab/issues/621#issuecomment-7201035592): App.ts independently opens recovery-modal on every unexpected engine exit; request supervised desktop exit guard only, preserving unclean-app and legacy recovery. Resolve SR21 against B2 #540 and B5 #545 writers. Fail-first [#624](https://github.com/kalharbi11/wirescape-lab/pull/624) `abfab0516837eab0d9242985fbe0edc7b8088b39` checks seeded autosave plus non-modal UI. | RS #621 final UI integration; supervisor/banner continue |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B3-OBh1-dispatch | 2026-11-26 | Dispatch `ob-g7-hosted-soak.yml` at `48479fc` for #600 | **Dispatched** run [45877224981](https://github.com/kalharbi11/wirescape-lab/actions/runs/45877224981) (workflow from `main` `337d8e8`, `ref=48479fc38d5d1d74eefd0851ff893988d9398220`) ([#600 comment](https://github.com/kalharbi11/wirescape-lab/issues/600#issuecomment-7200746558)), run 47. B3 audits. |
| Planner run 1 | 2026-11-26 | Verify 0023, file its tasks, end wrap-up (§8) | **Transcribed** in run 47: M3 r2, M7 r1.7, OB r2.13 (+Gate P0 rows), STANDING SR22–SR25, CI-S1–S3 applied, issues #363/#358 reopened, #619–#622 filed, BUILDERS refreshed. One cite error (R2.5 `RealEngine.ts:300-304` → `:393-436`); rulings unaffected. |
