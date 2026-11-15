<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Constraints

**Drafted by Keel 2026-11-14; accepted by the owner as is, 2026-11-15. The owner edits this file; agents don't.**

## Fixed (changing any of these needs the owner)
- Licences: GPL-3.0 product; MIT for the SDK, `module2.h` and `native/voice/`. Third-party licences kept.
- Devices off in tests, CI and agent runs; real devices only behind `--confirm-*`, run by the owner.
- Realtime rules in the audio path (no allocation, locks, I/O, exceptions, logging or JSON).
- The owner's saved patches and the bundled patches keep loading and sounding the same
  (an intentional sound change is listed in the PR and measured).
- Targets: Raspberry Pi 5 (ARM64 Linux) first, Windows x64 second; module DSP stays portable C++17.
- Renderer isolation: `contextIsolation` on, `nodeIntegration` off, OSC/LAN off by default.

## Open (may change with evidence; say what changed and why)
- Electron vs other shells; the separate-process design; the stdio JSON protocol and its version.
- ABI 2 details, including `legacy_index`, while no third-party modules exist.
- Native patch v1 import (keep, convert offline, or drop).
- Module/port/parameter IDs *before a public release*, with a lossless migration for existing patches.
- Folder layout, names, CMake structure, test suites and their split, CI jobs.
- Module format and SDK shape; how modules are built and loaded out of tree.
- Performance targets and thresholds.
