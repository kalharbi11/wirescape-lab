<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 19:15 EST. Architect runs 19–19c and [0021 §6](../../proposals/0021-replan-to-ob1.md#6-owner-answers-and-rulings-2026-11-23-1430-et) govern release. Use the existing issues, branches and PRs. Keep one active PR per lane, with one engine draft-ahead slot. Each issue names its execution environment.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / OB-c | OB-a3 [#287](https://github.com/kalharbi11/wirescape-lab/issues/287) / [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `5ecf300` | [Signed exact-head Result](https://github.com/kalharbi11/wirescape-lab/pull/298#issuecomment-7117181191): six native/web routes and desktop backup semantics, green Lab/Golden/M1/Web. A34 is on main and `review-ready` is applied. Preserve the reviewed head. | [G-W1 #368](https://github.com/kalharbi11/wirescape-lab/issues/368) (Chat and CI) after #298 handoff/lead release → OB-c #275/#203 → S7.3. |
| **B2** `gpt-builder2` · OSC / I/O | OB-g8 [#326](https://github.com/kalharbi11/wirescape-lab/issues/326) / [#339](https://github.com/kalharbi11/wirescape-lab/pull/339)  `f18e83d` | Panic recovery and Windows compile correction landed on the branch. Linux L0, Golden and paired M1 passed. Final diagnostic: 2,973 sanitizer drops and 56.665 ms longest render call, without sender catch-up. Blocked after the final packet. Next lead decides SR6 disposition before further source work. Preserve the branch and all gates. | #324 merged. PI-1 [#369](https://github.com/kalharbi11/wirescape-lab/issues/369) lab half, after #339 disposition and owner token setup. OB-f1 at the OB1 candidate. |
| **B3** `gpt-builder3` · CI / sound | C1 [#367](https://github.com/kalharbi11/wirescape-lab/issues/367) / [#375](https://github.com/kalharbi11/wirescape-lab/pull/375) `3267a17` | Chat created the branch and draft PR with the connector. Lab passed and lead ran 8/8 parser tests. Keep draft pending A35 on sequencing the live two-head acceptance. | S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) after C1 and release → S7.6 #314 → S7.9. #322 parks until after CAT-1+MB. |
| **B4** `gpt-builder4` · modules | S7.7 VCF [#373](https://github.com/kalharbi11/wirescape-lab/issues/373) (released, Chat and CI) | Follow M7 K1–K8, measured passband/peak and Ir evidence, then required Claude review. #356 parks under R3: only existing LFO paired rows failed on x64/ARM64. | S7.8 Ladder [#374](https://github.com/kalharbi11/wirescape-lab/issues/374) after S7.7 merges. #333 and #356 retain their branches. |
| **B5** `gpt-builder5` · OB1 engine | T1.6c [#364](https://github.com/kalharbi11/wirescape-lab/issues/364) / [#376](https://github.com/kalharbi11/wirescape-lab/pull/376) `418d4a7` | B5 signed Result; Lab, Golden and paired M1 passed. A36 requests Architect contract-review of 0007 rules 2–5. Preserve the head. | TR1e [#378](https://github.com/kalharbi11/wirescape-lab/issues/378) (one stacked draft allowed) → E6 → E4a → E4b → E5 → E7. All merge prerequisites hold. |
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

Signed: codex-lead, 2026-11-23, 19:15 EST
