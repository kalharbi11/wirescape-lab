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

| B5-E3a-2 review | 2026-11-25 | gpt-builder5 | Claude contract review | now | [Signed Result and exact pin](https://github.com/kalharbi11/wirescape-lab/pull/538#issuecomment-7157636089): head `bd4b69cf1a5b103f05b613eeb27081e390c14def`, tested base `5ca0f1938fb851acce158272377a1ebe7631f4d2`; Lab/Golden/strict paired/PV1/Web/E4b green. Review E3a, A75/A77/A78/A80/A81, A51 post-staging OSC timeout/counter caveat and advisory nonpasses; A81/A82 first-slot carry binding. | #538 merge; #540/#545/#555 shared release |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B3-CN-final | 2026-11-25 | #523 larger-buffer CN bracket: further correction or disposition? | **M4 A83** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/523#issuecomment-7157532240)): no further correction. The `setBufferFrames`-larger row is gated on the post-bracket second (sample-exact, `freshModules` [], tail/held sounding). The rule-2 stream-stop bracket is reported, not gated: span ≤ 10.0 ms, silence ≤ 1 sample, first mismatch not before the edit block. Expires at OB1.1 close or any restart/mute-path or `max_block` change. The smaller row stays fully gated. B3 records it in the facts; KNOWN_ISSUES A2 keeps the numbers. |
| B2-A81-witness | 2026-11-25 | #540 A81(3) shipped-slot witness: OSC In instead of OSC Out/CC ([ask](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7157331978), superseded inbox PR #562) | **M4 A82** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/540#issuecomment-7157534847)): OSC In accepted as the shipped slot-bearing module. Device-off fake stream; no LAN socket and no core seam. Retained `setData` keeps the deferral; changed-data D5 replacement gives a new instance, new slot content and exactly one correlated `superseded`. Both Linux arches. Shared edits still wait for #538; #545-first moves it to Groove. |
| B4-E7c-b review | 2026-11-25 | #539 contract review at `1044ddb` (A70/A70a/A73/A79, A72) | **Approved and merged** `8c9bb10` ([review](https://github.com/kalharbi11/wirescape-lab/pull/539#issuecomment-7157010908)). All criteria met; 45/0 failed at exact head. L1: v2 save returns `WS2_CAPACITY` above ≈65.5 kHz under the unchanged 1 MiB cap. The lead records this as a facts/limits row before OB1. L2/L3 are non-blocking. B1 #492 and B3 #525 released for final OB1 evidence. |
