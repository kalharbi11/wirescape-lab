<!-- SPDX-License-Identifier: GPL-3.0-only -->
# DEV_RUN — build and test from a chat session, with no sandbox

**For every builder, and especially ChatGPT chat builders (Architect, 2026-11-23).** You do not
need a local environment, a Codex sandbox or the Pi to build, test, sanitize or profile. Your
**PR is your environment**: GitHub's hosted runners do the work and they are free for this public
repo. The first two engines were built this way. Hand a task to Codex only for *interactive*
debugging that these two tools cannot express, and say why in your Result.

## Tool 1: push a commit, and Lab CI runs everything
Every push to your PR branch runs the full Lab CI: native build and tests on linux-x64,
linux-arm64 and windows-x64, plus sanitizers, Studio and the other workflows the change touches.
Read the PR's checks and their job logs through the GitHub connector. This is also the **evidence
run**: contracts accept only exact-head Lab CI and their named workflows.

## Tool 2: `/dev-run`, a targeted run whose result comes back as a PR comment
Post a **PR comment** whose first line is a request. Within a minute it gets a 👀 reaction. In about
5–25 minutes a comment starting **dev-run** appears. It gives the head SHA tested, a pass/fail row per
platform, each step's exit code and time, the failed test names, the last 150 log lines, and a
link to the full logs. You do not need to download artifacts.

```
/dev-run <profile> [platform=linux-x64|linux-arm64|both] [filter=<ctest regex>]
         [target=<a,b>] [build=release|asan] [cmd="<command>"] [timeout=<seconds>] [repeat=<n>]
```
| Profile | Does | Notes |
|---|---|---|
| `test` | Release build (the same configure as `tools/dev.py build --headless`), then `ctest` (`-R filter`) | default timeout 60 s per test, as in CI |
| `asan` | ASan+UBSan build (the Lab CI `sanitizers` flags), then `ctest` | `halt_on_error=1` |
| `cmd` | builds (`build=release` → `build/native`, `build=asan` → `build/asan`), then runs one command | `cmd` must start with `build/native/`, `build/asan/`, `python3 tools/`, `valgrind ` or `ctest `. It runs without a shell, so no pipes or `;`. `repeat` runs it n times |
| `studio` | `npm ci`, Chromium, `npm test` in `apps/studio` (`-g filter`) | linux-x64 only |

**Keep runs short.** Add `target=<test executable>[,…]` to build only what the test needs. A full build is about as long as Lab CI; a target build with the shared compiler cache usually takes a few minutes. Ask for `platform=both` only when the arm64 result matters.

Examples:
```
/dev-run test target=abi2_osc_graph_ingress_tests filter=abi2_osc_graph_ingress
/dev-run asan platform=both filter=abi2_osc_(host_service|graph_ingress)_tests timeout=600
/dev-run cmd build=asan target=abi2_osc_graph_ingress_tests cmd="build/asan/abi2_osc_graph_ingress_tests" timeout=900
/dev-run cmd cmd="valgrind --tool=callgrind --callgrind-out-file=cg.out build/native/wirescape_render <args>"
/dev-run test filter=engine2 repeat=5
/dev-run studio filter="groove wheel"
```
A bad request gets a **dev-run refused** comment that gives the reason.

**What it runs:** the PR's head at the moment of the request, on hosted runners. A later push
does not change a run that has already started; check the SHA in the result. Requests are accepted
only on open PRs in this repo (forks are refused) and only from the owner's account, which is the
account every lab agent posts as. The run has a read-only token and no secrets.

## Test-first loop for a chat builder
1. Open your task PR as a **draft** (`Closes #<issue>`), on `task/<issue#>-<slug>`.
2. Commit the failing test only. Post `/dev-run test filter=<new test>` and record the expected
   failure in your next Result or progress comment.
3. Commit the fix, then `/dev-run` the same filter, plus `asan` if the task touches native memory or
   realtime code.
4. Mark the PR ready only when **exact-head Lab CI** is green. Post the Result
   (template in [README](README.md)) citing the CI run, not the dev-run.

## Rules
- **Diagnostic, not evidence.** A dev-run comment never satisfies a contract criterion, a gate or a
  review request. Exact-head Lab CI and the contract's named workflows do.
- **Never loosen to pass:** do not change a load, deadline, queue size, tolerance or cap to make a
  dev-run green. Report the failure.
- **One request in flight per PR.** Send the next one after the result comment arrives. Do not
  re-request unchanged code to "see if it passes": use `repeat=<n>` once instead.
- **Keep working while it runs (owner, 2026-11-24).** Do not end your session after a request or a
  push. Carry on with the next step of the task, the next task in your lane, or evidence
  preparation. With nothing else to do, wait and re-check: a dev-run takes about 2–5 min, and Lab CI
  about 10–15 min. Check once per expected duration, not continuously. See
  [Builder continuation](README.md#builder-continuation-after-ci).
- **Not covered:** windows-x64 (push and read Lab CI instead), real audio or MIDI devices
  (owner only), and Pi soaks (the Pi bridge, postponed to the OB1 candidate). A paired base/head
  measurement uses the contract's own workflow (for example M1 paired), never two dev-runs.
- Timing numbers from hosted runners are noisy. Cite them as diagnostics, never as `facts/`.

Trust model and code: [`.github/workflows/dev-run.yml`](../../.github/workflows/dev-run.yml),
[`tools/ci/dev_run.py`](../../tools/ci/dev_run.py) (tests: `python -m unittest tools/ci/test_dev_run.py`).
