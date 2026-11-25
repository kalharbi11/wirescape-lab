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
| A31 | 2026-11-23 | owner | blocker (Pi) | **postponed to OB1 candidate** (OB r2.6, owner 2026-11-23) | wirescape-pi hosted jobs cannot run: (1) Actions minutes are used up until 2026-11-30; (2) the `WIRESCAPE_LAB_TOKEN` secret returns 401 and the owner replaces it; (3) the Pi runner may need re-registering. Keep this row Open until a `/pi-run` round-trip works. **Run 19b: [PI-1 #369](https://github.com/kalharbi11/wirescape-lab/issues/369) removes (1) and (2): dispatch and publish move to the lab, and the private repo needs no hosted minutes. It waits for the owner's token setup.** **Interim, allowed (owner question, 2026-11-23):** an agent running on the Pi as `wsci` may run `ci/sandbox.py` (CURRENT run 10c command), which keeps lab code inside podman. It posts `result.json` as a lab comment through its own app connection, with the SHA, Pi and date. The agent never runs lab code outside the sandbox and never gets the Pi user's own credentials. **2026-11-24:** owner is re-registering the runner and creating the PI-1 token (`PI_BRIDGE_TOKEN` in lab Environment `pi-bridge`, main only). | Pi runs only (advisory, OB r2.4a) |
| A3 | 2026-11-17 | gpt-lead | ruling (optional) | later | #176 MT2 T11: neutral adapter/describe option-metadata grant + option-mutant regression, or a contract disposition. MT2 is parked until OB1. | MT2 only |

| B4-A85-line99 | 2026-11-25 | gpt-builder4 | ruling | soon | [#576: extend A85 to sixth same-value min/max line, CV to Notes line 99](https://github.com/kalharbi11/wirescape-lab/issues/576#issuecomment-7158414743); full failed diagnostic `b1c8915e7813db06defdc323137e29f93f61bbe4`, draft fix `11c126f9aa7b1b9b15586d26854dc169603b99da` | S2a #580 / S2 #567; not OB1 |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B4-S2-arm | 2026-11-25 | #564 ARM compile failures in five portable modules ([ask](https://github.com/kalharbi11/wirescape-lab/issues/564#issuecomment-7158295457), superseded inbox PR #575) | **M10 A85** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/564#issuecomment-7158346297)): a real portability defect (`uint32_t` is `unsigned long` on ARM, so `std::min/max` deduction fails). New task **[#576](https://github.com/kalharbi11/wirescape-lab/issues/576) M10 S2a** (B4): same-value typing on the five lines only, Golden identical, G8, lead merge. #567 measures the host rows now; its ARM rows stay unmeasured, and the step stays red until #576 merges and portability reruns. Not an OB1 blocker. |
| B5-E3a-2 review | 2026-11-25 | #538 E3a-2 contract review at `bd4b69c`; A51/A78(2) OSC counter reset after post-staging timeout | **Approved and merged `4f0bf18`** ([review](https://github.com/kalharbi11/wirescape-lab/pull/538#issuecomment-7158068546)). **M4 A84:** no correction before merge. OSC now pauses only at the post-staging hook or before D5; a timed-out publication exposes nothing (A51), and OSC restarts against the committed document, so routes, data and the document are unchanged (A78(2)). The counter restart is telemetry only. OB-g7 config-edit drops = A67 class (parked), and the instruction advisory is outside G8; both recorded apart from the gates. A81(3)/A82 carry binds #540 (or #545 if first). |
