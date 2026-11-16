<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CURRENT — lab workflow handoff

Updated: 2026-11-15 (ET). Baseline `main`: `71daa1cbf6a67fedd9d6b7e60a27351363ec7ea9`.
**This document is a WP1 draft. No milestone contract is active until Fable accepts M0 and
WP1 is merged.** All existing rules apply in the meantime. The live repository may move:
check exact head SHA and CI before every merge.

## Milestone and contract
- Proposed milestone: **M0 (Phase 0 measurement floor)**, revision **r0 DRAFT**:
  [M0 contract](milestones/M0.md). Acceptance and task-specific delegation pending Fable.
- [Execution plan](../../proposals/0004-execution-plan.md); [deployment plan](DEPLOY_PLAN.md).
  Owner accepted the proposed WP0 authority defaults; Fable must confirm each actual contract.

## Phase 0 issue / PR snapshot (2026-11-15 ET)
- **Merged evidence:** T0.1 [#41](https://github.com/kalharbi11/wirescape-lab/issues/41) / [PR #48](https://github.com/kalharbi11/wirescape-lab/pull/48);
  T0.2 [#42](https://github.com/kalharbi11/wirescape-lab/issues/42) / PR #46;
  T0.3 #43 / PR #47; T0.4 #55 / PR #64; T0.7 #53 / PR #57.
- **Open:** T0.5 [#51](https://github.com/kalharbi11/wirescape-lab/issues/51) / [PR #60](https://github.com/kalharbi11/wirescape-lab/pull/60);
  T0.6 [#52](https://github.com/kalharbi11/wirescape-lab/issues/52) / [PR #58](https://github.com/kalharbi11/wirescape-lab/pull/58);
  T0.8 [#54](https://github.com/kalharbi11/wirescape-lab/issues/54) / [PR #59](https://github.com/kalharbi11/wirescape-lab/pull/59);
  T0.11 [#66](https://github.com/kalharbi11/wirescape-lab/issues/66) / [PR #69](https://github.com/kalharbi11/wirescape-lab/pull/69);
  T0.12 [#61](https://github.com/kalharbi11/wirescape-lab/issues/61) / [PR #63](https://github.com/kalharbi11/wirescape-lab/pull/63).
- **Not contracted for M0:** T1.1 [#67](https://github.com/kalharbi11/wirescape-lab/issues/67) / [PR #70](https://github.com/kalharbi11/wirescape-lab/pull/70) is concurrent Phase 1 work, not authority to merge.
- **Verify/file:** T0.9 device results filing, T0.10 `facts/BASELINE.md`. T0.13 needs Fable's harness design. T0.14 is owner-controlled cloud-network access.

## Decisions and blockers
- Owner's [Fixed constraints](../context/CONSTRAINTS.md) remain binding.
- Fable must settle the T0.5 impulse/tail instrumentation and T0.8 latency definition/timing reference before accepting their evidence; see [QUESTIONS](QUESTIONS.md).
- Do not infer check results from this snapshot. A PR's green status must be verified on its current head.

## Next action by role
- **Fable:** review WP1, approve or revise M0 r0 and answer the open rulings.
- **gpt-lead:** once WP1 and the accepted contract are in force, reconcile live issue/PR heads and prepare the first batch.
- **Builders:** continue only existing explicitly assigned tasks until delegation becomes active.
- **Owner:** finish WP0 GitHub protections and decide whether T0.14 dependency hosts may be allowed.

The lead updates CURRENT at each batch boundary; Fable updates it after contract revisions.
