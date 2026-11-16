<!-- SPDX-License-Identifier: GPL-3.0-only -->
# QUESTIONS — batched decisions for Fable

**State:** seed queue for M0 r0, pending Fable's review. The lead appends only genuinely
unresolved questions; Fable answers them in place in one `fable: run questions` session.
If an answer changes a frozen contract, Fable increments the revision, lists affected tasks,
and records the stop/replan instruction in `CURRENT.md`.

## Q1 — T0.8 latency measurement
- **Question:** Which physical/observed quantity and timing reference must the latency tool report?
- **Why contract does not settle it:** A Python midpoint/command ACK is not a validated audio output
  callback or DAC onset; the measurement definition needs a design decision.
- **Evidence:** [issue #54](https://github.com/kalharbi11/wirescape-lab/issues/54),
  [PR #59](https://github.com/kalharbi11/wirescape-lab/pull/59).
- **Lead's proposed answer:** distinguish software command/ACK timing from true electrical loopback
  measurement; require proven timestamp relationship before claiming hardware onset.
- **Blocked:** acceptance of T0.8 as a hardware round-trip measurement.
- **Fable answer:** pending.

## Q2 — T0.5 impulse and tail metrics
- **Question:** What impulse/tail instrumentation is needed for reproducible, meaningful measurement?
- **Why contract does not settle it:** The acceptance meaning and instrumentation were not finalized.
- **Evidence:** [issue #51](https://github.com/kalharbi11/wirescape-lab/issues/51),
  [PR #60](https://github.com/kalharbi11/wirescape-lab/pull/60).
- **Lead's proposed answer:** require explicit signal stimulus, window and units, with unit tests
  against known synthetic responses. Fable must specify the final criterion.
- **Blocked:** acceptance of any T0.5 impulse/tail claims affected by that decision.
- **Fable answer:** pending.

## Q3 — T0.13 edit-continuity harness
- **Question:** What exact edits, timestamps, continuity metrics, and baseline method define the harness?
- **Why contract does not settle it:** T0.13 is class C design before a class B implementation.
- **Evidence:** [execution plan §Phase 0](../../proposals/0004-execution-plan.md),
  [known issues](../context/KNOWN_ISSUES.md).
- **Lead's proposed answer:** capture deterministic engine output around each edit and report
  phase reset, silent interval and maximum discontinuity without defining pass thresholds yet.
- **Blocked:** issuing implementation authority for T0.13.
- **Fable answer:** pending.
