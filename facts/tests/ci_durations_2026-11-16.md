<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Hosted CI durations, 2026-11-16

- **Date (America/New_York):** 2026-11-16
- **Commit (main):** `320576c322c81b8feae76f18ff0cb58ba1f6feb9`
- **Source:** [Lab CI run 43837588432](https://github.com/kalharbi11/wirescape-lab/actions/runs/43837588432)
  (`push` on `main`) for job and step times; the last 40 completed `push` runs on `main`
  (2026-11-15 04:59 ET to 2026-11-16 04:11 ET) for the run-time range.
- **Measurement:** job and step `completed_at` minus `started_at`. Run time is the run's `updated_at`
  minus `run_started_at`, which includes the wait for a runner. Minutes, two decimal places.
- **Earlier baseline:** [ci_durations.md](ci_durations.md) (2026-11-14, `0a58849`).

## Lab CI jobs, run 43837588432

| Job | Runner | Job (min) | Build step (min) | Test step (min) | Other steps (min) |
| --- | --- | ---: | ---: | ---: | ---: |
| sanitizers | `ubuntu-latest` | 9.48 | 8.27 (ASan/UBSan compile) | 1.07 (`ctest -R abi2`) | 0.14 |
| studio | `ubuntu-latest` | 9.42 | 0.58 (npm ci, Playwright install) | 8.68 (Playwright + linked desktop) | 0.16 |
| windows-x64 | `windows-latest` | 7.00 | 4.60 (+0.45 PortAudio fetch/build) | 1.42 | 0.53 |
| linux-arm64 | `ubuntu-24.04-arm` | 4.68 | 3.57 | 0.93 | 0.18 |
| linux-x64 | `ubuntu-latest` | 3.88 | 2.88 | 0.88 | 0.12 |
| desktop | `ubuntu-latest` | 2.02 | 0.25 (apt, npm ci) | 1.60 | 0.17 |
| foundation | `ubuntu-latest` | 0.73 | — | 0.43 | 0.30 |
| **Sum** | | **37.21** | | | |

- First job start minus run creation: 2.92 min (09:11:59Z to 09:14:54Z).
- Run time: 13.7 min.

## Run-time range, last 40 completed `push` runs on `main`

| Workflow | Successful runs | Min (min) | Median (min) | Max (min) |
| --- | ---: | ---: | ---: | ---: |
| Lab CI | 27 | 8.10 | 9.78 | 18.75 |
| Golden patch renders | 3 | 4.57 | 5.10 | 7.47 |
| Generate device-off facts | 8 | 18.00 | 39.35 | 79.28 |
| Cortex-M7 portability | 1 | 0.90 | 0.90 | 0.90 |

## Configuration observed at `320576c`

- `apps/studio/playwright.config.ts`: `workers: 1`, `fullyParallel: false`.
- `apps/desktop/playwright.config.cjs`: `workers: 1`, `fullyParallel: false`.
- `apps/studio/package.json` `test`: on Linux CI, also runs `npm --prefix ../desktop ci`, the desktop build
  and the desktop Playwright suite. The separate `desktop` job runs the desktop suite as well.
- `.github/workflows/ci.yml` sanitizers job: `cmake --build build/asan` (all targets), then `ctest -R abi2`.
- `CMAKE_BUILD_PARALLEL_LEVEL: '2'` on native and sanitizer jobs. No compiler cache. No path filters on
  `pull_request`. `.github/workflows/ci.yml` last changed in `ddf85e8` (2026-11-14).
