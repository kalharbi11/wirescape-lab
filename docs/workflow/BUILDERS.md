<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 19:48 EST; Architect run 21 refreshed B2/B4 at 20:20 EST. Architect runs 19–19c and [0021 §6](../../proposals/0021-replan-to-ob1.md#6-owner-answers-and-rulings-2026-11-23-1430-et) govern release. Use the existing issues, branches and PRs. Keep one active PR per lane, with one engine draft-ahead slot. Each issue names its execution environment.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / OB-c | [G-W1 #368](https://github.com/kalharbi11/wirescape-lab/issues/368) | Chat draft #384 has the fail-first wheel test. Read hosted evidence, then apply the scoped fix. | OB-c #275/#203 after release → S7.3. |
| **B2** `gpt-builder2` · OSC / I/O | [OB-g8 #383](https://github.com/kalharbi11/wirescape-lab/issues/383) | #339 closed unmerged under SR6(c). Chat first for bounded CPU versus preemption diagnosis. One Linux test-only measurement released to the existing Codex sandbox. | PI-1 #369 **postponed to the OB1 candidate** (OB r2.6). OB-f1 at the OB1 candidate. |
| **B3** `gpt-builder3` · CI / sound | [S7.5 #288 / #291](https://github.com/kalharbi11/wirescape-lab/pull/291) | Released in Chat after C1 #375 merged `7993a28`. Refresh exact-head evidence, ARM64 Ir and D5. Independent K1–K8 review. Lead owns C1 acceptance on #367. | S7.6 #314 → S7.9. #322 stays parked behind CAT-1+MB. |
| **B4** `gpt-builder4` · modules | [S7.7 #373 / #380](https://github.com/kalharbi11/wirescape-lab/pull/380) | **A37 ruled** ([M7 r1.5](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7118689012)): retire only the S4 whole-graph ABI1 bound in `serialized_demo_equivalence` (all other assertions stay), add `Cost-change:` lines for VCF-containing rows (cap +5 %; rows without VCF stay at 1 %), then post the Result. The lead dispatches the Claude review with `architect-ready`. | S7.8 #374 after merge. #333 and #356 stay parked. |
| **B5** `gpt-builder5` · OB1 engine | [TR1e #378](https://github.com/kalharbi11/wirescape-lab/issues/378) | Released after #376 merged `519d53a`. Codex draft #385 for native tests and paired evidence. ER1 and 0008 K1/K2/K4, then Architect review. | E6 → E4a → E4b → E5 → E7. One stacked draft after explicit release. |
| **CB1–CB3** | Closed | Architect retains design, required review and acceptance. | Owner controls future Claude builder starts. |

Parked branches are retained: #333, #356, #322, #358 and #363. CAT-1 and MB1 combine after OB1. Exact-head evidence stays required; authorized exceptions are limited to their named rows. Hosted soak results are advisory.

## How the lead maintains this table

- Every lead run checks each builder's open issues, PR heads, Results, checks and labels.
  Refresh every row's next action, including lower priority work with no Architect request.
  When a row is unchanged, retain the next action and update the review date above.
- Keep each builder's active and queued work visible. Put serial tasks in order. Mark tasks
  parallel when their prerequisites are met, scopes do not overlap and the lead released
  both. Each keeps its own issue, writer, branch and PR. A queued entry is planning only.
- Prefer continuity in each lane. Fill a free slot with ready independent work. If waiting
  is better, name the dependency, who can clear it and the next trigger.
- Remove finished tasks after merge or final disposition. Keep final evidence on GitHub
  and completed milestones on the roadmap. Update issue and PR labels in the same handoff.
  See [label rules](README.md#github-labels-for-work-and-review).
- In cloud, give the owner one runnable start list. Resume a CI-dependent task when its
  results enable a new action.

Signed: codex-lead, 2026-11-23, 19:48 EST
