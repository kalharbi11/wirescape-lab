<!-- SPDX-License-Identifier: GPL-3.0-only -->
# QUESTIONS — batched decisions for Fable

**State:** Q1–Q3 answered (M0 r2); Q4, Q5 open. The lead appends only genuinely
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
- **Fable answer (2026-11-15):** see ruling R1 in [M0 r1](milestones/M0.md). Three named quantities; command-to-sound is a range.

## Q2 — T0.5 impulse and tail metrics
- **Question:** What impulse/tail instrumentation is needed for reproducible, meaningful measurement?
- **Why contract does not settle it:** The acceptance meaning and instrumentation were not finalized.
- **Evidence:** [issue #51](https://github.com/kalharbi11/wirescape-lab/issues/51),
  [PR #60](https://github.com/kalharbi11/wirescape-lab/pull/60).
- **Lead's proposed answer:** require explicit signal stimulus, window and units, with unit tests
  against known synthetic responses. Fable must specify the final criterion.
- **Blocked:** acceptance of any T0.5 impulse/tail claims affected by that decision.
- **Fable answer (2026-11-15):** see ruling R2 in [M0 r1](milestones/M0.md). Unit impulse through the engine path; tail measured under the engine's own FTZ/DAZ setting.

## Q3 — T0.13 edit-continuity harness
- **Question:** What exact edits, timestamps, continuity metrics, and baseline method define the harness?
- **Why contract does not settle it:** T0.13 is class C design before a class B implementation.
- **Evidence:** [execution plan §Phase 0](../../proposals/0004-execution-plan.md),
  [known issues](../context/KNOWN_ISSUES.md).
- **Lead's proposed answer:** capture deterministic engine output around each edit and report
  phase reset, silent interval and maximum discontinuity without defining pass thresholds yet.
- **Blocked:** issuing implementation authority for T0.13.
- **Fable answer (2026-11-16):** see [proposals/0005](../../proposals/0005-edits-without-restart.md) section 4 and ruling R6 in M0 r2. End-to-end through the sidecar on the null sink, one capture flag, witness signals, six metrics, no thresholds.

## Q4 — refused edits in protocol v1 (0010 P5)
- **Question:** Should Studio, after a refusal, drop all later unacknowledged structural edits (P5 as
  written) or keep those still valid without the refused one, and retry `busy` refusals instead of dropping?
- **Evidence:** [issue #90](https://github.com/kalharbi11/wirescape-lab/issues/90) part 1 (reviewer
  opinion, not a ruling).
- **Blocked:** contracting protocol stage PV3 (client convergence).

## Q5 — owner allows bundled patches and presets to be reset (2026-11-16)
- **Question:** How to record the owner's decision in CONSTRAINTS, and what it changes for the golden
  gate, 0006 decision 6 / D3 (v1 reading), 0008 and 0003. Macro Oscillator models are kept; the
  owner's own patches are not covered.
- **Evidence:** [issue #90](https://github.com/kalharbi11/wirescape-lab/issues/90) part 2 (owner's words quoted).
- **Blocked:** nothing in flight; affects later contracts.
