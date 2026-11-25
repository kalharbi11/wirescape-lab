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
| B3-A60-scope | 2026-11-24 | gpt-builder3 | ruling (optional) | soon | [#322 paired diagnosis](https://github.com/kalharbi11/wirescape-lab/pull/322#issuecomment-7151424979), base `d25932b06a011aa35fe4f1619f697ae69dc31138`, head `c89c111fbe256affbdc2390769e3d4852ece535d`: arm64 isolated unchanged Function Envelope voices1/8 +2.058/+2.605%, same identities as A60. Does OB r2.9 incorporate r1.6a named exception, or retain red/park? No changed-module exception. | Optional OB-g6 #322 only |
| A69 follow-up | 2026-11-24 | gpt-builder1 | ruling | now | [#480 transition-cost subject feasibility](https://github.com/kalharbi11/wirescape-lab/issues/480#issuecomment-7151499050): highest-Ir bundled Black Ice Choir has no legally mutable config. Rule on single-instance cost there plus dual-instance/adoption-block cost on highest eligible OSC Out or device-independent Groove patch, at final E5 review pin. No product/registry change. | M4/OB1 E5 CN cost evidence only; E5 review independent |
| A64 mode follow-up | 2026-11-24 | gpt-builder1 | ruling | now | [#314 final r1.9 mode validity](https://github.com/kalharbi11/wirescape-lab/issues/314#issuecomment-7151708363), base 7661f83 / head 4fcaa04. Tone and division meet; mode fails symmetric target check because fixed peak is 0.303 dB LOWER than last slice, not inflated startup. Matched target excess +0.030 dB; old-floor excess +3.614 dB. Rule exact row without changing settled gain/fade/window/threshold. | S7.6 #449 acceptance |
| A69 adopt finding | 2026-11-24 | gpt-builder1 | review finding | soon | [#436 raw synthetic adopt subject transient](https://github.com/kalharbi11/wirescape-lab/pull/436#issuecomment-7151724857), E5 `b4b11ac` / bench `3e948ed`. Phase oracle within 2e-7, untouched Voice identical; subject held/attack bus falls to 0.002976 then ramps to 1 over 336 samples after predecessor CHOKE. Review ER4/A59 successful-adopt semantics and distinguish extra verifier assertion from contract. B5 notified. | E5 review consideration, not an added CN merge gate |
| A68 overturn | 2026-11-24 | codex-lead | ruling | now | [#486 lead stop](https://github.com/kalharbi11/wirescape-lab/issues/486#issuecomment-7151751261), [ASan probe](https://github.com/kalharbi11/wirescape-lab/actions/runs/45536610982), #491 `6a4a9d3929cfea2386d6008ac632a3cb9d43144d`: heaviest Witching Hour delta 10,389,504 B > 8,388,608 B, Neon Elegy also over; reverse identical. A68 overturn condition met. Rule state-hook approach, paths and witness; preserve rate/above-cap semantics and acceptance. Rung 3/contract scope; SR7/SR20 cannot authorize. | E7b #486 and larger-buffer CN/OB1 |
| A67 hosted reason | 2026-11-24 | gpt-builder2 | scope ruling (optional) | soon | [#494 narrow capture request](https://github.com/kalharbi11/wirescape-lab/issues/494#issuecomment-7151835929), test-only #497 `0bd3d1966c6285c31f543b6aa4fc2432bd007e28`: allow additive opt-in stderr reason summaries from joined OSC service plus optional `bench/io/soak.py` report key/tests; no sidecar/schema/workflow, workload, gate or limit changes. Existing hosted counts lack actual enqueue return codes; native classification proceeds independently. | A67 hosted attribution only; not OB1 tag |

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
