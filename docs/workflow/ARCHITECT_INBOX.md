<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

A planned review condition goes on the task with `review-required`. Open an Architect-only
review row when its request is ready to dispatch. **Do not add `review-ready` to it** (that starts the regular
cloud reviewer); the lead dispatches it with `architect-ready`. Routine independent review uses
`review-ready` and a pinned PR request naming the eligible reviewer, without an inbox row.

A row and its labels record the decision or review request. When the item is ready, the delivery lead adds
[`architect-ready`](README.md#architect-dispatch-architect-ready) to the most urgent one (one per lead run); that
starts an Architect run, which clears every ready Open row. The Architect removes the label when done.

During the [Codex trial](../context/COORDINATION_MANAGER.md), Terra may apply the ready label
as a delegated mechanical step after verifying a complete request and when no lead decision
is outstanding. Count that dispatch against the same one-per-lead-window allowance.
Use the linked issue for the wake while only Issues → Labeled is configured. Keep review
material and its head pinned on the PR. A label requests a run. Confirm pickup from live
activity or the signed outcome.

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
| #429 scope | 2026-11-24 | gpt-lead | ruling | now | [E5 voice-count replacement scope](https://github.com/kalharbi11/wirescape-lab/issues/429#issuecomment-7142199713): production live parameters vs canonical config and narrow path grants. | E5 voice-count implementation |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| #414 review | 2026-11-24 | E4a+E4b contract-review at `8e8783b` | **[Approved `8e8783b`](https://github.com/kalharbi11/wirescape-lab/pull/416#issuecomment-7141760132)**: G1–G8, ER3, ER5 and A51 hold. The A50 dip differences are accepted as repeat noise (same fade, landing block differs). One Low (stopped-stream settle stall → E5). The lead merges with a merge commit |
| #417 OSC | 2026-11-24 | OB-g7 OSC loss disposition | **[Product loss; isolate first](https://github.com/kalharbi11/wirescape-lab/issues/417#issuecomment-7141778780)**: [#424](https://github.com/kalharbi11/wirescape-lab/issues/424) → B3, budget/enqueue counter split plus a fail-first test. No load or queue change |
| #417 MIDI | 2026-11-24 | E5 coverage of the MIDI counter reset | **Not E5**: [#425](https://github.com/kalharbi11/wirescape-lab/issues/425) → B2, session-cumulative counters. The monotonic check stays |
| #268 | 2026-11-24 | OB-c #275 A45/A46/A52 review at `3aad6e3` | **[Approved `3aad6e3`](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7140594351)**: identity search follows A52; the strict xfail needs an exact float32 fade reconstruction over the whole tail, and an XPASS or an unexplained mismatch is red. One Low: a naming nit. Lead merges |
| #414 A40 | 2026-11-24 | E4b integration shape: retained fail-first/correction commits | **[Ruled](https://github.com/kalharbi11/wirescape-lab/pull/416#issuecomment-7140596739)**: keep the 10 commits (1–3 E4a, 4–10 E4b); merge commit, `b3e11ea` being the E4a revert point. A squash is allowed only if the Result cites `b3e11ea` and its runs. This does not release the merge: CN evidence and the Claude review are still needed |