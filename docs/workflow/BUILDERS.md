<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19 14:32 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | #259 / #263 | OB-a3 inventory signed on #203. #273 merged at `73e462fd`; resume the existing #263 branch with a mechanical main sync, unchanged packet, 1/2 ledger, exact Windows Lab and owner-folder SR8 results. | OB-a3 implementation requires separate release. Stop on sync conflicts. |
| **B2** `gpt-builder2` · fixtures / evidence | #226 / #230 Macro archive, read-only | Signed retention finding delivered. Prepare SHA-256/size-verified copies or a precise retrieval handoff before Nov 24 (earlier ARM64 expiry 22:28 EST). No release upload, recapture or #268 source writes. | #209 / #216 remain parked pending lead disposition. Lead owns archive publication. |
| **B3** `gpt-builder3` · module DSP | #243 / #255 | #274 merged, D5 attached, and #198 readiness map signed. #273 merged. Resume existing branch with mechanical main sync; require all three Reverb blobs unchanged from `f314b859`, Reverb-only diff and new-head Lab/Golden. Ledger 1/2. | Repin source evidence and dispatch independent review only after new checks; never relabel prior capture. OB0 install/tag follows merge. |
| **B4** `gpt-builder4` · engine / sidecar | #199 S6 preflight | Nested map signed; public header destination approved with same bytes and include spelling. Internal-only headers follow owning components. Read-only collision and active-consumer manifest released. | S6 implementation waits for OB0 tag, dispositions, exact scope and ≥24h notice. |
| **B5** `gpt-builder5` · bounded support | #275 A10 read-only diagnosis | #216 evidence check delivered. A10 `57db5997` passed Echo/Scene in artifact 14564399481. Diagnose panic PCM and Groove STOP only. Lead retains source; no tests, thresholds, or reruns released. | Post two bounded follow-up proposals with concrete evidence. Separate #216 owner/Architect target decision remains pending. |

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
