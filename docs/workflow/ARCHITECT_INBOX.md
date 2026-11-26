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

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B5-E3b-review | 2026-11-26 | #545 E3b contract review | **Approved for merge `638d8b6`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/545#issuecomment-7205331364)): G4/G6/G7, A90 (a)–(c), A100 met. Medium follow-up: no `sequencing.groove` branch in `session.cpp` (route through the per-type dispatch) before MB2. Branch updated, auto-merge on |
| B3-604-render-timing | 2026-11-26 | #648 renderer timing scope | **A102** granted: opt-in timing in `tools/render/main.cpp` plus its CTest; with the flag unset, PCM and stdout stay byte-identical. [ruling](https://github.com/kalharbi11/wirescape-lab/pull/648#issuecomment-7205338334) |
| B4-MB1-A97-followup | 2026-11-26 | #363 SDK prefix and offline reader | **A103**: SDK examples keep `ws2_example_<folder>` (MB1 asserts, MB2 preserves); `bench/offline` keeps its 33 IDs, and widening is a separate contract. [ruling](https://github.com/kalharbi11/wirescape-lab/issues/363#issuecomment-7205339238) |
| B2-620-host-scope | 2026-11-26 | #620 P0b host wrapper scope | **A104**: `midi_host` and `osc_host` lifecycle and health plus one bounded control-thread accessor; `osc_out_host` and `osc_service` only with a named red test; freezes kept. [ruling](https://github.com/kalharbi11/wirescape-lab/issues/620#issuecomment-7205340357) |
| Planner-implementation | 2026-11-26 | wirescape-test #4, #652, limitations | wirescape-test #4 reviewed (separate session) and merged `1f94fa5`; **#652 closed**. MOD-1 #9, MOD-2 #10, MOD-3 #11 and MOD-5 #12 reviewed; #9, #11 and #12 merged; #10 merges on T1 green. MOD-3a [test #13](https://github.com/kalharbi11/wirescape-test/issues/13) (beat-clock reset fix) and MOD-4 [test #14](https://github.com/kalharbi11/wirescape-test/issues/14) filed. Limitations routed: #663 → B5, #664 and #665 → B4 (after their current PRs) |
| MM-macro-labels | 2026-11-26 | Macro `labels.rows` length | Note for MM (no ruling needed): the pinned renderer refuses a `labels.rows` with fewer than 8 entries, so MM writers (Studio and the Player) always write all 8 rows. Empty names mean the defaults (0024 §3.1) |

