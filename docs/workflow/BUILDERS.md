<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 18:32 EST. Architect runs 19–19c and [0021 §6](../../proposals/0021-replan-to-ob1.md#6-owner-answers-and-rulings-2026-11-23-1430-et) govern release. Use the existing issues, branches and PRs. Keep one active PR per lane, with one engine draft-ahead slot. Each issue names its execution environment.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / OB-c | OB-a3 [#287](https://github.com/kalharbi11/wirescape-lab/issues/287) / [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `5ecf300` | [Signed exact-head Result](https://github.com/kalharbi11/wirescape-lab/pull/298#issuecomment-7117181191): six native/web routes and desktop backup semantics, green Lab/Golden/M1/Web. Lead pins Claude Architect review A34. Preserve the reviewed head. | [G-W1 #368](https://github.com/kalharbi11/wirescape-lab/issues/368) (Chat and CI) after #298 handoff/lead release → OB-c #275/#203 → S7.3. |
| **B2** `gpt-builder2` · OSC / I/O | OB-g8 [#326](https://github.com/kalharbi11/wirescape-lab/issues/326) / [#339](https://github.com/kalharbi11/wirescape-lab/pull/339) `ab75b77` | Panic recovery and Windows compile correction landed on the branch. Linux L0, Golden and paired M1 passed. Sanitizer ingress overflow and gate timing remain red. Chat reads hosted logs and source; the existing Codex session owns any instrumented correction. Preserve load, latency and zero-drop criteria. | #324 merged. PI-1 [#369](https://github.com/kalharbi11/wirescape-lab/issues/369) lab half, after #339 disposition and owner token setup. OB-f1 at the OB1 candidate. |
| **B3** `gpt-builder3` · CI / sound | C1 [#367](https://github.com/kalharbi11/wirescape-lab/issues/367) / [#375](https://github.com/kalharbi11/wirescape-lab/pull/375) `c8ab747` | Chat created the branch and draft PR with the connector. Correct the workflow name, validate comment serialization, verify credential-safe log downloads and run the device-off parser tests. Live two-head acceptance needs A35 disposition because the workflow runs from main. | S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) after C1 and release → S7.6 #314 → S7.9. #322 parks until after CAT-1+MB. |
| **B4** `gpt-builder4` · modules | [#328](https://github.com/kalharbi11/wirescape-lab/issues/328) / [#356](https://github.com/kalharbi11/wirescape-lab/pull/356), Poly Merge + Poly Split | Codex for native generator and targeted tests. One Studio/S0 regeneration for both modules; parsed changes limited to their entries. Keep 34 frozen IDs and strict gates. If shared code-generation blocks the corrected branch, R3 applies. | S7.7 [#373](https://github.com/kalharbi11/wirescape-lab/issues/373) then S7.8 [#374](https://github.com/kalharbi11/wirescape-lab/issues/374) (Chat and hosted CI, mandatory Claude reviews). #333 parks. |
| **B5** `gpt-builder5` · OB1 engine | T1.6c [#364](https://github.com/kalharbi11/wirescape-lab/issues/364) (released) | #324 merged `2d992aa`. Codex is the single engine writer. Verify proposal 0007 rules 2–5, then Architect contract-review. | TR1e (one stacked draft allowed) → E6 → E4a → E4b → E5 → E7. All merge prerequisites hold. |
| **CB1–CB3** | Closed | Architect retains design, required review and acceptance. | Owner controls future Claude builder starts. |

Parked branches are retained: #333, #322, #358 and #363. CAT-1 and MB1 combine after OB1. Exact-head evidence stays required; authorized exceptions are limited to their named rows. Hosted soak results are advisory.

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

Signed: codex-lead, 2026-11-23, 18:32 EST
