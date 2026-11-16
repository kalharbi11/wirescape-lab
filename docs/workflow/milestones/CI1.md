<!-- SPDX-License-Identifier: GPL-3.0-only -->
# CI1 — shorter Lab CI per merge

**Revision:** r1 — **ACTIVE.** Written and accepted by Fable, 2026-11-16 (ET), answering
[QUESTIONS](../QUESTIONS.md) Q6 (owner request). Runs alongside M0, M1 and M2 and revises none of them.
**Baseline commit:** `320576c`.
**Outcome:** the longest Lab CI job on a pull request drops from 9.48 min to about 5 min, and a pull
request that changes only notes and facts runs one job. The set of tests that runs on code is the same.
**Evidence:** [facts/tests/ci_durations_2026-11-16.md](../../../facts/tests/ci_durations_2026-11-16.md).
The 5 min figure is an estimate, not a pass mark.

## Task
| Task | Class | Allowed paths | Depends on | Merge |
|---|---|---|---|---|
| CI1.1 Lab CI time | B | `.github/workflows/ci.yml`; `apps/studio/package.json` (`test` script only); `tools/ci/changed_scope.py` (new); `tools/foundation/tests/test_changed_scope.py` (new); one new `facts/tests/ci_durations_*.md` | — | lead |

**Do, in one PR:**
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

## Single-writer area
`.github/workflows/ci.yml` belongs to CI1.1 while its PR is open. M2 PV1 places its drift check in a
new workflow file, which M2 r2 already allows.

## Out of scope
Compiler caches; the PortAudio build; `workers` above 1; the golden, facts and portability
workflows; required checks or any repository setting.

## Escalate
A test that passes at base and fails only when sharded: report the file, do not reorder, skip or
retry it. A core count of 2 on the Linux runners. An out-of-memory or link failure after step 1
that a level of 3 does not cure. Any K1 difference.

Signed: Fable, 2026-11-16
