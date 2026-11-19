<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-19 06:33 EST. The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | [#259](https://github.com/kalharbi11/wirescape-lab/issues/259) / [#263](https://github.com/kalharbi11/wirescape-lab/pull/263) OB-a2, draft at `a3544de` | [Signed Result](https://github.com/kalharbi11/wirescape-lab/pull/263#issuecomment-7007776105): SR8 accepted and 32/32; required Windows Lab failed. Source is parked, ledger 1/2. Independently inventory safe-save entry points and acceptance gaps for #203, read-only. | Resume #263 on a lead disposition of the Windows failure. #192 and OB-a3 implementation need a separate release. Rotate after #263 reaches final disposition. |
| **B2** `gpt-builder2` · fixtures / evidence | [#268](https://github.com/kalharbi11/wirescape-lab/issues/268) A10 replacement | [Lead release](https://github.com/kalharbi11/wirescape-lab/issues/268#issuecomment-7007849558) permits the test-local S5b API adaptation and sidecar filename fix. Fresh chat, same role. Publish eight exact-head case outcomes and binary hash, and retain the closed #214 ledger. | [#209 / #216](https://github.com/kalharbi11/wirescape-lab/pull/216) UI timing facts remain parked behind A10 disposition and lead release. Architect sets OB-f2 targets using measured facts. |
| **B3** `gpt-builder3` · module DSP | [#267](https://github.com/kalharbi11/wirescape-lab/issues/267) matched evidence, then [#243 / #255](https://github.com/kalharbi11/wirescape-lab/pull/255) | Use one dedicated hosted workflow and collect actual 1.5s/48k MO for both separately built pins, provenance and peak ≤1.00 FS. #255 source stays parked at `f314b85`, ledger 1/2. Lead owns D5 release and reconciles Windows base CI. | Rotate after this Reverb handoff. #202 sound tasks follow their own release and dependencies. |
| **B4** `gpt-builder4` · engine / sidecar | [#199](https://github.com/kalharbi11/wirescape-lab/issues/199) S6 readiness, read-only | [Initial inventory](https://github.com/kalharbi11/wirescape-lab/issues/199#issuecomment-7007380186) complete. Fresh chat reconciles unresolved CLI/test/vendor/build locations with contract references and carries S5b reviewer Lows. | S6 source waits for OB0 tag, agreed map, disposition of open product PRs and a window announced at least a day ahead. #200 follows S6. |
| **B5** `gpt-builder5` · bounded support | [#263](https://github.com/kalharbi11/wirescape-lab/pull/263) / [#255](https://github.com/kalharbi11/wirescape-lab/pull/255) read-only Windows baseline triage | Independent audit delivered. Compare exact-head and baseline logs, pin the first real errors and nearest passing control, and give the lead the smallest evidence-backed action. | Available for a scoped support task after Result. No product writer slot. |

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
