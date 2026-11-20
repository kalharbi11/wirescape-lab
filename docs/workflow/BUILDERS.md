<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-20 (claude-architect acting as lead). The delivery lead owns this table. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · patch tools / Studio | W2 [#285](https://github.com/kalharbi11/wirescape-lab/issues/285) | Four Windows evaluation patches in `bench/owner_eval/windows/`, due 18:00 ET, device-off load + round-trip evidence. | Then OB-a3 [#287](https://github.com/kalharbi11/wirescape-lab/issues/287) under OB r2.2 (A19); `review-required`, Claude contract-review. Parks if S6 opens. |
| **B2** `gpt-builder2` · fixtures / evidence | #209 / #216 OB-f1, released by A20 | Offline CPU ranking of all 24 bundled v2 patches via `wirescape_cli play` (idle-only label), then the four UI rows plus native ACK on the winner at current main. #216's own paths plus one new facts file. | Architect sets OB-f2 targets from the result. #268 stays parked. Macro ZIPs are retained. |
| **B3** `gpt-builder3` · module DSP | M7 S7.5 [#288](https://github.com/kalharbi11/wirescape-lab/issues/288) | Quad VCA mode crossfade, ≥ 20 dB switch-click drop, T7.0 before/after, three-platform Golden. | Merge after the OB0 tag. Then S7.6 Delay (new issue, same rules). |
| **B4** `gpt-builder4` · engine / sidecar | W3 [#286](https://github.com/kalharbi11/wirescape-lab/issues/286) read-only | Windows MIDI path audit and owner decision tree, due 17:00 ET. | #199 product-PR inventory refresh (read-only). Owns any W4 engine/MIDI fix if the owner reproduces one. S6 waits for the OB0 tag plus at least 24 h notice. |
| **B5** `gpt-builder5` · bounded support | W1 [#284](https://github.com/kalharbi11/wirescape-lab/issues/284) | OSC In sender, device-off OSC loopback check and tests in `tools/examples/`, due 18:00 ET. | The #198 OB0 checklist stays ready for the owner's Pi run. A10 stays parked. |

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
