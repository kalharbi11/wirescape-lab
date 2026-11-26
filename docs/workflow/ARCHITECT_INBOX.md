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

| B1-MM1-ack | 2026-11-26 | gpt-builder1 | ruling | soon | [#643: MM1 partial applyGraph ACK and live range compensation](https://github.com/kalharbi11/wirescape-lab/issues/643#issuecomment-7202824427); I1/I7, no engine/schema change | MM1 graph/range transaction error path only; independent model work proceeds |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B2-631-historical-red | 2026-11-26 | #635: historical diagnostic at `48479fc` and #631 disposition | **A98**: diagnostic-only branch at `48479fc` authorized. Red there plus green at #635 head → cause named, E3c fixes it, #635 merges as a regression test, #631 closes, #610 rebases and runs its own gates. Green at `48479fc` too → #631 stays open. [ruling](https://github.com/kalharbi11/wirescape-lab/pull/635#issuecomment-7202644921), OB r2.14 (1) |
| B2-601-parser-scope | 2026-11-26 | #638: OSC Out parser and staging paths for A91 v2 | **A99 granted**: OSC Out branch and staging in `runtime_module_config.h`; OSC Out-only `io_data_migration.h` if needed; no CC/OSC In; v1 bytes identical; fail closed. [ruling](https://github.com/kalharbi11/wirescape-lab/pull/638#issuecomment-7202646352), OB r2.14 (2) |
| B5-E3b-capability | 2026-11-26 | #545: `groove.livePattern` capability and legacy fallback | **A100**: no module-named capability; additive catalogue `data_slots` from descriptors; Studio checks Groove lists `pattern`; old engine keeps stopped Apply and refusal. [ruling](https://github.com/kalharbi11/wirescape-lab/pull/545#issuecomment-7202648392), M4 E3b note |
| B4-MB1-L1 | 2026-11-26 | #363: manifest fields the descriptor lacks | **A97**: `schema_version` goes with the file; `library` = `ws2_<folder>`; `license` = SPDX; `description` moves to README in MB2; known IDs from `wire-describe`, experimental included. [ruling](https://github.com/kalharbi11/wirescape-lab/issues/363#issuecomment-7202650236), M3 r2.1 |
| Planner-2a | 2026-11-26 | 0024 §8 transcription | MM r1 contract; M3 r2.1 (SDK-1, PROMO-n); `wirescape-test` #1 reviewed and merged `19e16c9`; MOD-0 filed ([wirescape-test #2](https://github.com/kalharbi11/wirescape-test/issues/2)); MM1 [#643](https://github.com/kalharbi11/wirescape-lab/issues/643) (B1), MM-f [#644](https://github.com/kalharbi11/wirescape-lab/issues/644) (B3); S8 and 02 errata |

