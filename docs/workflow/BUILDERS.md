<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19 23:03 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | #259 / #263 merged `b148d34` | Exact-head Lab and device-off owner-folder proof passed. OB-a3 loader inventory signed on #203. | No OB-a3 source release. Pin older-shape/Save As contract and reserve a sole writer first. |
| **B2** `gpt-builder2` · fixtures / evidence | #226 / #230 retention complete in chat | Both original Macro ZIPs byte-verified; earlier expiry Nov 24 at 22:28 EST. Durable draft-release publication remains with lead. | #209 / #216 remain held; #268 source stays parked. |
| **B3** `gpt-builder3` · module DSP | #243 / #255 `da19529`, correction 2/2 | Exact-head Lab, three-platform Golden and Reverb Ir passed. Fresh full-mode capture active on #280 / #281. Lead handles refreshed D5. No further source release. | Pinned independent review after full MO and D5. Then lead merge and OB0 install/tag. |
| **B4** `gpt-builder4` · engine / sidecar | #199 S6 preflight delivered | [Final pinned mechanical map](https://github.com/kalharbi11/wirescape-lab/issues/199#issuecomment-7020815710) signed. | S6 implementation waits for OB0 tag, product PR dispositions and ≥24h notice. |
| **B5** `gpt-builder5` · bounded support | #198 OB0 install/tag preflight delivered | [Packaging and tag preflight](https://github.com/kalharbi11/wirescape-lab/issues/198#issuecomment-7020888787) signed; A10 diagnosis retained on #275. | No install, build or tag mutation released. A10 source stays parked. |

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

Signed: codex-lead, 2026-11-19, 15:04 EST
