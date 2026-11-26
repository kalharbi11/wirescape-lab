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
| B2-631-historical-red | 2026-11-26 | gpt-builder2 | ruling | now | [#635 request](https://github.com/kalharbi11/wirescape-lab/pull/635#issuecomment-7202403530): post-E3c forced poll and original gate green at `2c9d09a50e7070f578beffa664f3bc7e0db38209`; authorize historical diagnostic red at `48479fc` and disposition if E3c already fixes race | #631 / #610 |
| B2-601-parser-scope | 2026-11-26 | gpt-builder2 | ruling | soon | [#638 request](https://github.com/kalharbi11/wirescape-lab/pull/638#issuecomment-7202416263): grant OSC Out-only real document parser/staging paths for A91 v2; draft test head `efd4cfa4a3802b6cb64c96e60631f2d2ba44c836` | #601 implementation |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B2-E3c-review | 2026-11-26 | #540 contract review (A81/A82/A86/A95, G1–G9), head `65a3eb8` | **Approved for merge 65a3eb8**, merged `f8c994c`. No High or Medium findings; 4 Low (OSC In render-side compile on serial change, invalid-pattern fallback, missing A95 red-first witness, lost-ACK follow-up). The `ccMap.set` golden `gen` `=` is the E3c criterion, with the spec changed in the same PR. [review](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7201383615) |
| B5-OBh3-gate | 2026-11-26 | #610 sole red `abi2_midi_egress_gate_tests` `unexpected_gate_edge: 1` | **Real egress defect** (the oracle records the expected edge before sending, so the sidecar emitted an extra rise). Fix owner B2, [#631](https://github.com/kalharbi11/wirescape-lab/issues/631), red-first on `f8c994c`. #610 holds; no rerun or waiver. [ruling](https://github.com/kalharbi11/wirescape-lab/pull/610#issuecomment-7201406602) |
| B4-CMP1-merge | 2026-11-26 | #592 lead merge | Result and exact-head Lab (facts-only) green at `4026404`; marked ready, auto-merge on. |
