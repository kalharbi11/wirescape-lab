<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 21:04 EST. Architect runs 19–19c and [0021 §6](../../proposals/0021-replan-to-ob1.md#6-owner-answers-and-rulings-2026-11-23-1430-et) govern release. Use the existing issues, branches and PRs. Keep one active PR per lane, with one engine draft-ahead slot. Each issue names its execution environment.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / OB-c | [OB-c #203](https://github.com/kalharbi11/wirescape-lab/issues/203) / evidence #275 | G-W1 #384 merged `7a750b4`. B1 reads the existing oracles in Chat and proposes the first scoped fail-first case. | Case implementation on explicit release → S7.3. |
| **B2** `gpt-builder2` · OSC / I/O | [OB-g8 #383](https://github.com/kalharbi11/wirescape-lab/issues/383) | #339 closed unmerged under SR6(c). Chat first for bounded CPU versus preemption diagnosis. #386 `e1efbab` measured 56.032 ms wall / 55.628 ms thread CPU under sanitizer, with 2,887 drops. One bounded render-stage attribution released in the existing sandbox. | PI-1 #369 **postponed to the OB1 candidate** (OB r2.6). OB-f1 at the OB1 candidate. |
| **B3** `gpt-builder3` · CI / sound | [S7.5 #288 / #291](https://github.com/kalharbi11/wirescape-lab/pull/291) | Released in Chat after C1 #375 merged `7993a28`. #291 `733cff4` parked under 0021 R3: both red fixed rows lack Quad VCA. Numeric floor and D5 remain. Independent K1–K8 review. Lead owns C1 acceptance on #367. | S7.6 #314 → S7.9. #322 stays parked behind CAT-1+MB. |
| **B4** `gpt-builder4` · modules | [S7.7 #373 / #380](https://github.com/kalharbi11/wirescape-lab/pull/380) | **A37 ruled** ([M7 r1.5](https://github.com/kalharbi11/wirescape-lab/pull/380#issuecomment-7118689012)): retire only the S4 whole-graph ABI1 bound in `serialized_demo_equivalence` (all other assertions stay), add `Cost-change:` lines for VCF-containing rows (cap +5 %; rows without VCF stay at 1 %), then post the Result. `e44888e` Lab/Golden green; Chat must classify paired failures and supply the S4 log value, offline spectral facts and render evidence before dispatch. | S7.8 #374 after merge. #333 and #356 stay parked. |
| **B5** `gpt-builder5` · OB1 engine | [TR1e #378](https://github.com/kalharbi11/wirescape-lab/issues/378) | Released after #376 merged `519d53a`. #385 `5d2d78b` is non-draft. Signed Result and Lab/Golden/strict paired green. A38 requests Architect review against ER1 and 0008 K1/K2/K4. | E6 → E4a → E4b → E5 → E7. One stacked draft after explicit release. |
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

Signed: codex-lead, 2026-11-23, 21:04 EST
