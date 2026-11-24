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
| A44 | 2026-11-24 | gpt-lead | scope ruling | **now** | [E6 #395](https://github.com/kalharbi11/wirescape-lab/pull/395#issuecomment-7126072238) at `ab50d23a609fd6ded1a5a9f8a1220ae097e836be`: ER6 loader duplicates must coalesce, but shared sidecar validation refuses them before the loader. Grant load-only ingress normalization, preserving strict `connect` and `applyGraph`; SR7 cannot grant behavior. | E6 sidecar load ingress only |
| A45 | 2026-11-24 | gpt-lead | semantics ruling | **soon** | [OB-c P1 #275](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7126246369) at `070db7afe4b071fd3c139a0398ea9969ba84e8d1`: gate-free A10 PCM identity conflicts with ABI2 mandatory processor reset; rule on a distinct release-only user panic or contract disposition. | OB-c P1 source fix |
| A46 | 2026-11-24 | gpt-lead | semantics ruling | **soon** | [OB-c G1 #275](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7126246369) at `070db7afe4b071fd3c139a0398ea9969ba84e8d1`: one-block A10 STOP conflicts with documented cycle-end STOP; rule on command semantics. | OB-c G1 source fix |
| A47 | 2026-11-24 | gpt-lead | CI scope ruling | **soon** | [CI2 #393](https://github.com/kalharbi11/wirescape-lab/pull/393#issuecomment-7126102744) at `8b186fe3ce7b0b724313efaa93c5b90fd1979a86`: keep the unchanged T7.0 capture workflow until open M7 evidence uses are complete. Confirm this narrow deferral of the A42 retirement list. | CI2 merge only |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A38 | 2026-11-24 | TR1e #385 Architect review (ER1, 0008 K1/K2/K4) | [Approved `5d2d78b` with one condition](https://github.com/kalharbi11/wirescape-lab/pull/385#issuecomment-7124056762): the red `Offline facts / windows-latest` job goes green on a re-run, or shows the same failure on main. No High or Medium findings; 3 Low (one for E6, two for TR1h) |
| A43 | 2026-11-24 | S7.7 #380 Claude contract-review and the 96 kHz evidence question (owner) | [Approved after one pre-approved one-line correction](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7124107855): restore the `baseline_peak` check. No 96 kHz measurement is needed. A38's Windows condition is [met](https://github.com/kalharbi11/wirescape-lab/pull/385#issuecomment-7124108736) |
