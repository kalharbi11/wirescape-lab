<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19 14:06 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | #259 / #263, draft `a3544de` | SR8 owner-folder acceptance and 32/32 OB-a1 passed. Windows Lab remains blocked behind #271; ledger 1/2. B1 is released to the independent #203 OB-a3 entry-point inventory. | Resume #263 when the lead releases the runner fix. #192 and OB-a3 implementation remain gated. |
| **B2** `gpt-builder2` · fixtures / evidence | #268 / [#275](https://github.com/kalharbi11/wirescape-lab/pull/275#issuecomment-7010713356), draft `05954b3` | Lead-owned writer slot per SR12. Real sidecar executed. Panic identity failed, internal Groove aborted, and the Echo fixture rejected the trace. External Groove and historical MIDI passed. | Lead worker is released to the test-local measured gesture-span correction. B2 can verify #226/#230 evidence retention in parallel. #209 remains parked. |
| **B3** `gpt-builder3` · module DSP | #243 / #255, draft `f314b85` | #267 / #274 merged; verified full-mode head peak 0.9806554914 FS and D5 published. Ledger 1/2. | B3 can prepare #198 release readiness. Lead pinned the Windows base-build and ARM64 Function Envelope advisory failures. Source review waits for CI disposition. #202 requires separate release. |
| **B4** `gpt-builder4` · engine / sidecar | #199 S6 preflight | [Signed destination reconciliation](https://github.com/kalharbi11/wirescape-lab/issues/199#issuecomment-7008070874) complete, with decisions and collisions recorded. | B4 is released to the exact nested map under the #199 ruling. S6 implementation waits for OB0 tag, open-PR disposition, lead release and ≥24h notice. #200 follows. |
| **B5** `gpt-builder5` · bounded support | Independent read-only #216 evidence review | Audit delivered. Lead-assigned Codex worker completed the Windows diagnosis. #273 proved the Windows runner. New head 966af91 pins the Studio Ubuntu image. Automatic Lab and Golden are running. | Keep the CI writer with the lead. No second retry or new product writer slot. |

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
