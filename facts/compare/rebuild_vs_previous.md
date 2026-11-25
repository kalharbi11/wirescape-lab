<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Rebuild versus previous engine (CMP-1, draft collection plan)

- Previous engine as imported, upstream `44da1e4a235e606ebecd5bd6232f908d4df9b97f` (upstream main read via connector 2026-11-25 ET; commit 2026-11-14 19:54:06 UTC). Lab import `660556fbfb6ef30f828c68e9a05afa38ce0ee957` (2026-11-14 20:48:30 UTC, [snapshot](../../docs/context/SNAPSHOT.md)).
- Rebuild: lab main at dispatch, full SHA to be recorded; draft reading pin `4de561c87ae8ce240521b74a1f3f606cb3f49b94` is not a measurement.
- Same job and runner for each pair; Linux x64 and arm64; Release, no audio/MIDI devices or LAN. Timing rows are hosted-runner diagnostics. Delta = after minus before; ratio = after / before for nonzero before.
- No numeric measurements are claimed in this draft. Raw JSON, CPU, run link and exact subject pins will be recorded after collection.

| Metric | Common method / source | Before | After |
|---|---|---|---|
| Engine cost: abi2_poly8 mean/p99 | abi2_benchmark, 48 kHz/256 frames, five repeats, 4000 measured blocks; import does not accept --block | unmeasured: collection pending | unmeasured: collection pending |
| Heaviest bundled patch | wirescape_soak, common patch filenames, using import fixture bytes on both; 48 kHz/128, 30 s, p99/max and fraction of period | unmeasured: collection pending | unmeasured: collection pending |
| Module CPU | abi2_module_cpu_probe, common catalogue IDs, two instances, 48 kHz/128, channels 1 and 8, 2 s | unmeasured: collection pending | unmeasured: collection pending |
| Edit continuity | M4 CN A2 facts at ff20670; previous pin only if same harness runs unchanged | unmeasured: compatibility pending | unmeasured: source citation pending |
| Core module-ID references | literal ID grep in engine/control/host source; explicit core path sets, quoted catalogue IDs and matched lines | unmeasured: collection pending | unmeasured: collection pending |
| External module build | current SDK trial template preparation and external CMake configure/build, temporary directory | unmeasured: compatibility pending | unmeasured: collection pending |
| Cortex-M7 compile count | compile-only both FPUs, pinned x64-host Arm GNU 14.2.rel1 toolchain; old/new include paths | unmeasured: collection pending | unmeasured: collection pending |
| UI drag at 200 modules | current ui_frames.cjs, unchanged temporary overlay on each subject, if compatible | unmeasured: compatibility pending | unmeasured: collection pending |
| Bundled renderable | current golden render method, own bundled inventories, two runs per patch; list fixture IDs | unmeasured: collection pending | unmeasured: collection pending |
| Engine sidecar executable / catalogue module shared-library .text | file bytes and size -A; record artifact identity | unmeasured: collection pending | unmeasured: collection pending |

No result or acceptance claim. Draft-ahead under #589; release follows #567.

## Draft source compatibility observations (not runner measurements)

- Imported `native/engine2/tests/benchmark.cpp` accepts exactly two arguments and fixes 256 frames; the current `engine/tests/benchmark.cpp` also accepts its original 256-frame invocation. The common mean statistic is median of five 800-block repetition means, p99 is index 3960 of the 4000 sorted durations. Do not compare an imported 256-frame timing with an after 128-frame timing.
- Import and draft reading pin each have 24 bundled JSON filenames; all 24 blobs have the same Git blob SHAs at these two reading pins. Recheck against actual dispatch pins. Paired soak ranks common fixtures by p99; the worst block is reported separately. No device or Pi inference.
- Historical CN ledger pin: [ff206709b60cb26a34626c2ab38b1d864e59e4fb](https://github.com/kalharbi11/wirescape-lab/blob/ff206709b60cb26a34626c2ab38b1d864e59e4fb/facts/dsp/edit_continuity.md). It contains source-pinned final Delay-inclusive subject `8c9bb10d9eb8acf616395404c26ed0c3964e19d2` and earlier CN subjects. Keep actual subject, runner, method and run per cited row; do not relabel as a dispatch measurement. The import's capture capability must be checked before attempting the unchanged harness.
- The Cortex-M7 collector uses the existing portability workflow's exact archive SHA-256 on Linux x64; no ARM64-host compiler archive is configured. Record unavailable source context/compile failures separately.
- The comparison workflow is draft-only and not yet executed. The new workflow's manual dispatch requires a default-branch registration or an authorized premerge execution path. No raw JSON or timing delta is available yet.
