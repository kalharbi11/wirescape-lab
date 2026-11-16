<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1 — shorter Lab CI per merge

**Revision:** r3 — **ACTIVE.** r3 (Fable, 2026-11-16, QUESTIONS Q12, issue #117) adds task CI1.4 and
invariant K9 and puts CI1.4 ahead of CI1.3 for `ci.yml`. Affected: CI1.3 (#109) keeps preparing but
pushes no `ci.yml` change until CI1.4 is merged, then rebases. CI1.1 and CI1.2 are merged and unaffected.
r2 (Fable, 2026-11-16, QUESTIONS Q7 and Q9) added tasks CI1.2 and
CI1.3 and invariants K6–K8. CI1.1 is merged (PR #96) and unaffected; nothing stops. r1 was written and
accepted by Fable, 2026-11-16 (ET), answering [QUESTIONS](../QUESTIONS.md) Q6 (owner request).
Runs alongside M0, M1 and M2.
**Baseline commit:** `320576c`.
**Outcome:** the longest Lab CI job on a pull request drops from 9.48 min to about 5 min, and a pull
request that changes only notes and facts runs one job. The set of tests that runs on code is the same.
**Evidence:** [facts/tests/ci_durations_2026-11-16.md](../../../facts/tests/ci_durations_2026-11-16.md).
The 5 min figure is an estimate, not a pass mark.

## Task
| Task | Class | Allowed paths | Depends on | Merge |
|---|---|---|---|---|
| CI1.1 Lab CI time | B | `.github/workflows/ci.yml`; `apps/studio/package.json` (`test` script only); `tools/ci/changed_scope.py` (new); `tools/foundation/tests/test_changed_scope.py` (new); one new `facts/tests/ci_durations_*.md` | — | lead |
| CI1.2 required native check names | B | `.github/workflows/ci.yml`; `tools/ci/` (check script, new); `tools/foundation/tests/` (its tests, new) | CI1.1 | lead |
| CI1.3 sanitizer compiler cache | B | `.github/workflows/ci.yml` (`sanitizers` job only); one new `facts/tests/ci_durations_*.md` | CI1.4 merged | lead, only under K8 |
| CI1.4 authenticated aggregate checks | B | `.github/workflows/ci.yml` (the four aggregate jobs only); `tools/ci/` verifier and its tests | CI1.2 | lead |

**CI1.4 (r3).** The four aggregate jobs (`linux-x64`, `linux-arm64`, `windows-x64`, `studio`) get
job-level `permissions: { contents: read, actions: read }` and send `github.token` as the
`Authorization` header on their one jobs-list request. The Studio inline check moves into the
`tools/ci/` verifier. Details and evidence: QUESTIONS Q12.

**CI1.2 (r2).** Seven check names are required by the repository: `foundation`, `linux-x64`,
`linux-arm64`, `windows-x64`, `sanitizers`, `studio`, `desktop`. Rename the `native` matrix legs to
`native build <platform>`. Add three literal jobs `linux-x64`, `linux-arm64`, `windows-x64`, each
with `needs: [scope, native]` and the same job-level condition as the other gated jobs. When one
runs, it passes only if exactly one job named `native build <its platform>` exists in this run
attempt and concluded `success`. The logic is a script with unit tests, as the `studio` aggregate does it.

**CI1.3 (r2).** `ccache` on the `sanitizers` job through `CMAKE_C_COMPILER_LAUNCHER` and
`CMAKE_CXX_COMPILER_LAUNCHER` on the configure line, compiler checked by content, cache capped at
500 MB, key from runner OS and architecture, compiler version text and the sanitizer flag string.
Print `ccache -s` after the build. File queue time per job for the 20 most recent pull-request runs.

**CI1.1, in one PR (merged):**
1. **Build parallelism.** Replace the fixed `2` (`CMAKE_BUILD_PARALLEL_LEVEL`, `--parallel 2`) on the
   `native` and `sanitizers` jobs with the runner's core count. Print the core count in the log.
2. **Studio shards.** Run the Studio Playwright suite as a three-way job matrix with
   `--shard=N/3`. `workers: 1` and `fullyParallel: false` stay. Failure artifacts get a name per shard.
3. **Linked desktop suite.** `apps/studio/package.json` `test` becomes `playwright test`. The
   `desktop` job is unchanged and stays the place where the desktop suite runs.
4. **Scope rule.** A first job runs `tools/ci/changed_scope.py` over the pull request's changed
   paths and outputs `code=true|false`. `native`, `sanitizers`, `studio` and `desktop` run when
   `code` is true; `foundation` always runs. `code` is false only when every changed path matches
   `proposals/**`, `docs/context/**`, `docs/workflow/**`, `facts/**` outside `facts/dsp/**`, or a
   `*.md` file at the repository root. It is true on `push`, on `workflow_dispatch`, on an empty or
   unreadable path list, and on any error. Plain `git`, no third-party action, no permission beyond
   `contents: read`.

## Invariants
- **K1** Same tests. `ctest -N` names on each native job and under `-R abi2` on the sanitizer job are
  identical at base and head. The Studio test count summed over the three shards equals
  `playwright test --list` at base. The desktop job's test count is unchanged.
- **K2** No test is removed, skipped, marked flaky or given a retry; no timeout is raised; no
  `continue-on-error`; sanitizer flags and options are unchanged.
- **K3** Every job runs on every push to `main` and on manual runs.
- **K4** Before step 4 is written, the builder greps `native/`, `apps/`, `tools/` and the CMake
  files for reads of the skipped directories and lists the result in the PR. A directory that a
  native, Studio or desktop test reads comes off the skip list.
- **K5** No other workflow file, Playwright config or test file changes.
- **K6** (CI1.2) No repository setting changes, no bypass, no job that succeeds without checking.
  An aggregate is skipped only when scope succeeded with `code=false` on a pull request; if scope
  failed it runs. Missing, duplicate, failed, cancelled or skipped platform job: the aggregate fails.
- **K7** (CI1.3) Pushes to `main` and manual runs do not restore the cache; they build cold and
  save. Pull requests restore and never save. Sanitizer flags, options and the 78 `-R abi2` test
  names are unchanged. No CMake file changes.
- **K9** (CI1.4) Workflow-level permissions stay `contents: read`; only the four aggregate jobs add
  `actions: read`. The token goes to one step as an environment variable and to `api.github.com`
  only; it is never printed, stored or output. Every HTTP error fails the job. No retry, no
  anonymous fallback. K6 holds unchanged.
- **K8** (CI1.3) Merged only if a warm pull-request run of `sanitizers` is at least 2.0 min shorter
  than 7.30 min. Otherwise the PR is closed and its numbers are filed as facts.

## Acceptance
1. CI1.1 merged with K1 shown as a table in the result comment (base and head lists or counts,
   with run links) and K4's grep result.
2. `test_changed_scope.py` runs in the `foundation` job and covers: notes only → false; one code
   path among notes → true; `docs/specs/` → true; `facts/dsp/` → true; `.github/` → true; empty
   list → true; a path outside every listed directory → true.
3. A new `facts/tests/ci_durations_<date>.md`, same method and table as the 2026-11-16 file, from
   the PR's own full run, stating that it is a pull-request run and the core count printed.
4. Report against the estimate: longest job, sum of runner-minutes. If `sanitizers` is still the
   longest job, the lead queues a question for a compiler-cache task; this contract gives no
   authority for one.

5. CI1.2: its own run shows the seven required names green with the three platform legs under
   their new names; unit tests cover each failing case in K6; PR #97, re-run after the merge,
   shows seven of seven with the native aggregates skipped and merges by the normal route.
6. CI1.3: K7 shown by one `main`-style cold run and one warm pull-request run with `ccache -s`
   output; the before and after table; the queue-time table; K8 applied.

## Single-writer area
`.github/workflows/ci.yml` belongs to CI1.4, then CI1.3, one open PR at a time. M2 PV1 places its drift check in a
new workflow file, which M2 r2 already allows.

## Out of scope
Compiler caches on any job but `sanitizers`; the PortAudio build; `workers` above 1; the golden, facts and portability
workflows; required checks or any repository setting.

## Escalate
A test that passes at base and fails only when sharded: report the file, do not reorder, skip or
retry it. A core count of 2 on the Linux runners. An out-of-memory or link failure after step 1
that a level of 3 does not cure. Any K1 difference.

Signed: Fable, 2026-11-16
