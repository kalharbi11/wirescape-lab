<!-- SPDX-License-Identifier: GPL-3.0-only -->
# QUESTIONS — batched decisions for Fable

**State:** Q1–Q6 answered; queue empty. The lead appends only genuinely
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
- **Fable answer (2026-11-16):** `busy` is retried and drops nothing; every other refusal keeps P5's
  drop of later unacknowledged structural edits. [0010](../../proposals/0010-protocol-v1.md) P5 is
  amended in this PR; P4 and the engine side are unchanged, so PV3 can be contracted as designed.
  1. **Transient (`busy`):** `D` and undo history are untouched. The client resends `applyGraph(D)`
     after 100, 200, 400, 800 ms, then once per heartbeat (P8), and shows "engine busy, edits pending"
     from the fourth try. `unavailable` is a session loss and follows P6.
  2. **Rejected (every other code):** P5 as written, plus two requirements: undo history is cut back
     to the restored snapshot in the same step, and the one message shown names the refused edit and
     the number of later edits discarded.
  3. **"Keep later edits that still apply" is declined for PV4.** Studio's history is whole-document
     snapshots (`apps/studio/src/patch/History.ts`), not operations, so removing one edit from under
     later ones needs a new three-way document merge. With `busy` taken out, what remains is edits the
     local check missed (`limit`, catalogue disagreement), where the user needs to see the state reset.
  4. **Assumption:** rejected refusals with later edits outstanding do not occur in normal patching.
     **Overturned by:** refusal counts by code in P2 (`edit_paths.md`) or T0.13b runs showing a
     non-`busy` refusal with two or more unacknowledged later edits outside fault injection. Then the
     merge is designed as its own stage after PV4.

## Q5 — owner allows bundled patches and presets to be reset (2026-11-16)
- **Question:** How to record the owner's decision in CONSTRAINTS, and what it changes for the golden
  gate, 0006 decision 6 / D3 (v1 reading), 0008 and 0003. Macro Oscillator models are kept; the
  owner's own patches are not covered.
- **Evidence:** [issue #90](https://github.com/kalharbi11/wirescape-lab/issues/90) part 2 (owner's words quoted).
- **Blocked:** nothing in flight; affects later contracts.
- **Fable answer (2026-11-16):** recorded; nothing is deleted or moved now, and M0, M1 and M2 are unchanged.
  1. **CONSTRAINTS:** this PR adds an "Owner's change, 2026-11-16" line under the patch bullet,
     in the form used for the 2026-11-15 change. The file is the owner's; merging this PR is the
     owner's confirmation of the wording.
  2. **Scope:** resettable: the 25 files in `apps/studio/patches/` and every module's presets, CHAOS
     included. Kept: Macro Oscillator models. The six files in `native/modules2/macro_oscillator/patches/`
     are source diffs applied to the vendored code at build time (`apply.cmake`, `*.patch`), not sound
     patches; the decision does not touch them. The owner's own patches stay under the Fixed rule.
  3. **Golden gate:** unchanged through M1 and M2. The gate shows that engine work does not change
     module sound, which does not depend on the patches being product content, so the current 25
     files stay where they are as its input and "24 identical" stays a criterion. The reset is one
     task after M1 S6 and T1.8: the 25 files move to `bench/patches/legacy/` as gate input and the
     owner makes the new bundled set. After that, a legacy file that stops loading because of an
     intended format change is retired in that PR, listed, provided no module loses its only
     golden render (a coverage patch is added first).
  4. **0006 decision 6 / plan D3:** native v1 reading still stays through M1 (M1 r2 is frozen and
     gains nothing from a revision). After M1 S6 it is removed. The condition "Studio migrates
     every bundled v1 patch without loss" is dropped; what remains is the fact list of native
     paths that read v1 and one offline conversion of any owner patch in v1. This settles the Open
     item "Native patch v1 import" as: drop, with offline conversion. 0006 carries a note.
  5. **0008:** no change. "Existing documents are not migrated" still protects the owner's patches;
     remade bundled patches get the `host` default as new documents.
  6. **0003:** preset data is not carried into `panel.json`; each module's preset list starts empty
     at conversion. Macro Oscillator model order and identity are kept. Lossless ID migration is
     still owed to the owner's own patches only.
  7. **For the owner:** `bench/patches/owner/` is empty, so no gate sees the owner's own patches.
     Add the ones that must keep sounding the same, or say there are none; if there are none, the
     ID migration and the v1 conversion in 4 and 6 are not needed.

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
- **Fable answer (2026-11-16):** contracted as its own one-task milestone, [CI1](milestones/CI1.md),
  dispatchable now; M0, M1 and M2 are not revised. Of the reviewer's four proposals:
  1. **Sanitizers: changed.** Build parallelism goes from 2 to the runner's core count on the
     sanitizer and native jobs. Building only the `abi2` targets is not contracted: nearly every
     test in `native/` is named `abi2_*`, so the saving is unshown. The builder may add it only with a
     target list and a measured saving of 1 min or more.
  2. **Studio: accepted.** Three Playwright shards as a job matrix, `workers: 1` kept inside each
     shard, and the linked desktop suite removed from Studio's `test` (the `desktop` job runs it).
     Raising workers is declined: it needs proof that tests in one file set share no state.
  3. **Changes job: accepted, narrower.** `foundation` always runs. Native, sanitizer, Studio and
     desktop jobs are skipped on a pull request that touches only `proposals/`, `docs/context/`,
     `docs/workflow/`, `facts/` outside `facts/dsp/`, and top-level `*.md`. `docs/specs/` counts as
     code (PV1's schema lives there). Any error, `main` push or manual run means run everything. The lab has no
     required checks, so skipped jobs need no stand-in success.
  4. **Compiler cache and PortAudio cache: not now.** PortAudio is 0.45 min. A cache on the
     sanitizer job becomes a second task only if that job is still the longest after CI1.
  **Guards:** the list of tests run is identical before and after (ctest names, Playwright counts
  summed over shards); the path rule is a script with unit tests; no test is removed, skipped or
  retried; before and after go in `facts/tests/`. **Expected (estimate):** longest job about 5 min,
  Windows, against 9.48 now. **Assumptions:** the hosted Linux runners have 4 cores; no test file depends
  on another having run first. **Overturned by:** `nproc` of 2, or a test that fails only when sharded.
