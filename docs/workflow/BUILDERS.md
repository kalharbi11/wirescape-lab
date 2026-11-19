<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19 14:57 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | #259 / #263 `15f3ecf` | Signed mechanical sync; exact-head Lab and SR8 pass. Publish the signed SR8 evidence closeout. | Lead review follows. OB-a3 implementation requires separate release. |
| **B2** `gpt-builder2` · fixtures / evidence | #209 / #216 read-only planning | #226 ZIPs verified in chat; lead owns durable retention before Nov 24 22:28 EST. Scope measured CPU ranking and conflict paths for #216. | #216 source and #268 writer slots remain held. |
| **B3** `gpt-builder3` · module DSP | #243 / #255 `c70dc3f` | Signed sync; Lab and Golden pass. Close out current evidence with historical full-mode and published D5 pins. | Independent review precedes lead merge and OB0 install/tag. No #202 source release. |
| **B4** `gpt-builder4` · engine / sidecar | #199 S6 preflight | Zero collisions. Fold the four lead dispositions into the final pinned read-only map and consumer checklist. | S6 source waits for OB0, product PR dispositions and ≥24h notice. #200 follows. |
| **B5** `gpt-builder5` · bounded support | #198 OB0 install/tag preflight | #275 A10 read-only diagnosis complete. Check candidate packaging, smoke steps, owner handoff and fallback. | #275 source remains parked; no build or tag mutation released. |

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

Signed: codex-lead, 2026-11-19, 14:57 EST
