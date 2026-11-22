<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-22 (claude-architect, acting lead this run). The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install | OB-g7 [#306](https://github.com/kalharbi11/wirescape-lab/issues/306) / [#309](https://github.com/kalharbi11/wirescape-lab/pull/309) `593a601`; OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) parked | #312 merged; match CLI, reports and tier inputs and exercise Linux OSC L0. Earlier workflow run verified loading only. Prepare #298 pin 7 matrix read-only. | S6 → rebase #298 first and obtain Claude review → OB-b [#318](https://github.com/kalharbi11/wirescape-lab/issues/318) at Phase C handoff. Workflow prep is independent; activate OSC after #305 and MIDI after #308 integration. |
| **B2** `gpt-builder2` · evidence / injected MIDI | OB-g2 [#308](https://github.com/kalharbi11/wirescape-lab/issues/308) / [#311](https://github.com/kalharbi11/wirescape-lab/pull/311) `f529b94`, correction 2/2 | Scripted tests pass. Keep default S0 snapshot byte-identical by scoping diagnostics transport to explicit scripted MIDI. Bench writer handoff to B2 is recorded. | MIDI/mixed integration can proceed during correction CI; S6 + mapped paths before merge. OB-f1 at candidate. P3 [#319](https://github.com/kalharbi11/wirescape-lab/issues/319) only if no P0–P2 work can run and lead releases it. |
| **B3** `gpt-builder3` · module DSP | OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307), transferred to dedicated B3 chat; S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) parked | Finish MIDI to CV draft. A27 Delay evidence planning can run read-only in parallel. | If still in S6 after #307 Result, ADSR [#316](https://github.com/kalharbi11/wirescape-lab/issues/316) draft. After S6: #298 rebases first, then #291; Delay [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) → S7.7 → S7.8 → S7.9 in released order. Serialize ADSR with S7.9. |
| **B4** `gpt-builder4` · engine / sidecar | S6 slot transferred to CB1 (`0020` §6); stands down from #295 | None in S6. Do not push to `task/294-m1-s6`. | After S6 merges: mapped-path [#315](https://github.com/kalharbi11/wirescape-lab/issues/315) T1.6a, if the lead releases it. |
| **B5** `gpt-builder5` · bounded support | OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317), Studio-test-only draft | Reproduce endpoint change on a device-off baseline. Keep native writes with B2. #312 merged `445123b`; Linux L0 remains advisory. | After S6, bounded OB-c marker/PCM proof, one separate case at a time. |
| **CB1** `claude-builder1` · S6 sole writer (cloud) | M1 S6 [#294](https://github.com/kalharbi11/wirescape-lab/issues/294) / [#295](https://github.com/kalharbi11/wirescape-lab/pull/295), from head `4b33b6f` | Continue B4's `lab/s6_handoff/` plan and `s6-active-consumer-gaps.json`: zero unresolved, guarded apply, build, 0006 evidence 1–6 on hosted CI. S0 test: hosted CI is the authority, with no snapshot edit (`0020` §6). The Architect is started by the owner and does the Claude contract-review. | Lead merges after review. |
| **CB2** `claude-builder2` · note tools | CV to Notes [#327](https://github.com/kalharbi11/wirescape-lab/issues/327) | Draft PR with tests and green Lab. Merges after S6. | Then Poly Merge [#328](https://github.com/kalharbi11/wirescape-lab/issues/328), the same way. It merges last, after Gate Delay. |
| **CB3** `claude-builder3` · Gate Delay | Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) | Draft PR with the §4 tests and green Lab, so the owner can play the branch. Merges after S6, right after CV to Notes. | None. |

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
