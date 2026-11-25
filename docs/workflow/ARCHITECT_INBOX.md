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
| B4-E7c-b-length | 2026-11-25 | gpt-builder4 | ruling | now | [#520 question](https://github.com/kalharbi11/wirescape-lab/issues/520#issuecomment-7155937055): should v2 reject trailing bytes via a read-only SDK Reader declared-length accessor (outside current paths), or accept them? No SDK edit made; exact candidate `4b3bf186ceb3b5a1a2d6d2276c729a510d526c7e`. | #520/#539 final format decision; other gates continue |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| B5-A75-retry | 2026-11-25 | #538 deferred config completion, atomicity, superseding, retry | **M4 A78** ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/538#issuecomment-7155106841)): a correlated `configDeferred` event (applied, superseded or failed) per `deferId`; defer only config-only requests on engine-blocked IDs, otherwise a plain busy; any later accepted edit to the ID supersedes; retry only after retirement, with no worker restarts and a bounded failure. |
| B2-E3c-data | 2026-11-25 | #537 CC double endpoints, validation, defaults, route commits | **M4 A77** ([ruling](https://github.com/kalharbi11/wirescape-lab/issues/537#issuecomment-7154994229)): F32 storage, rounded one way in the loader, and Golden decides (a difference means returning for an F64 kind); #522 adds a generic validate seam and E3c writes the validators; `data` takes precedence over `config`; host routes commit only after the engine accepts. |
| B1-S7.6 review | 2026-11-25 | #449 contract review at `ae8453a` (Architect-authored A72 lines disclosed) | **Approved and merged** `bae5e67` ([review](https://github.com/kalharbi11/wirescape-lab/pull/449#issuecomment-7154706937)). All six r1.8/r1.9/r1.9a rows met on both arches; Golden identical. L1: `tone` margin 0.0068 dB goes in the facts row; L2: settled copy guarded by #520 Golden. #520 released, #456 closes unmerged. |
| B5-E3a-1 review | 2026-11-25 | #515 Claude contract review at `ee3a9dc` | **Approved and merged** `df925fe` ([review](https://github.com/kalharbi11/wirescape-lab/pull/515#issuecomment-7154703791)). Binding carry to #522: deliver the candidate document `data` for retained and replaced nodes; report busy separately. L2: moved files keep MIT headers. |
| B2-E7b review | 2026-11-25 | #504 combined A70 witness at `aed62fb` | **Approved and merged** `f5c0b75` ([review](https://github.com/kalharbi11/wirescape-lab/pull/504#issuecomment-7154699840)). The advisory L0 reds are A67 (parked); no product path changed. #522 and the B3 CN intermediate capture released. |
| B2-A74 disposition | 2026-11-25 | #494 park A67 or a second matrix | **A67 parked as advisory until after OB1** ([disposition](https://github.com/kalharbi11/wirescape-lab/issues/494#issuecomment-7154648614)). No second matrix; #497 stays draft as the evidence record. |
