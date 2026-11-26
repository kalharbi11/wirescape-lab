<!-- SPDX-License-Identifier: GPL-3.0-only -->
# MM-f (#644): 64 / 128 node measurement protocol (draft)

Status: **unmeasured**. This is draft-ahead preparation while #604 awaits its gates; not a completed Result.

## Workload and boundaries

- Fixed 48 kHz, 128 frames, two rendered output channels; same sounding VCO→Output base as `tests/fixtures/patch_shapes/no-config.json`, same seed, no device, injected events, sockets or LAN.
- Pad to exactly 64 and 128 authored/prepared nodes. Use idle MIDI In feeders, CC-to-CV converters (event cable from a feeder), OSC In without a host service, and Macro pages after the real native descriptor is promoted. Record exact counts by type, cable count and fixture/hash. Do not substitute `ports.macro_oscillator` for `essentials.macro`.
- Source inspection on main during 2026-11-26 draft: `host/document/runtime_patch.cpp::load_runtime_patch` also enforces `modules.size()<=64`; a larger `engine2::Config::max_nodes` alone cannot load 128. The sidecar cap and the loader cap are distinct. Bench-only test override permitted by #644: use a generated copy of the loader in a build directory with the single graph-size bound changed for the probe, assert the exact replacement occurs once, link unchanged production AppEngine and modules. Do not change either product cap. Keep the same override translation unit for both rows; use explicit max_nodes equal to each row. Preserve all other load/config/connection checks. Verify actual loaded nodes and finite, sounding base output; refuse to report an incomplete graph as measured.
- Build a dedicated benchmark executable from a bench-only CMake project include/deferred target, using the existing native configuration and product libraries; no edits to shared native CMake or workflows. Validate the build and the cap distinction before accepting data. Hosted execution can use a dedicated supported CTest script under bench (targeted diagnostics), or the lead's authorized hosted execution if the existing runner cannot invoke it. No evidence from an unexecuted script.
- Warm up 375 blocks, then 3,750 measured blocks (10 s of logical audio); three fresh processes per row on each architecture, no clock or output except timing the actual render call and collecting a fixed vector of samples. Report each mean and worst in µs, as well as configured period (2666.666… µs). Hosted timings are diagnostic, not realtime or Pi performance.
- Capture process resident memory before graph creation, after graph prepare/warm-up, and process peak RSS (Linux /proc/self/status and getrusage; units explicit); report whole-process memory, not engine-only allocations. Separate process per repetition, record machine, OS, architecture, compiler, build type, source SHA, date, workload hash and command/run link.
- `essentials.macro` absent from current native catalogue; a separately labelled available-module-only experiment can characterize existing idle sources, but cannot satisfy full four-kind workload. Full rows stay unmeasured until actual Macro promotion. Do not fake a descriptor or use Studio FakeEngine for native costs.
- Pi only from owner-provided A31 zip; do not run devices or write to the private Pi repo.

## Evidence inventory (no measurement yet)

| Machine | Nodes | Workload | RSS | Mean / worst block | Status |
|---|---:|---|---|---|---|
| Hosted linux-x64 | 64 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Hosted linux-x64 | 128 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Hosted linux-arm64 | 64 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Hosted linux-arm64 | 128 | Full four-kind | unmeasured | unmeasured | Macro absent |
| Owner Pi | 64 | Full four-kind | unmeasured | unmeasured | Owner zip unavailable |
| Owner Pi | 128 | Full four-kind | unmeasured | unmeasured | Owner zip unavailable |

Signed: gpt-builder3, 2026-11-26
