<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0006 — One engine: removing ABI1 and the legacy types (design for T1.2–T1.4)

Fable, 2026-11-16 (ET), against `main` at `4956f2d`. Number `0005` stays reserved for the
edit/protocol design (T2.0). This note fixes the order, the invariants and the evidence for
T1.2, T1.3 and T1.4 so one builder can deliver them under contract `M1`.

## What is there today (observed)
- `wirescape_engine` (ABI1, `native/src/engine.cpp`, 555 lines) is a shared library. It is linked by
  the ABI1 tests, `wirescape_cli`, three engine2 probes, `abi2_integration_tests`,
  `qt_free_patch_coverage_tests` and, through `wirescape_app_engine`, by everything in the app
  (`native/engine2/CMakeLists.txt:61,69,114,157,166`; `native/CMakeLists.txt:8-90`).
- The facade `AppEngine` owns a `ws_engine` beside the real engine and uses it to load ABI1
  libraries (`native/control/app_engine.cpp:18,36,99`). A catalogue entry without a native
  descriptor becomes an ABI1 node (`app_engine.cpp:108`).
- `engine2::Engine` carries the shim: `add_abi1`, `rebind_abi1_descriptor`, `Node::legacy` and
  about 25 `legacy` branches, several inside `process_node` (`engine2.cpp:102-130, 278-311,
  555-641, 749-754, 821-823, 1015-1142`).
- The facade speaks ABI1 types: `ws_engine_config`, `ws_event`, `ws_meter`, and a synthesised
  `ws_module_descriptor` kept as "UI metadata only" (`app_engine.h`). Parameter events are found
  by numeric legacy id (`app_engine.cpp:144`). Gate events carry a routing rule: a gate drives
  envelopes, never oscillator pitch (`app_engine.cpp:147-150`).
- All 13 ABI1 modules in `native/modules` have a same-named ABI2 module in `native/modules2`.
- `legacy_index` is a field of `ws2_param` in the public MIT header `module2.h:43`.

## Decisions
1. **Five stages, one writer, in order.** Each PR lands green with golden identical. No stage is
   combined with another and nothing is renamed before stage 6.
2. **`legacy_index` stays in `module2.h`.** Removing it changes the public module header and
   every module's source; that belongs to the module API work in `0003`. From stage 5 the engine,
   facade, loader and sidecar no longer read it. Module tests that assert it stay.
3. **The facade takes engine types directly.** `engine2::Config` replaces `ws_engine_config`,
   `engine2::Meter` replaces `ws_meter`, `ws2_descriptor` replaces the synthesised descriptor. No
   new intermediate "host" types are invented in this milestone.
4. **Parameters are addressed by string ID at the facade.** The string is resolved to an index on
   the control side, once per message, from a per-module-type table built when the catalogue is
   built. Nothing on the audio thread sees a string.
5. **The gate routing rule is preserved, not redesigned.** It moves into one named function that
   takes native types. Changing what a gate does is a sound change and is out of scope.
6. **Native v1 patch reading is not removed in M1** unless the builder first shows, as facts,
   which native paths read v1 and that Studio migrates every bundled v1 patch without loss. Patch
   loading is a Fixed constraint. Until then stage 5 leaves v1 reading alone. This is the one part
   of T1.3 that is held.
   *Note, 2026-11-16 (QUESTIONS Q5):* the owner allows bundled patches to be reset. The hold
   stays through M1; after S6 removal needs only the fact list of native v1 readers and an
   offline conversion of any owner patch in v1, not the bundled-migration proof.
7. **Namespace and directory names stay** (`wirescape::engine2`, `native/engine2`) until stage 6.

## Stages

**S0 — snapshot tests (additive, any builder, before S2).** Commit (a) the module catalogue the
sidecar emits to the UI, as a snapshot file with a test that compares byte for byte; (b) the same
for one meter/status message and one parameter-set round trip in the protocol tests. These are the
tripwires for S2 and S5.

**S1 — T1.1** (contract M0, ruling R5). Frozen reference data; comparison tests stop linking ABI1.

**S2 — native-only catalogue.** `AppEngine` no longer creates a `ws_engine`. Remove
`app_engine_load_module`, ABI1 registration, `library_owners`, the ABI1 arm of
`app_engine_add_node_config`, `app_legacy_fixture.cpp` and the provider bridge with its test.
`wirescape_app_engine` stops linking `wirescape_engine`. The synthesised descriptor stays for now.

**S3 — remove the shim from the engine.** Delete `add_abi1`, `rebind_abi1_descriptor`,
`Node::legacy`, `legacy_ids`, `legacy_in`, `legacy_out`, every `legacy` branch, and the
`wirescape/module.h` include. Engine2 probes and tests that link ABI1 are converted to frozen data
or deleted.

**S4 — delete the ABI1 tree.** `native/src`, `native/modules`, `native/tests`, the
`wirescape_engine` target, `wirescape_cli` if it only drives `ws_engine`, the ABI1 capture tool
(its committed reference data and the reader stay), `engine.h` declarations that nothing uses, and
the matching names in `tools/dev.py`. `module.h` and the three structs go in S5.

**S5 — engine-native types (T1.3).** Two PRs. *S5a:* config and meter (decision 3), descriptor
consumers read `ws2_descriptor`. *S5b:* events and parameters (decisions 4, 5); then delete
`engine.h` and `module.h`. `native/web` and `native/tools/render` are converted in the PR that
removes the type they use.

**S6 — T1.4 rename and layout** to the `0002` tree. Stop-the-world: every other product PR is
merged or parked first. The PR contains only moves and identifier substitutions produced by a
script that is committed with it under `lab/`.

## Invariants (the reviewer checks these, quoted in the review request)
- **I1** No allocation, lock, I/O, exception, logging or JSON is added to `render`,
  `process_node`, event dispatch or `reset`. These stages only remove code from those paths.
- **I2** For native nodes the processing order, the `direct` fast-path condition, channel
  resolution and parameter smoothing are unchanged. `direct` becomes `!n.loop`.
- **I3** Replan and reconfigure keep their staging and state carry for native nodes exactly:
  the reuse test stays `prior->d == n.d && prior->config == n.config`; `save_state`/`load_state`
  calls are untouched.
- **I4** The FTZ/DAZ guard and the cross-thread surface listed in `engine2.h` are untouched.
- **I5** The public `Engine` API loses only `add_abi1` and `rebind_abi1_descriptor`.
- **I6** String-to-index parameter resolution runs on the control side only.
- **I7** Protocol output and the UI catalogue are byte-identical (S0 snapshots unchanged). Module,
  port and parameter IDs do not change.
- **I8** No existing ABI2 assertion, tolerance or expected value is loosened.

## Evidence per stage PR
1. Golden gate: 24 identical on Linux x64, ARM64, Windows x64.
2. Instruction counts (T0.6 tool) base vs head: no row more than 1 % worse. A worse row is an
   escalation, not a correction round.
3. Sanitizers job green; S0 snapshot tests unchanged and green.
4. A grep table in the PR showing zero matches for the symbols that stage removes, and, from S2,
   the link dependencies of `wirescape_app_engine` and the sidecar without `wirescape_engine`.
5. A list of every deleted test with one line each: it tested deleted ABI1 code, or its ABI2
   coverage now comes from frozen case *N* of T1.1. A test with neither reason is not deleted.
6. S6 only: the reviewer runs the committed script on the base commit and gets the head tree.

## Assumptions the builder verifies first (from inventory P1), before writing code
- **A1** No bundled patch, Studio path or sidecar path yields a catalogue entry without a native
  descriptor outside ABI1 tests.
- **A2** The sidecar loads no module through `ws_engine_load_module`; ABI2 modules come from the
  static catalogue.
- **A3** `native/web` is built by a CI job. If it is not, say so in the PR: it is then unverified.
- **A4** `wirescape_cli` and `native/cli/play.cpp`: which engine each drives.

A false A1 or A2 stops the work and goes to `QUESTIONS.md` with the evidence. This note was
written from grep-level reading of the tree, so these are the points most likely to be wrong.

## Not in this note
T1.6 (splitting `process_node`), T1.7 (transport), T1.8 (module build): each needs its own design
and should start only after S5, on the cleaned engine.

Signed: Fable, 2026-11-16
