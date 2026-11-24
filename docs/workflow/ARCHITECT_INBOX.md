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
| A61 | 2026-11-24 | gpt-lead | scope and evidence | soon | [#424](https://github.com/kalharbi11/wirescape-lab/issues/424)/[#433](https://github.com/kalharbi11/wirescape-lab/pull/433) `8cb9d2edc3486fe7d39dcd54f1e20ab12b90f6e2`: grant four additive OSC status fields in `Session::status()` for hosted attribution, serialized with B2/B5, or accept native-only diagnosis and assign hosted exposure separately. No limits, queue, load or lifecycle changes. [Blocked Result](https://github.com/kalharbi11/wirescape-lab/pull/433#issuecomment-7143352337). | Hosted OSC attribution only |
| A62 | 2026-11-24 | gpt-lead | protocol and evidence | soon | [#431](https://github.com/kalharbi11/wirescape-lab/issues/431)/[#442](https://github.com/kalharbi11/wirescape-lab/pull/442) `0f6d33bc45bf53408e1914a4ed34d4abad412bed` (production unchanged from 6f5b74a; [pin refresh](https://github.com/kalharbi11/wirescape-lab/issues/431#issuecomment-7147366655)): rule whether rebuild `freshModules` covers successful version-only resets; grant protocol documentation if required and name a CN capture owner and larger-buffer witness without changing thresholds. [Builder ask](https://github.com/kalharbi11/wirescape-lab/issues/431#issuecomment-7144483551). | E7 final reply and CN evidence |
| A63 | 2026-11-24 | gpt-lead | scope (K5) | **now** | [#440](https://github.com/kalharbi11/wirescape-lab/issues/440#issuecomment-7147367324)/[#444](https://github.com/kalharbi11/wirescape-lab/pull/444) `d85c076b060c07a3e02fbc4ba3fe048638ea82fd`: grant only `vco()` in `engine/tests/port_behavior_tests.cpp` to replace obsolete CHOKE phase-reset expectations with an independent phase-continuous 220 Hz oracle, or rule different behavior; preserve all other assertions, coordinate B5. SR7 cannot grant; [Q25](QUESTIONS.md#q25--s79-choke-shared-frozen-vco-test-k5-a63). | S7.9 only |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| #432 A60 | 2026-11-24 | S7.3 Golden scope; unrelated ARM64 function_envelope paired rows | **A60** ([#432](https://github.com/kalharbi11/wirescape-lab/pull/432#issuecomment-7143875832)): declare the nine actual CHAOS patches; function_envelope voices1/8 arm64 ≤ +3.0 % bounded exception (CAT-1/OB1 expiry). Approved and merged `fe321f9` |
| #436 A59 | 2026-11-24 | E5 descriptor-size guard outside B5 paths; replay design | **A59** ([#436](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7143183539)): `tools/module/runner/abi_ws2.h` size guard granted under 0012 G5; bounded held-note record, replayed after `collect()` clears pending |
| #429 scope | 2026-11-24 | E5 voice-count replacement scope | **A55** ([M4 note](milestones/M4.md), [#429](https://github.com/kalharbi11/wirescape-lab/issues/429)): voice count stays a live parameter, no ID/document change; in-place `Allocator::resize` as **E5v #439** (B3, `merge: lead`). E5 = same-descriptor config replacement with ER4, adopt/ring-out, settle Low |
| #438 | 2026-11-24 | Roadmap status review; M7 batch 2 vs R3 inconsistency | **A56**: M7 r1.6 unparks S7.5/S7.6/S7.9 for OB1 with a bounded paired-row exception (≤ +2.5 %, rows without a changed module, linux, expires at CAT-1 or the OB1 tag). OB r2.9 adds optional #322. Roadmap revised and merged |
| run 29 process | 2026-11-24 | Owner: fewer stops before merge-ready | **A57** → STANDING SR20 (self-release, Lows never block, lead merges `merge: lead` on green + Result, facts auto-merge, one Claude review at the merge-ready head) |
| #424 routing | 2026-11-24 | OSC fix after the split counts | **A58** (pre-ruled): see [#424](https://github.com/kalharbi11/wirescape-lab/issues/424). The lead routes the fix without a new row unless it changes a limit, queue size, load or the soak profile |
