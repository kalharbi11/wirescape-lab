<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-22 04:50 ET (claude-architect, acting lead). Owner: GPT builders take all the work except S6 (CB1). The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install | OB-g7 [#306](https://github.com/kalharbi11/wirescape-lab/issues/306) / [#309](https://github.com/kalharbi11/wirescape-lab/pull/309) `c0f1821`; OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `fda3dd5` parked | Finish the #309 Result: the CLI, reports and tier inputs match #312, and Linux OSC L0 has been exercised (advisory). Prepare the #298 pin 7 matrix read-only. | After S6: rebase #298 first and get the Claude review, then OB-b [#318](https://github.com/kalharbi11/wirescape-lab/issues/318) at the Phase C handoff. |
| **B2** `gpt-builder2` · evidence / injected MIDI | OB-g2 [#308](https://github.com/kalharbi11/wirescape-lab/issues/308) / [#311](https://github.com/kalharbi11/wirescape-lab/pull/311) `de0d6a0`, correction 2/2 | Post the Result at `de0d6a0`. The default S0 snapshot must stay byte-identical, with diagnostics only on explicit scripted MIDI. Hosted CI is the S0 authority (`0020` §6). | Merges after S6 and the mapped paths. Then OB-f1 at candidate. P3 [#319](https://github.com/kalharbi11/wirescape-lab/issues/319) only if lead-released. |
| **B3** `gpt-builder3` · module DSP | OB-g5 ADSR trigger [#316](https://github.com/kalharbi11/wirescape-lab/issues/316) / [#325](https://github.com/kalharbi11/wirescape-lab/pull/325) `50a2fcf`; OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) / [#322](https://github.com/kalharbi11/wirescape-lab/pull/322) `36e5bd7`; S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) parked | Post a Result on both drafts. #325 is first in the new-module merge order (`0020` §1), so finish it first. Gate mode stays bit-identical. | After S6: #325 → #322 merge; #291 rebases after #298; then Delay [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) (S7.6, released under M7 r1.4) → S7.7 → S7.8 → S7.9. Serialize ADSR with S7.9. |
| **B4** `gpt-builder4` · Gate Delay (S6 moved to CB1) | Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329), new branch `task/329-gate-delay` | Draft PR to `0020` §4 with its test list and green Lab, so the owner can build and play the branch. Do not push to `task/294-m1-s6`. | Merges after S6, third (after #325 and #327). Then mapped-path [#315](https://github.com/kalharbi11/wirescape-lab/issues/315) T1.6a, if the lead releases it. |
| **B5** `gpt-builder5` · bounded support / note tools | OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317) / [#324](https://github.com/kalharbi11/wirescape-lab/pull/324) `3bf1e02`; then CV to Notes [#327](https://github.com/kalharbi11/wirescape-lab/issues/327) | Post the #324 Result, then draft CV to Notes (`0020` §2) on `task/327-cv-to-notes`. Keep native writes for OB-g3 with B2. | Then Poly Merge [#328](https://github.com/kalharbi11/wirescape-lab/issues/328) on `task/328-poly-merge` (merges last). After S6: bounded OB-c marker/PCM proof, one case at a time. |
| **CB1** `claude-builder1` · S6 sole writer (cloud) | M1 S6 [#294](https://github.com/kalharbi11/wirescape-lab/issues/294) / [#295](https://github.com/kalharbi11/wirescape-lab/pull/295), from head `4b33b6f` | Continue B4's `lab/s6_handoff/` plan and `s6-active-consumer-gaps.json`: zero unresolved, guarded apply, build, 0006 evidence 1–6 on hosted CI. S0 test: hosted CI is the authority, with no snapshot edit (`0020` §6). The Architect is started by the owner and does the Claude contract-review. | Lead merges after review. |

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

Signed: claude-architect, 2026-11-22
