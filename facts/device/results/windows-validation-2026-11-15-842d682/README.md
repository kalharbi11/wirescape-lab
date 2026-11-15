<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Windows validation and speaker check, 2026-11-15 (ET)

Lab commit: `842d68225fb44c167b8714cb4cfc36455138273a` · Machine: Windows laptop, WASAPI shared,
Realtek laptop speakers, 48 kHz, 256 frames. Scope: Release build, silent app checks, real-engine
device-off bench and an owner-confirmed speaker check. The 15-minute real-device quick run was not
performed (`manifest.json`: `timed_quick_run_completed: false`).

Summary: `report.md`; outcomes: `pass-fail-skip.md`; numbers: `review.json`; owner statements:
`owner-observations.json`; privacy scan: `privacy-check.json` (493 text files, no findings).

Unpacked from `windows-validation-2026-11-15-842d682.zip`. Left out of git: `device-off/events.ndjson`
(16.7 MB), `device-off/offline_scripts/`, `*.log` (gitignored) and the two offline WAV renders in
`sound-check/` (768 KB each). The full ZIP belongs on the draft release `bench-2026-11-14`.
