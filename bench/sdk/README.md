<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Out-of-tree SDK authoring trial

The non-required `out-of-tree.yml` workflow runs on Linux x64 and Windows x64.

`python bench/sdk/out_of_tree_trial.py --platform linux-x64` copies
`native/sdk` outside the checkout, derives `trial.gain` from the SDK template,
and executes the documented CMake snippet without inventing an external SDK
package. The first out-of-tree failure ends that phase.

The runner refuses direct local execution unless GITHUB_ACTIONS=true and GITHUB_WORKSPACE matches the disposable checkout; it is not a command to run against a developer's working tree.

The runner then reproduces the in-tree steps in the disposable CI checkout.
Only the trial script, workflow, and evidence file are committed. A native
engine or sidecar code change is never committed. No audio/MIDI device or LAN
socket is opened. Linux and Windows require the existing repository build
toolchain; Windows reuses the pinned PortAudio build used by lab CI.

Each CI artifact contains `trial.json` and `out_of_tree_trial.md`, with exact
stderr for failures and per-command timings. The consolidated neutral evidence
is in `facts/code/out_of_tree_trial.md`.
