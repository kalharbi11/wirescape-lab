<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19 08:37 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | #259 / #263, draft `a3544de` | SR8 owner-folder acceptance and 32/32 OB-a1 passed. Windows Lab remains blocked behind #271; ledger 1/2. OB-a3 read-only Result has not landed. | Resume #263 when the lead releases the runner fix. #192 and OB-a3 implementation remain gated. |
| **B2** `gpt-builder2` · fixtures / evidence | #268 / [#275](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7010713356), draft `05954b3` | Lead-owned writer slot per SR12. Real sidecar executed. Panic identity failed, internal Groove aborted, and the Echo fixture rejected the trace. External Groove and historical MIDI passed. | Bounded fixture/failure diagnosis before any correction. #209 / #216 remain parked. |
| **B3** `gpt-builder3` · module DSP | #243 / #255, draft `f314b85` | #267 / #274 merged; verified full-mode head peak 0.9806554914 FS and D5 published. Ledger 1/2. | Lead reconciles Windows Golden and advisory ARM64, then dispatches independent source review. #202 requires separate release. |
| **B4** `gpt-builder4` · engine / sidecar | #199 S6 preflight | [Signed destination reconciliation](https://github.com/kalharbi11/wirescape-lab/issues/199#issuecomment-7008070874) complete, with decisions and collisions recorded. | S6 requires OB0 tag, agreed map, open-PR disposition, lead release and ≥24h notice. #200 follows. |
| **B5** `gpt-builder5` · bounded support | Available for a bounded dispatch | Audit delivered. Lead-assigned Codex worker completed the Windows diagnosis. #271 / #273 proved the Windows runner but remains blocked by Linux package mirror failures after its SR5 retry. | Keep the CI writer with the lead. No second retry or new product writer slot. |

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

Signed: codex-lead, 2026-11-19, 04:05 EST
