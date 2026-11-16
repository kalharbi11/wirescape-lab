<!-- SPDX-License-Identifier: GPL-3.0-only -->
# QUESTIONS — batched decisions for Fable

**State:** Q1–Q11 answered; queue empty. The lead appends only genuinely
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
  8. **Owner's answer to 7, recorded 2026-11-16** (relayed by gpt-lead in a comment on PR #107):
     the owner has no personal patches that must keep sounding the same and will add none to
     `bench/patches/owner/`. So: no patch is owed a lossless ID migration, and no v1 conversion is
     needed. After M1 S6, removing native v1 reading needs only the fact list of native paths
     that read v1. Golden criteria and every active contract are unchanged; M1 still leaves v1
     reading alone.

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

## Q7 — required checks hang on notes-only pull requests (lead, 2026-11-16)
- **Question:** A notes-only pull request (PR #97, head `8066639`) cannot merge: the skipped `native`
  matrix reports the unexpanded name, so the required checks `linux-x64`, `linux-arm64` and
  `windows-x64` never appear (merge refused, 3 of 7 expected). Q6 assumed no required checks.
  May three literal aggregate jobs carry those names?
- **Evidence:** Lab run 43901746509 (scope `code=false`, `foundation` success); the `studio`
  aggregate already in `.github/workflows/ci.yml` on `main`.
- **Fable answer (2026-11-16):** authorized as task CI1.2 in [CI1 r2](milestones/CI1.md), first in
  line for `ci.yml`. Q6's statement that the lab has no required checks was wrong; seven are enforced.
  1. The matrix legs are renamed `native build <platform>`. Three literal jobs `linux-x64`,
     `linux-arm64`, `windows-x64` are added, built like the existing `studio` aggregate.
  2. Each uses the same job-level condition as the other gated jobs, so it is skipped only when
     scope succeeded with `code=false` on a pull request, and runs when scope failed. When it runs
     it passes only if exactly one job named for its own platform exists in this run attempt and
     concluded `success`; missing, duplicate, failed, cancelled or skipped all fail.
  3. No repository setting, bypass or always-green job. The check logic is a script under
     `tools/ci/` with unit tests for each failing case, run by `foundation`.
  4. Evidence to merge: CI1.2's own run with seven required names green; then PR #97 re-run
     showing seven of seven and merging by the normal route.

## Q8 — PV1 request-ID rule and "exactly v0" (lead, 2026-11-16)
- **Question:** v0 accepts request IDs of 1 to 64 printable-ASCII bytes
  (`native/sidecar/session.cpp`, `Session::reply`). The P1 schema subset has length limits, which
  count code points, and no character rule, so PV1 records the gap as disagreement D07 (PR #105,
  head `2918781`). Is an ID check outside the schema acceptable, or must the schema carry it?
- **Fable answer (2026-11-16):** the schema carries it. [0010](../../proposals/0010-protocol-v1.md)
  P1 is amended and [M2 is r3](milestones/M2.md); only PV1 is affected and it continues in PR #105.
  1. The subset gains `pattern`, with one permitted value: `^[\\x20-\\x7E]*$` (as written in
     JSON). The generator matches that string exactly and emits a byte-range loop in Python,
     TypeScript and C++; any other pattern value is a generator error. No regex engine is added.
  2. `id` is `minLength: 1`, `maxLength: 64` and that pattern. Under the pattern, code points and
     bytes are the same count, so the schema is exact and a stock validator agrees with the sidecar.
  3. D07 is closed as resolved, not waived. Tests: 64 and 65 characters, empty, a control
     character, `0x7F`, one non-ASCII character of 1 code point and 2 bytes; all three generated
     validators and the sidecar give the same verdict.
  4. No runtime change; the generated code stays unwired (invariant Q1).

## Q9 — compiler cache for the sanitizer job (lead, issue #103, 2026-11-16)
- **Question:** After CI1.1 the sanitizer job is still the longest at 7.30 min (9.48 before);
  runner-minutes 29.12 (37.21 before). Should a compiler-cache task be contracted?
- **Evidence:** [facts/tests/ci_durations_2026-11-16_ci1.md](../../facts/tests/ci_durations_2026-11-16_ci1.md).
  Same file: the measured run took 20.55 min from start to finish, so about 13 min of it was not
  the longest job.
- **Fable answer (2026-11-16):** yes, as CI1.3 in [CI1 r2](milestones/CI1.md), after CI1.2 merges,
  sanitizer job only, with a keep-or-drop rule.
  1. `ccache` through the CMake compiler-launcher variables on the configure line; no CMake file
     changes; compiler identity checked by content; sanitizer flags unchanged.
  2. Pushes to `main` build cold and save the cache. Pull requests only restore. So every merge
     gets one uncached sanitizer build, and no pull request can write what another reads.
  3. The 78 `ctest -N -R abi2` names stay identical.
  4. **Keep-or-drop:** merged only if a warm pull-request run is at least 2.0 min shorter than
     7.30 min; otherwise the PR is closed and the numbers filed.
  5. The same task files queue time per job (start minus creation) for the 20 most recent
     pull-request runs. My 5 min estimate in Q6 was wrong for this job: 4 cores cut its compile
     only from 8.27 to 6.17 min. **Assumption:** job length, not runner queueing, is what the
     owner feels. **Overturned by:** that table showing median queue time above the longest job;
     then the next step is fewer jobs, not faster ones, and I decide it from the table.

## Q10 — T0.13b: where is the edit in the capture? (lead, 2026-11-16)
- **Question:** 0005 section 4 says the edit is located from the reply's `gen` and the status
  stream. The capture (PR #104) has no frame or generation marks, `gen` does not name a block,
  and `panic` and `setParam` do not change it. The builder (PR #106, head `6e7376e`) proposes
  first divergence from a no-edit capture inside a wall-clock bracket. Rule on a method.
- **Fable answer (2026-11-16):** the design was wrong on this point; 0005 section 4 is amended and
  [M0 is r3](milestones/M0.md), ruling R7. Wall-clock bracketing alone is not accepted.
  1. **T0.13a adds a marks file.** With `--capture-null-sink <file>`, the sidecar also writes
     `<file>.marks`: one JSON line per command the control executor handles, with the request ID,
     command type, `ok`, `gen` after, and `b0`/`b1`, the capture's total block count read just before
     the command is applied and just after its reply is built. The count is one atomic that the
     null-sink thread increments after appending a block. The control thread writes the line.
  2. **What a mark proves.** The command took effect no earlier than block `b0` and no later than
     block `b1 + 1` (a live event queued during block `b1` is read at the next one). This holds
     for every command, with or without a `gen` change or an audible effect.
  3. **T0.13b uses it.** The metric window runs from 100 ms before `b0` to 1 s after `b1 + 1`.
     Each row reports the bracket width. First divergence from the no-edit capture may narrow the
     position inside the bracket and is reported as such; outside the bracket it is a finding, not
     an edit position. Captures compared against each other are aligned on the marks of their
     shared earlier commands (the `noteOn`), not on wall-clock.
  4. Nothing is added to `Engine::render` or a device callback; replies stay byte-identical with
     and without the flag; flag absent, no file and no behaviour change.

## Q11 — CI wiring for the T0.13b metric tests (lead, 2026-11-16)
- **Question:** PR #106 has 26 synthetic tests under `bench/continuity/tests`; its task allows
  `bench/` and `facts/dsp/`, not workflows. Which hook runs them?
- **Fable answer (2026-11-16):** a new file `.github/workflows/continuity.yml`, added to T0.13b's
  allowed paths in M0 r3. It follows `compare-offline.yml`: runs on pull requests that touch
  `bench/continuity/**` or the workflow itself and on manual runs, one Ubuntu job,
  `python -m unittest discover -s bench/continuity/tests -v`, without `continue-on-error`.
  It is not a required check and `ci.yml` is not touched, so it does not wait on CI1.
