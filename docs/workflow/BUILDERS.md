<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19, 04:56 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | [#259](https://github.com/kalharbi11/wirescape-lab/issues/259) / [#263](https://github.com/kalharbi11/wirescape-lab/pull/263) OB-a2, draft | Reject nested input/report overlap. Run the authorized isolated SR8 device-off owner-mode tests with temporary copies, input hashes, ignored reports and unchanged OB-a1 baseline. | [#192](https://github.com/kalharbi11/wirescape-lab/issues/192) Reload engine waits for lead release of the Studio/Desktop lane after higher priority work. OB-a3 in [#203](https://github.com/kalharbi11/wirescape-lab/issues/203) needs the native/document writer and its own task. |
| **B2** `gpt-builder2` · fixtures / evidence | [#207](https://github.com/kalharbi11/wirescape-lab/issues/207) / [#214](https://github.com/kalharbi11/wirescape-lab/pull/214) A10, `9ce062f`, blocked | Lab green and real Studio trace generated. Dedicated runner could not locate the production sidecar. B2 inspects paths and proposes an SR6(c) replacement; no more #214 source writes. | [#209](https://github.com/kalharbi11/wirescape-lab/issues/209) / [#216](https://github.com/kalharbi11/wirescape-lab/pull/216) UI timing facts remain parked behind A10's disposition and a lead release. Architect sets OB-f2 targets from measured facts. |
| **B3** `gpt-builder3` · module DSP | [#243](https://github.com/kalharbi11/wirescape-lab/issues/243) / [#255](https://github.com/kalharbi11/wirescape-lab/pull/255) Reverb S7.2, `f314b85` | [Signed Result](https://github.com/kalharbi11/wirescape-lab/pull/255#issuecomment-7004276611): corrected Lab and original three-platform Golden passed. Matched full-mode MO is open. Lead verifies/publishes the D5 audio and reconciles the later Windows base-build failure. Review required. Queue it only after evidence is reconciled. Ledger 1/2. | [#202](https://github.com/kalharbi11/wirescape-lab/issues/202) sound queue: S7.3/S7.5/S7.6 after dispatch, S7.7–S7.9 follow S6 and module dependencies. S7.2 is the OB0 priority. |
| **B4** `gpt-builder4` · engine / sidecar | [#253](https://github.com/kalharbi11/wirescape-lab/issues/253) / [#261](https://github.com/kalharbi11/wirescape-lab/pull/261) S5b, `e621863` in independent Claude review | [Pinned request](https://github.com/kalharbi11/wirescape-lab/pull/261#issuecomment-7005726151) at e621863. Lab, paired evidence and three-platform Golden passed. B4 addresses signed review findings within the existing 1/2 ledger. A17 excludes CMake. | [#199](https://github.com/kalharbi11/wirescape-lab/issues/199) S6 waits for reviewed S5b merge and an announced rename window. Then [#200](https://github.com/kalharbi11/wirescape-lab/issues/200) M3/M4 serial engine work follows the roadmap. |

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
- In cloud, give the owner one B1–B4 start list. Resume a CI-dependent task when its
  results enable a new action.

Signed: codex-lead, 2026-11-19, 04:05 EST
