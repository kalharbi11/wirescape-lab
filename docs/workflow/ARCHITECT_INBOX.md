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


| SC2-Linux-wake (#763) | 2026-11-28 | gpt-builder2 | ruling | soon | [Blocked Result](https://github.com/kalharbi11/wirescape-lab/pull/763#issuecomment-7239334457): base `ce3cca83bdaa97fe2a8df0abf9e41f3fe2fb851c`, head `54a141252291593d05d9aa34c437ad1392cf8f41`; Golden green, latest Linux sanitizer no-OSC soak wake-only failure after prior green. SR5: request bounded base/head diagnosis or neutral follow-up; no waiver/retry expansion. | SC2 #721, then TR1h #740 |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| SC1-review (#685) | 2026-11-27 | gpt-builder5: SC1 contract review at `62b4219` | [Approved](https://github.com/kalharbi11/wirescape-lab/pull/685#issuecomment-7228382595); merged `23f3fe2` (run 59e). Two Lows: inline card styles, option casing. |
| B1-MB2-final (#725) | 2026-11-27 | gpt-builder1: MB2 contract review at `ed33428` | [Approved](https://github.com/kalharbi11/wirescape-lab/pull/725#issuecomment-7229543648); merged `027db95` (run 59f), with **A120** bounded for x64 `osc.out/voices8` ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/725#issuecomment-7229995026)). Follow-up X1 #759. |
| B1-MB2-residual (#725) | 2026-11-27 | gpt-builder1: Output/Groove still miss the paired gate after A118 | **A119** [ruling](https://github.com/kalharbi11/wirescape-lab/pull/725#issuecomment-7228142460): attribute in the formal configuration (the diagnostic driver does not reproduce x64). The A118 hoist is granted for `modules/output/dsp.h` and `modules/groove/dsp.h` **only if** the excess is in the module's own `process`, with bit-identical goldens. If the excess is outside module code, stop and report back. No waiver. |
| B1-MB2-finiteness (#738) | 2026-11-27 | gpt-builder1: `finite_samples` regression | **A116** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/358#issuecomment-7225734313): the contracted fallback first; a noinline pin on `finite_samples` only if the fallback misses. No flags, thresholds or exceptions. |
| SC2-worker-scope (#737) | 2026-11-27 | gpt-builder2: SC2 paths and count semantics | **A117** [ruling](https://github.com/kalharbi11/wirescape-lab/issues/721#issuecomment-7225734569): `host/net/osc_service` and `engine/control/osc_host` granted (worker telemetry only). Count at match time, before refusal, address-only. Starts after #685 **and** MB2 merge. |
