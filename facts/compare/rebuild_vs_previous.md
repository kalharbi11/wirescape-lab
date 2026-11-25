<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Rebuild versus previous engine (CMP-1, draft collection plan)

- Previous engine as imported, upstream `44da1e4a235e606ebecd5bd6232f908d4df9b97f` (upstream main read via connector 2026-11-25 ET; commit 2026-11-14 19:54:06 UTC). Lab import `660556fbfb6ef30f828c68e9a05afa38ce0ee957` (2026-11-14 20:48:30 UTC, [snapshot](../../docs/context/SNAPSHOT.md)).
- Rebuild: lab main at dispatch, full SHA to be recorded; draft reading pin `4de561c87ae8ce240521b74a1f3f606cb3f49b94` is not a measurement.
- Same job and runner for each pair; Linux x64 and arm64; Release, no audio/MIDI devices or LAN. Timing rows are hosted-runner diagnostics. Delta = after minus before; ratio = after / before for nonzero before.
- No numeric measurements are claimed in this draft. Raw JSON, CPU, run link and exact subject pins will be recorded after collection.

| Metric | Common method / source | Before | After |
|---|---|---|---|
| Engine cost: abi2_poly8 mean/p99 | abi2_benchmark, 48 kHz/256 frames, five repeats, 4000 measured blocks; import does not accept --block | unmeasured: collection pending | unmeasured: collection pending |
| Heaviest bundled patch | wirescape_soak, common patch filenames and identical fixture bytes where accepted; 48 kHz/128, 30 s, p99/max and fraction of period | unmeasured: collection pending | unmeasured: collection pending |
| Module CPU | abi2_module_cpu_probe, common catalogue IDs, two instances, 48 kHz/128, channels 1 and 8, 2 s | unmeasured: collection pending | unmeasured: collection pending |
| Edit continuity | M4 CN A2 facts at ff20670; previous pin only if same harness runs unchanged | unmeasured: compatibility pending | unmeasured: source citation pending |
| Core module-ID references | literal ID grep in engine/control/host source; explicit scope and matched lines | unmeasured: collection pending | unmeasured: collection pending |
| External module build | documented out-of-tree SDK trial, disposable worktree | unmeasured: compatibility pending | unmeasured: collection pending |
| Cortex-M7 compile count | compile-only both FPUs, pinned toolchain | unmeasured: collection pending | unmeasured: collection pending |
| UI drag at 200 modules | same frame-p95 harness if compatible | unmeasured: compatibility pending | unmeasured: collection pending |
| Bundled renderable | golden render method, own bundled inventories; list fixture IDs | unmeasured: collection pending | unmeasured: collection pending |
| Engine executable / module library .text | file bytes and size -A; record artifact identity | unmeasured: collection pending | unmeasured: collection pending |

No result or acceptance claim. Draft-ahead under #589; release follows #567.
