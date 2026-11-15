<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Out-of-tree SDK module trial

| Field | Value |
|---|---|
| Trial | ABI2 signal processor based on native/sdk/template; new ID: trial.gain |
| Lab source | kalharbi11/wirescape-lab, task/25-out-of-tree-sdk-trial |
| Date (New York) | 2026-11-14 |
| OS | Linux x64 and Windows x64 CI |
| Total steps (per OS) | Pending CI execution |
| Steps completed out of tree (per OS) | Pending CI execution |
| Core files edited in disposable checkout | Pending CI execution |
| Step durations (seconds) | Pending CI execution |
| Devices | No audio or MIDI devices opened |

The trial follows docs/MODULE_BUILD_GUIDE.md §§B.0–B.5 and
docs/SDK_AUTHOR_GUIDE.md §§1, 2, 12. It copies the MIT SDK and template
to a directory outside the repository, tests the documented CMake entry, then
continues at the first external failure in a disposable CI checkout.

The reported source edits apply only to CI's temporary checkout. No native,
Studio, sidecar or engine product code is committed by the trial.

The exact per-OS command outcomes, error strings and durations are published
in the out-of-tree workflow artifact and consolidated here after execution.
