<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 10:00 ET (claude-architect run 14, acting lead: #309 merged; lanes re-sent after the owner's GPT run). The delivery lead owns this table; with no lead active, the Architect refreshes it every run. Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

**Merged today:**
- #311 OB-g2 `3f8f646`
- #325 ADSR trigger `d4884bd`
- #334 CV to Notes `5bff39c`
- #343 WEB1 `92747e4`
- #336 OB-b `3eeedd6`
- #344 T1.6a `ef11118`
- #309 OB-g7 `4efb204`

**Merge order (lead):**
1. #333 Gate Delay.
2. Poly Merge #328, last among the modules.
3. #298, then #291.
4. TR2 #345.
5. T1.6b, after the Architect's contract-review.
6. #322, #339, #324 and OB-g9 when green.

Each needs green Lab, Golden and M1 paired at its exact head; only the non-required `Offline facts / windows-latest` and advisory soak jobs may fail.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install | OB-a3 [#287](https://github.com/kalharbi11/wirescape-lab/issues/287) / [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `71bd210` | Fix the red native build and sanitizers. Merge `main`. Write the remaining five pin-7 cases in the granted paths. Result, then `review-ready` for claude-reviewer (CB2) ([direction](https://github.com/kalharbi11/wirescape-lab/pull/298#issuecomment-7104617999)). | #291 rebases after #298. |
| **B2** `gpt-builder2` · OSC heavy load | OB-g8 [#326](https://github.com/kalharbi11/wirescape-lab/issues/326) / [#339](https://github.com/kalharbi11/wirescape-lab/pull/339) `3616336` | Merge `main`. Fix the Windows `abi2_osc_heavy_ingress_tests` failure and the red builds and sanitizers. The hosted `osc-heavy` L0 now runs automatically (#309 merged) ([direction](https://github.com/kalharbi11/wirescape-lab/pull/339#issuecomment-7104616666)). | OB-f1 at candidate. |
| **B3** `gpt-builder3` · module DSP | OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) / [#322](https://github.com/kalharbi11/wirescape-lab/pull/322) `49b90cd` | **Ruling:** the +4,887 Ir/block on `host.keyboard` patches is #322's defect to fix. Use function-level attribution, and fix it in #322's files or with a no-behaviour change to `engine/voice/note_to_cv.h`. Merge `main` and regenerate S0 ([ruling](https://github.com/kalharbi11/wirescape-lab/pull/322#issuecomment-7104614163)). | #291 after #298, then S7.6 [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) → S7.7 → S7.8 → S7.9. |
| **B4** `gpt-builder4` · Poly Merge | **Poly Merge [#328](https://github.com/kalharbi11/wirescape-lab/issues/328)** (new start, run 14) | `task/328-poly-merge` on main with `0020` §7. Append to `bench/module_sets.json` `experimental` and regenerate S0. It merges after #333. #333 moved to CB1, which was already on it. | T1.6a done; the next engine work stays with CB1. |
| **B5** `gpt-builder5` · OB-g3 | OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317) / [#324](https://github.com/kalharbi11/wirescape-lab/pull/324) `9228093` | A native `--scripted-midi` failing test (enable an endpoint while running, inject, assert delivery), then the control-thread fix ([disposition](https://github.com/kalharbi11/wirescape-lab/pull/324#issuecomment-7098921069)). | Bounded OB-c marker/PCM proof. |
| **CB1** `claude-builder1` · engine writer | Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) / [#333](https://github.com/kalharbi11/wirescape-lab/pull/333) `a001a44`, then **T1.6b [#350](https://github.com/kalharbi11/wirescape-lab/issues/350)** | #333: merge `main`, append `essentials.gate_delay`, regenerate S0, and fix the M1 x64 row (LFO +2 % lead). Then the Result. | T1.6b → Architect contract-review → T1.6c → TR1e. |
| **CB2** `claude-builder2` · I/O and reviews | **OB-g9 [#348](https://github.com/kalharbi11/wirescape-lab/issues/348)** | `midi-m8/still` missing gate edge: failing test first, then the fix. The hosted L0 runs on its PR. | claude-reviewer for #298 when pinned. |
| **CB3** `claude-builder3` · transport / module build | M3 TR2 [#341](https://github.com/kalharbi11/wirescape-lab/issues/341) / [#345](https://github.com/kalharbi11/wirescape-lab/pull/345) `1a9b581` | Fix the Lab build, keep existing rows within 1 %, merge `main` and regenerate S0, then the Result. | MB1 → MB2 → MB3 after TR2. |

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

Signed: claude-architect, 2026-11-23
