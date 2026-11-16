<!-- SPDX-License-Identifier: GPL-3.0-only -->
# QUESTIONS — batched decisions for Fable

**State:** Q1–Q3 answered (M0 r2); Q4, Q5, Q6 open. The lead appends only genuinely
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

## Q6 — CI time per merge (owner request, 2026-11-16)
- **Question:** The owner asked for ways to cut CI testing time where a run is not needed, so work merges
  faster. Which changes to `.github/workflows/ci.yml` and the test configs should be contracted, under
  which milestone, and with what guard so coverage is not lost? CI jobs are "Open" in CONSTRAINTS.
- **Evidence:** [facts/tests/ci_durations_2026-11-16.md](../../facts/tests/ci_durations_2026-11-16.md):
  Lab CI median 9.78 min per `main` run, 37.21 runner-min; sanitizers 9.48 (8.27 compile) and studio 9.42
  (8.68 serial Playwright) set the critical path; unchanged since 2026-11-14.
- **Reviewer's proposed answer (claude-reviewer, estimates, not measured):**
  1. Sanitizers: build only the ABI2 test targets that `ctest -R abi2` runs, parallel 4 (est. −4 to −6 min).
  2. Studio: shard Playwright across 2–3 jobs or raise workers where tests are independent; drop the linked
     desktop suite from Studio's CI `test`, since the `desktop` job runs it (est. −4 to −5 min).
  3. A changes job: PRs touching only `docs/`, `facts/`, `proposals/`, `*.md` skip native, sanitizer,
     Studio and desktop jobs, reporting success so required checks do not hang; `main` pushes always run all
     (est. ~35 runner-min saved per docs/facts PR; 5 of 10 open PRs are of this kind).
  4. ccache/sccache keyed on toolchain for native jobs; cache the pinned PortAudio build (est. −1 to −3 min
     per platform).
  Expected result after 1–2: about 5 min per merge, Windows on the critical path. Each change re-measured
  into `facts/tests/` before and after.
- **Blocked:** nothing in flight; owner wants it soon.
