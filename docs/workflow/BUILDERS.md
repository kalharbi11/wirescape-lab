<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-21 18:38 EST (codex-lead). The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install | OB-g7 [#306](https://github.com/kalharbi11/wirescape-lab/issues/306) / [#309](https://github.com/kalharbi11/wirescape-lab/pull/309) `593a601`; OB-a3 [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) parked | #312 merged; match CLI, reports and tier inputs and exercise Linux OSC L0. Earlier workflow run verified loading only. Prepare #298 pin 7 matrix read-only. | S6 → rebase #298 first and obtain Claude review → OB-b [#318](https://github.com/kalharbi11/wirescape-lab/issues/318) at Phase C handoff. Workflow prep is independent; activate OSC after #305 and MIDI after #308 integration. |
| **B2** `gpt-builder2` · evidence / injected MIDI | OB-g2 [#308](https://github.com/kalharbi11/wirescape-lab/issues/308) / [#311](https://github.com/kalharbi11/wirescape-lab/pull/311) `f529b94`, correction 2/2 | Scripted tests pass. Keep default S0 snapshot byte-identical by scoping diagnostics transport to explicit scripted MIDI. Bench writer handoff to B2 is recorded. | MIDI/mixed integration can proceed during correction CI; S6 + mapped paths before merge. OB-f1 at candidate. P3 [#319](https://github.com/kalharbi11/wirescape-lab/issues/319) only if no P0–P2 work can run and lead releases it. |
| **B3** `gpt-builder3` · module DSP | OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307), transferred to dedicated B3 chat; S7.5 [#291](https://github.com/kalharbi11/wirescape-lab/pull/291) parked | Finish MIDI to CV draft. A27 Delay evidence planning can run read-only in parallel. | If still in S6 after #307 Result, ADSR [#316](https://github.com/kalharbi11/wirescape-lab/issues/316) draft. After S6: #298 rebases first, then #291; Delay [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) → S7.7 → S7.8 → S7.9 in released order. Serialize ADSR with S7.9. |
| **B4** `gpt-builder4` · engine / sidecar | M1 S6 [#294](https://github.com/kalharbi11/wirescape-lab/issues/294) / [#295](https://github.com/kalharbi11/wirescape-lab/pull/295) `7d7f89e` | Clean-tree previews agree: 444 moves, 2 retained, 170 candidate edits, 76 unresolved. Classify all references, guard apply/replay, gather evidence 1–6 and obtain Claude review. | S6 merge → mapped-path [#315](https://github.com/kalharbi11/wirescape-lab/issues/315) T1.6a → T1.6b → T1.6c → TR1e → E6. One writer and one actual predecessor merge per stage. |
| **B5** `gpt-builder5` · bounded support | OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317), Studio-test-only draft | Reproduce endpoint change on a device-off baseline. Keep native writes with B2. #312 merged `445123b`; Linux L0 remains advisory. | After S6, bounded OB-c marker/PCM proof, one separate case at a time. |

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

Signed: codex-lead, 2026-11-21, 18:38 EST
