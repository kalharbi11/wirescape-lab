<!-- SPDX-License-Identifier: GPL-3.0-only -->
# MM-f (#644): 64 / 128 node measurement protocol (draft)

Status: available-only hosted diagnostics executed; full four-kind workload and owner Pi rows remain **unmeasured**. #604 closed under A102. This record is not a product-cap decision or an exact-head gate.

## Workload and boundaries

- Fixed 48 kHz, 128 frames, two rendered output channels; same sounding VCO→Output base as `tests/fixtures/patch_shapes/no-config.json`, same seed, no device, injected events, sockets or LAN.
- Pad to exactly 64 and 128 authored/prepared nodes. Use idle MIDI In feeders, CC-to-CV converters (event cable from a feeder), OSC In without a host service, and Macro pages after the real native descriptor is promoted. Record exact counts by type, cable count and fixture/hash. Do not substitute `ports.macro_oscillator` for `essentials.macro`.
- Source inspection on main during 2026-11-26 draft: `host/document/runtime_patch.cpp::load_runtime_patch` also enforces `modules.size()<=64`; a larger `engine2::Config::max_nodes` alone cannot load 128. The sidecar cap and the loader cap are distinct. Bench-only test override permitted by #644: use a generated copy of the loader in a build directory with the single graph-size bound changed for the probe, assert the exact replacement occurs once, link unchanged production AppEngine and modules. Do not change either product cap. Keep the same override translation unit for both rows; use explicit max_nodes equal to each row. Preserve all other load/config/connection checks. Verify actual loaded nodes and finite, sounding base output; refuse to report an incomplete graph as measured.
- Build a dedicated benchmark executable from a bench-only CMake project include/deferred target, using the existing native configuration and product libraries; no edits to shared native CMake or workflows. Validate the build and the cap distinction before accepting data. Hosted execution can use a dedicated supported CTest script under bench (targeted diagnostics), or the lead's authorized hosted execution if the existing runner cannot invoke it. No evidence from an unexecuted script.
- Warm up 375 blocks, then 3,750 measured blocks (10 s of logical audio); three fresh processes per row on each architecture, no clock or output except timing the actual render call and collecting a fixed vector of samples. Report each mean and worst in µs, as well as configured period (2666.666… µs). Hosted timings are diagnostic, not realtime or Pi performance.
- Capture process resident memory before graph creation, after graph prepare/warm-up, and process peak RSS (Linux /proc/self/status and getrusage; units explicit); report whole-process memory, not engine-only allocations. Separate process per repetition, record machine, OS, architecture, compiler, build type, source SHA, date, workload hash and command/run link.
- `essentials.macro` absent from current native catalogue; a separately labelled available-module-only experiment can characterize existing idle sources, but cannot satisfy full four-kind workload. Full rows stay unmeasured until actual Macro promotion. Do not fake a descriptor or use Studio FakeEngine for native costs.
- Pi only from owner-provided A31 zip; do not run devices or write to the private Pi repo.

## Full-workload evidence inventory (unmeasured)

| Machine | Nodes | Workload | RSS | Mean / worst block | Status |
|---|---:|---|---|---|---|
| Hosted linux-x64 | 64 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Hosted linux-x64 | 128 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Hosted linux-arm64 | 64 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Hosted linux-arm64 | 128 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Owner Pi | 64 | Full four-kind | unmeasured | unmeasured | Owner zip unavailable |
| Owner Pi | 128 | Full four-kind | unmeasured | unmeasured | Owner zip unavailable |

Signed: gpt-builder3, 2026-11-26

## Available-only hosted diagnostic — 2026-11-26 ET

Tested source `06428a31486a3d7808dfbdd24cb88859a9cc3035`; [dev-run result](https://github.com/kalharbi11/wirescape-lab/pull/655#issuecomment-7206101906), [run 45913699023](https://github.com/kalharbi11/wirescape-lab/actions/runs/45913699023). Both platforms exited 0. Actual command: `ctest -S bench/mm_f/run.cmake -V`, Release, via `/dev-run cmd platform=both build=release target=wirescape_cli ... timeout=1200`. Hosted timings are diagnostics only; no real-time, Pi, product sidecar, or full four-kind claim.

- arm64: Linux 7.0.0-1017-azure aarch64; GCC 13.3.0; 2026-11-26 23:56:53 UTC.
- x64: Linux 7.0.0-1020-azure x86_64; GCC 15.2.0; 2026-11-26 23:57:09 UTC.
- CPU model not recorded by probe. No audio/MIDI device or OSC service; no injected events. Both rows use the same generated loader override, 48 kHz / 128 frames, nominal period 2666.667 µs, 375 warmup and 3750 timed blocks per fresh process.
- 64 nodes: 2 base + 20 MIDI In + 20 CC-to-CV + 22 OSC In; 21 cables; generated patch SHA256 `c056bfef5ea5a490826b564f168b2da1f4c8486a68099e8f04c5750f3e8eb8d9`.
- 128 nodes: 2 base + 42 MIDI In + 42 CC-to-CV + 42 OSC In; 43 cables; generated patch SHA256 `e53c500431729688be341d9388990165cae033bffc1bfa74136db784c0e3f1fc`.
- All twelve processes passed descriptor, finite sounding output (peak 1.0) and clean meter assertions; zero Macro nodes in each. The loader override is bench-only.

| Hosted runner | Nodes | Mean block range (µs) | Worst observed block (µs) | Warmed RSS range (KiB) |
|---|---:|---:|---:|---:|
| linux-arm64 | 64 | 243.754–245.380 | 320.165 | 23736–23752 |
| linux-arm64 | 128 | 499.369–501.001 | 649.705 | 37668–37672 |
| linux-x64 | 64 | 234.845–235.347 | 489.538 | 24712–24796 |
| linux-x64 | 128 | 460.136–474.396 | 561.183 | 38980–39016 |

Raw reported samples (unrounded means, no aggregation substitution):

| Runner | Nodes | Rep | Before RSS KiB | Warmed RSS KiB | getrusage maxrss KiB | Mean µs | Worst µs |
|---|---:|---:|---:|---:|---:|---:|---:|
| linux-arm64 | 64 | 1 | 3528 | 23744 | 23652 | 244.22156426666695 | 320.165 |
| linux-arm64 | 64 | 2 | 3532 | 23752 | 23652 | 245.3799250666669 | 313.478 |
| linux-arm64 | 64 | 3 | 3516 | 23736 | 23636 | 243.7535967999997 | 294.391 |
| linux-arm64 | 128 | 1 | 3596 | 37668 | 37604 | 501.00106453333336 | 649.705 |
| linux-arm64 | 128 | 2 | 3600 | 37672 | 37604 | 499.6165653333346 | 542.112 |
| linux-arm64 | 128 | 3 | 3600 | 37672 | 37604 | 499.3693664000003 | 553.631 |
| linux-x64 | 64 | 1 | 4032 | 24752 | 24632 | 234.84534773333286 | 293.36 |
| linux-x64 | 64 | 2 | 4112 | 24712 | 24528 | 235.11222853333348 | 489.538 |
| linux-x64 | 64 | 3 | 4012 | 24796 | 24736 | 235.3470986666664 | 270.477 |
| linux-x64 | 128 | 1 | 4080 | 38996 | 38880 | 462.5280631999996 | 543.669 |
| linux-x64 | 128 | 2 | 4088 | 39016 | 38896 | 474.3955567999993 | 561.183 |
| linux-x64 | 128 | 3 | 4116 | 38980 | 38924 | 460.13630613333265 | 510.727 |

Memory caveat: `ru_maxrss` is below sampled `VmRSS` in every repetition (different Linux accounting interfaces). Both are retained verbatim; do not interpret the former as a verified upper bound on the latter or as engine-only memory. CPU timing is offline render-call duration, not a scheduled audio callback or load/transition metric. No extrapolation to a different machine, module mix, or long soak.

Signed: gpt-builder3, 2026-11-26
