<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Builder queue

Updated 2026-11-23 11:45 ET (claude-architect run 18: **hand-over to gpt-lead**; Claude builder lanes closed). **gpt-lead owns this table from now on.** Builders read their row,
then their issue and the latest PR Result. [CURRENT](CURRENT.md) is the lead–Architect
handoff. [ROADMAP](ROADMAP.md) shows milestone order and completion.

**Merged today:**

| PR | Task | Merge commit |
|---|---|---|
| #311 | OB-g2 | `3f8f646` |
| #325 | ADSR trigger | `d4884bd` |
| #334 | CV to Notes | `5bff39c` |
| #343 | WEB1 | `92747e4` |
| #336 | OB-b | `3eeedd6` |
| #344 | T1.6a | `ef11118` |
| #309 | OB-g7 | `4efb204` |
| #357 | OB-g9 | `f02c4f5` |
| #345 | TR2 | `224d16f` |
| #360 | T1.6b | `7cc20c7` |

**Merge order (lead):**
1. #298, after the Architect's Claude review.
2. #333 (bounded LFO exception, see below).
3. Poly Merge #356.
4. #324, #339 and #322 when green.
5. T1.6c.
6. CAT-1 #358.

Each needs green Lab, Golden and M1 paired at its exact head. Only the non-required `Offline facts / windows-latest` and advisory soak jobs may fail.

| Builder / lane | Active issue and PR | Next action and evidence | Queued work and release condition |
|---|---|---|---|
| **B1** `gpt-builder1` · Studio / install, then module build | OB-a3 [#287](https://github.com/kalharbi11/wirescape-lab/issues/287) / [#298](https://github.com/kalharbi11/wirescape-lab/pull/298) `5ecf300` | Green at the exact head (six pin-7 tests; only Offline facts fails). Post the final Result. The lead pins `review-ready` with an inbox row and `needs/architect`, because the **Architect does the required Claude review**. | **M3 MB1** (`wire-describe`, equality test, catalogue from it; per 0009), released now that TR2 has merged. The lead files the issue. |
| **B2** `gpt-builder2` · OSC / I/O | OB-g8 [#326](https://github.com/kalharbi11/wirescape-lab/issues/326) / [#339](https://github.com/kalharbi11/wirescape-lab/pull/339) `6c86cd5` | Red builds and sanitizers. Merge `main` (OB-g9's egress drain is in), fix the build, then add the **OSC generation-pinning** fail-first test and fix ([note](https://github.com/kalharbi11/wirescape-lab/pull/339#issuecomment-7105337882)). Hosted `osc-heavy` L0 runs on the PR. | OB-f1 at candidate. |
| **B3** `gpt-builder3` · module DSP | OB-g6 [#307](https://github.com/kalharbi11/wirescape-lab/issues/307) / [#322](https://github.com/kalharbi11/wirescape-lab/pull/322) `49b90cd` | Merge `main`. Post function-level attribution of the `host.keyboard` rise on x64 and ARM64. A wrapper-only cause gets an Architect-named bounded exception (inbox row); otherwise fix it ([note](https://github.com/kalharbi11/wirescape-lab/pull/322#issuecomment-7105336061)). | #291 after #298, then S7.6 [#314](https://github.com/kalharbi11/wirescape-lab/issues/314) → S7.7 → S7.8 → S7.9. |
| **B4** `gpt-builder4` · modules | Gate Delay [#329](https://github.com/kalharbi11/wirescape-lab/issues/329) / [#333](https://github.com/kalharbi11/wirescape-lab/pull/333) `e7867b7` (from CB1); Poly Merge [#328](https://github.com/kalharbi11/wirescape-lab/issues/328) / [#356](https://github.com/kalharbi11/wirescape-lab/pull/356) `1e2f196` | **#333 first:** at `e7867b7`, Golden and the Instruction gate fail on all three platforms, which the bounded LFO exception does **not** cover. Merge `main` (TR2 changed Clock and S0), regenerate S0, and diagnose the Golden failure; a Golden difference is a defect. Then #356 (red: M1, Golden and native builds). | **CAT-1 [#358](https://github.com/kalharbi11/wirescape-lab/issues/358)** after #356. |
| **B5** `gpt-builder5` · OB-g3, then engine | OB-g3 [#317](https://github.com/kalharbi11/wirescape-lab/issues/317) / [#324](https://github.com/kalharbi11/wirescape-lab/pull/324) `b5736c4` | Red native builds and sanitizers on the new native fail-first test. Fix the build, show the test failing first, then the control-thread fix. | **M3 T1.6c** (move functions to `build/render/edit.cpp`, split `process_node`; 0007 rules 2–5). B5 becomes the **single engine writer** for T1.6c → TR1e. T1.6c needs the Architect's contract-review. The lead files the issue. |
| **CB1–CB3** `claude-builder1..3` | **Closed** (owner, 2026-11-23: Codex is back) | T1.6a, T1.6b, #333's integration, TR2, WEB1 and OB-g9 are done or handed over. | No new Claude builder work unless the owner reopens it. The Architect keeps rulings and Claude reviews. |

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
