<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Wirescape device-off results

Date: 2026-11-14 (America/New_York)
Lab source: cd9a6a5d447bf6c078df0c9b9f9f5df869e71ff2

These are device-off checks. No real audio or MIDI run has started, and no audio recording is included. Null-sink resource samples do not measure loaded-patch hardware performance.

| Check | Raspberry Pi 5 | Windows laptop |
|---|---|---|
| Release engine, Studio, Desktop | Passed | Passed |
| Native tests | 108 passed, 0 failed | 4 setup checks passed |
| Device harness unit tests | 15 passed | 15 passed |
| Comparison harness unit tests | 15 passed | 15 passed |
| Silent app smoke | 1 expected, 0 unexpected/skipped/flaky | Passed; isolated launcher check also passed |
| Real-engine scenario-all dry run | 23,874 acknowledgements; 0 refusals; exit 0 | 23,874 acknowledgements; 0 refusals; exit 0 |
| Real-engine idle null-sink comparison | Completed; hello validated | Completed; hello validated |
| Report and manifest | Present in both run ZIPs | Present in both run ZIPs |
| Result privacy scan | No findings | No findings |

The Pi app smoke used Xvfb. It verifies functional ARM64 Electron/native integration; physical-display responsiveness and audio/MIDI remain pending.

## Included files

- pi5-device-off-2026-11-14-cd9a6a5.zip: complete Pi device-harness dry run.
- pi5-compare-null-2026-11-14-cd9a6a5.zip: Pi idle real-engine null-sink sample.
- windows-device-off-2026-11-14-cd9a6a5.zip: complete Windows device-harness dry run.
- windows-compare-null-2026-11-14-cd9a6a5.zip: Windows idle real-engine null-sink sample.
- windows-compare-synthetic-2026-11-14-cd9a6a5.zip: synthetic sampler check from the Windows handoff.
- pi5-device-off-report.md and windows-device-off-report.md: readable dry-run reports.
- pi5-source-build-summary.json and pi5-app-smoke-summary.json: source/build and app-smoke evidence.

The Windows checks and three Windows archives were supplied by the other agent's completed handoff and verified against the existing draft-release hashes. Tracked source files remain unchanged.

## Pending owner-run sequence

1. Pi 15-minute quick run.
2. Windows 15-minute quick run.
3. Pi 60-minute full run.
4. Reference-tool comparisons.

Only the owner starts commands with --confirm-audio or --confirm-midi. Each real run needs its own report review, privacy check, and archive. The benchmark release remains a draft.
