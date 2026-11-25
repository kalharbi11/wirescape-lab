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


## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| S7.5 H1 | 2026-11-24 | #291 `a875881` independent re-review | **Approved and merged** `6daa23e` ([review](https://github.com/kalharbi11/wirescape-lab/pull/291#issuecomment-7151194472)). H1 closed; Low L1 (regrown voice keeps its prime bit) is deferred. |
| A65 | 2026-11-24 | #444 `c86810e` S7.9 contract-review | **Approved and merged** `1be9da2` ([review](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7151198161)). x64 LFO reds are within r1.6. L1 (VCO sounds after CHOKE) is an OB-d note. |
| A66 | 2026-11-24 | #467 advisory Windows facts failure | **Handled separately**: the failure was in the libremidi fetch, before any collector, on an evidence-only PR. #467 merged `c6a585a`; the fix is B3 [#487](https://github.com/kalharbi11/wirescape-lab/issues/487). |
| A67 | 2026-11-24 | #463 hosted enqueue fix routing | **B2**, after E7b #486 and #482. One issue: same load and limits, fail-first, A61/A58. It does not hold the OB1 tag ([comment](https://github.com/kalharbi11/wirescape-lab/issues/475#issuecomment-7151232808)). |
| A64 follow-up | 2026-11-24 | #314 division target-control validity | **Ruled, M7 r1.9** ([comment](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7151227766)): a peak ≤ old floor + 0.1 dB meets; division meets; the steady-state check applies only above the old floor. |
| A68 | 2026-11-24 | #474 larger-buffer M4 acceptance | **Ruled, M4 A68** ([comment](https://github.com/kalharbi11/wirescape-lab/pull/474#issuecomment-7151226018)): smaller met, larger not met. The fix is E7b [#486](https://github.com/kalharbi11/wirescape-lab/issues/486) (B2, engine prepared for 1024); B1 reruns after. |
| B5-CN | 2026-11-24 | #480 E5 adopt seam and transition-cost method | **Ruled, M4 A69** ([comment](https://github.com/kalharbi11/wirescape-lab/issues/480#issuecomment-7151224251)): bench-only seam, per-block callgrind `Ir`; E5 merge waits on review, not on CN rows. |
