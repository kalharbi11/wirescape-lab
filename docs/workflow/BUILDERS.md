<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-21 12:34 EST (codex-lead quick check). The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | OB-g7 [#306](https://github.com/kalharbi11/wirescape-lab/issues/306) draft; OB-a3 [#287/#298](https://github.com/kalharbi11/wirescape-lab/pull/298) parked | Draft the dedicated hosted workflow only. OSC execution needs #305; MIDI profiles need OB-g2. #298 `fda3dd5` Lab and Golden passed; common-loader proof covers only part of pin 7. | After S6, rebase #298 first, establish scope for any missing per-entry-point tests, run exact-head CI and obtain Claude contract-review. OB-b follows. |
| **B2** `gpt-builder2` · fixtures / evidence | M7 T7.0b [#296/#300](https://github.com/kalharbi11/wirescape-lab/pull/300), `58ac812` | Signed facts Result and exact-head Lab/T7.0 succeeded. Record the two different Delay mode windows as measured; A27 asks how S7.6 should use them. Correction count 2/2. | OB-f1 advisory rerun at OB1 candidate. #268 remains parked. |
| **B3** `gpt-builder3` · module DSP | OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) draft; S7.5 [#288/#291](https://github.com/kalharbi11/wirescape-lab/pull/291) parked | Draft MIDI to CV trigger and device-off tests. #291 `cdf666c` has signed Lab/Golden/Ir evidence; lead still owes D5 and pinned independent K1–K8 review after rebase. | After S6, rebase #291 second. S7.6 waits for A27. Coordinate S7.7 → S7.8/S7.9 and other module drafts in writer order. |
| **B4** `gpt-builder4` · engine / sidecar | M1 S6 [#294/#295](https://github.com/kalharbi11/wirescape-lab/pull/295), `7d7f89e` | Phase B sole migration writer. Product baseline `23443691b4950b4747ade943d7d8602d281938fc`. Run preview against a full clean tree, close unresolved consumers, implement guarded apply, and produce 0006 items 1–6. Existing Lab covers only the draft scripts. | Claude S6 contract-review at evidence-ready head. Then M3 T1.6a → T1.6b → T1.6c → TR1e → M4 E6. |
| **B5** `gpt-builder5` · bounded support | OB-g1 [#305](https://github.com/kalharbi11/wirescape-lab/issues/305) released | Own `bench/io/**` and any `facts/perf/` results for #305. Stop rules, three injected failures and reports per 0019 §3. Record Linux L0 as advisory. | #275 panic read-only prep is complete. After S6, give each OB-c fix its own task and resolve panic reset semantics before changing behavior. #198 Pi checklist remains with the owner. |

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

Signed: claude-architect (acting lead), 2026-11-20
