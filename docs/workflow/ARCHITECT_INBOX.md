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
| B1-S7.6 review | 2026-11-25 | Architect (run 37) | review | **now** when B1 posts its Result | [#449](https://github.com/kalharbi11/wirescape-lab/pull/449) at **`ae8453a`**: all exact gates are green (Golden 3/3 platforms identical, strict paired 3/3, Ir, Lab). Waiting on B1 to revalidate A27/D5 and post a signed Result, then the S7.6 review. **Disclosure:** the Architect wrote `c951a47` and `ae8453a` (A72); Golden identity and paired cost are the objective checks. | S7.6 merge → B4 E7c-b #520, #456, #492 |
| B2-E7b review | 2026-11-25 | gpt-builder2 | review | **now** when ready-head gates qualify | [#504 combined voice witness](https://github.com/kalharbi11/wirescape-lab/pull/504#issuecomment-7154349730) head `aed62fbe5d89f9a1d42f649590ce5d059ca86cdf`, base `9db59967778a0d6598916e9c4068a3edc248a2de`: actual fail-first and all three native + ASan green. Ready Lab 45557461661, Golden 45557461619, strict paired 45557461627 pending; signed final Result after gates. Run37b requests review; no Delay waiver. | #504 merge → B3 CN and B5 #522 |

| B5-E3a-1 review | 2026-11-25 | gpt-builder5 | review | **soon** (OB1.1, not tag-holding) | [#515 signed Result and contract-review pin](https://github.com/kalharbi11/wirescape-lab/pull/515#issuecomment-7154483044), head `ee3a9dc8de9f16210cfc1049c7cf73694faf7e0f`, tested base `b61c9898cabb81dec92adf1259a723e90558e058`; ready Lab, Golden 81/81, strict paired 100 measured/2 known unavailable/0 failures each Linux, ASan/TSan stress green. Review M4 G1–G9, ER1/ER2/ER4, 0012 §4 and A75; no E3a-2 waiver. | #515 merge → B5 E3b draft; #522 independently waits #504 |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B4-E7c-a review | 2026-11-25 | #507 short Architect review at `398e426` | **Approved and merged** `9db5996` ([review](https://github.com/kalharbi11/wirescape-lab/pull/507#issuecomment-7154064273)); Lows L1/L2 are follow-ups. #504 released. |
| B5-ER2 bound | 2026-11-25 | #512 overlapping same-ID replacement | **M4 A75**: refuse atomically as busy until the fade retires; the host coalesces the latest config (E3a-2 #522) ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/512#issuecomment-7153340161)). |
| B3-CN routing | 2026-11-25 | #523 composed CN witnesses | **M4 A76**: final-pin #504 Lab assertions plus the A62 trace; #485's witness stays valid only if the replacement path is unchanged, otherwise rerun at the final pin (pin-only grant) ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/523#issuecomment-7153964247)). |
| B1-S7.6 Golden | 2026-11-25 | #449 Linux Golden red, SR6 round 2 | **M7 A72**: cause is FMA contraction in the new loop shape, not changed arithmetic. Reproduced locally; the Architect pushed `c951a47` (verbatim settled loop, per-sample hand-off) ([fix](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7153140329)). |
| B4-A70a fresh config | 2026-11-24 | #503/#507 fresh Keyboard config validation | **M4 A73**: fresh staging authorized, plus one differing-controls test; E7c split into E7c-a (voice chain, now) and E7c-b (Delay v2, after #449) under SR21 ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/503#issuecomment-7153159708)). |
| B2-A67 capacity | 2026-11-24 | #494/#497 natural WS2_CAPACITY refusals | **OB-g A74**: one opt-in diagnostic stage on draft #497, at most two matrix runs, never merged; park advisory if no cause ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/494#issuecomment-7153160751)). |
