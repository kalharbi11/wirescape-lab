<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ARCHITECT_INBOX — everything that needs the Claude Architect

**The Architect's first read on every run** (or its Sonnet scout's, see [ARCHITECT_SCOUT.md](ARCHITECT_SCOUT.md)). Any agent (lead, builder, reviewer) that needs a
ruling, a Claude contract-review, an acceptance, or wants the Architect to know something adds
**one row** here *and* labels the PR or issue `needs/architect`. Nothing else is required to
reach the Architect; do not rely on PR comments alone.

A planned review condition uses `review-required`. Open an Architect-only review row when its
pinned request is ready. Apply `needs/architect` and give the owner the ready queue and
`architect:run` trigger. The Architect clears ready Open rows at the owner's manual start.
Keep review material and its head pinned on the PR. Regular independent reviews use a pinned
request naming the eligible reviewer and the owner's manual start.

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
| A64 | 2026-11-24 | gpt-lead | ruling | soon | [Delay A27 evidence and question](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7148652913), head `e7726284a0116ba50f44946f48a4bf9720f36f6e`. Mode/tone target-only spectra exceed old floor; switched exceeds their target control by +0.030/+0.307 dB, and clocked division is 2.271 dB below old floor. Rule how to isolate transition artifact and interpret the below-floor result under the unchanged criterion. | S7.6 #449 |
| A65 | 2026-11-24 | gpt-lead | contract-review | soon | [S7.9 manual review](https://github.com/kalharbi11/wirescape-lab/pull/444#issuecomment-7148992053), base `cb0004b0ba56cfffd280567a29daf4151f830013`, head `c86810e2ac2d6d982df40ac1fdba29137bed0986`. D5 published, review M7 K1–K8, A63 and bounded r1.6 disposition. | S7.9 #444 |

## Cleared (last run only)
| ID | Date ET | Ask | Answer |
|---|---|---|---|
| A62 | 2026-11-24 | E7 #442 `0f6d33b`: `freshModules` semantics, protocol docs grant, CN capture owner and larger-buffer witness | **Ruled** ([M4 A62](milestones/M4.md), [Q26](QUESTIONS.md#q26--e7-freshmodules-protocol-docs-cn-rows-a62)): list = instances the host could not carry (no hook, save/load not OK, no ID/type/config match); a hook that returns OK counts as carried; no per-type lists in host code. Version-only resets named in the E7 Result/report from the inventory (M4 Escalate row), not in the reply. SR17 schema/regen + `ENGINE_PROTOCOL.md` reply paragraph granted in #442. CN rows: B1, after #442 merges; larger witness = a nontrivial-state module; no threshold change |
| A61 | 2026-11-24 | #424/#433 `8cb9d2e`: four additive OSC status fields, or native-only acceptance | **Native-only diagnosis accepted** ([Q27](QUESTIONS.md#q27--osc-hosted-attribution-a61)): #433 merges as is (`merge: lead`, exact-head green). Hosted exposure = new follow-up (B3), four read-only additive status fields + SR17 schema, draft-ahead now, ready only after E7 #442 merges. No product fix until a hosted sample shows nonzero split counts |
