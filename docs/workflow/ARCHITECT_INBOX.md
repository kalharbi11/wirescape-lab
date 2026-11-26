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

| B3-OBh1-dispatch | 2026-11-26 | gpt-lead | execution (no ruling) | soon | #608 merged `48479fc`. [#600](https://github.com/kalharbi11/wirescape-lab/issues/600#issuecomment-7189171083) reopened: run `gh workflow run ob-g7-hosted-soak.yml --repo kalharbi11/wirescape-lab --ref main -f ref=48479fc38d5d1d74eefd0851ff893988d9398220`, post run link/full input pin. Connector cannot dispatch; browser fallback is signed out. No load/gate changes. B3 then verifies four-lane raw artifacts and facts/routing. | #600 |
| B4-CMP1-retention | 2026-11-26 | gpt-lead | execution (no ruling) | soon | [#592 blocked Result](https://github.com/kalharbi11/wirescape-lab/pull/592#issuecomment-7189227965): existing branch `task/589-compare-rebuild`, head `011485b662a7086a98f228fe1cfad832dc7c5c81`. Download artifacts `15106255348`/`15104379390` from run `45791608325`; verify archive and all 33 JSON digests against `facts/compare/rebuild_vs_previous/raw-artifact-manifest.json`; retain exact JSON under its `linux-x64/` and `linux-arm64/` directories. Update retention sentence only after copy, then new exact Lab and Result for lead merge. Artifacts expire Dec 10. Lead API download 403; connector service-file links unreadable from executor. No product changes or rerun. | #592 (then #609) |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B1-A80-review | 2026-11-25 | [#585 Studio A80 client](https://github.com/kalharbi11/wirescape-lab/pull/585#issuecomment-7177065127) (inbox #599, closed) | **Approved and merged `05cf0d7`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/585#issuecomment-7187866441)) at head `73bda36`, base `4a5f2e6`. No High or Medium findings; two optional Lows. The shared RealEngine/App writer is released to #540 and #545. |
| B1-A92-path | 2026-11-25 | [#603 OscOutEditor path](https://github.com/kalharbi11/wirescape-lab/issues/603#issuecomment-7179490547) (inbox #599, closed) | **A96** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/603#issuecomment-7187939926)): `OscOutEditor.ts` granted for preset Save/Load only. The Host field stays the SR21 follow-up after #601. |
| B2-E3c-cc-learn | 2026-11-25 | [#540 CC Learn occupancy](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7179492687) (inbox #607, closed) | **M4 A95** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7187938502)): option B. An unwired default row is free; Learn takes the lowest free index; Forget resets the row. A Studio-only hint is refused (it would make the patch depend on the app). |
