<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19, 04:05 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | [#259](https://github.com/kalharbi11/wirescape-lab/issues/259) OB-a2, in progress, PR pending | Add the owner-folder round-trip mode. Verify unchanged input hashes, ignored reports and existing bundled/config-shape coverage. | [#192](https://github.com/kalharbi11/wirescape-lab/issues/192) Reload engine waits for lead release of the Studio/Desktop lane after higher priority work. OB-a3 in [#203](https://github.com/kalharbi11/wirescape-lab/issues/203) needs the native/document writer and its own task. |
| **B2** `gpt-builder2` · fixtures / evidence | [#207](https://github.com/kalharbi11/wirescape-lab/issues/207) / [#214](https://github.com/kalharbi11/wirescape-lab/pull/214) A10, `b6900c1` | [Final SR6(b) packet](https://github.com/kalharbi11/wirescape-lab/pull/214#issuecomment-7004613519): fix only the Node 22 JSON import attribute. Report actual Studio inventory and A10 results. Ledger 2/2 plus this packet. Buffer wall time still needs independent marks. Stop if the packet fails. | [#209](https://github.com/kalharbi11/wirescape-lab/issues/209) / [#216](https://github.com/kalharbi11/wirescape-lab/pull/216) UI timing facts remain parked behind A10's disposition and a lead release. Architect sets OB-f2 targets from measured facts. |
| **B3** `gpt-builder3` · module DSP | [#243](https://github.com/kalharbi11/wirescape-lab/issues/243) / [#255](https://github.com/kalharbi11/wirescape-lab/pull/255) Reverb S7.2, `f314b85` | [Signed Result](https://github.com/kalharbi11/wirescape-lab/pull/255#issuecomment-7004276611): corrected Lab and original three-platform Golden passed. Matched full-mode MO is open. Lead verifies/publishes the D5 audio and reconciles the later Windows base-build failure. Queue independent review at readiness. Ledger 1/2. | [#202](https://github.com/kalharbi11/wirescape-lab/issues/202) sound queue: S7.3/S7.5/S7.6 after dispatch, S7.7–S7.9 follow S6 and module dependencies. S7.2 is the OB0 priority. |
| **B4** `gpt-builder4` · engine / sidecar | [#253](https://github.com/kalharbi11/wirescape-lab/issues/253) / [#261](https://github.com/kalharbi11/wirescape-lab/pull/261) S5b, `e621863` | [Checkpoint](https://github.com/kalharbi11/wirescape-lab/pull/261#issuecomment-7004404418): correction 1/2 fixed a returned-filter compile error. Collect evidence 1–5 and request independent Claude review against A17 and M1. A17 excludes CMake. | [#199](https://github.com/kalharbi11/wirescape-lab/issues/199) S6 waits for reviewed S5b merge and an announced rename window. Then [#200](https://github.com/kalharbi11/wirescape-lab/issues/200) M3/M4 serial engine work follows the roadmap. |

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
