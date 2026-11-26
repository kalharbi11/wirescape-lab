<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Wirescape native graph limits — source and null-sink probe

- **Source lab commit:** `bb469122f06a783ae95d6ed916348e10fce98f66` (base of the L10 work branch).
- **Source inspection date:** 2026-11-14 (New York).
- **Runtime target:** native `wirescape-engine` with `--null-audio --rate 48000 --block 256`, without `--confirm-audio` or `--confirm-midi`.
- **Probe command:** `python bench/device/probe_limits.py --engine <built Release wirescape-engine path>`.
- **Test payload:** `loadGraph` with the N=16 scaling graph created by `scaling_patch(16, enforce_graph_limit=False)`: 96 modules, 95 connections, stereo outputs on channels 0 and 1.
- **Source-defined refusal:** `ok:false`, `code:"limit"`, `message:"Graph capacity exceeded"`; request correlation key `re:"limit-n16"`. The `session` token is process-specific. The separate 129-connection probe uses `re:"limit-edges"` and the same refusal.
- **Runtime observations:** recorded by `bench/device/results/limits/<date>/analysis.json` in the device-free CI workflow. The commands and replies are retained in the workflow artifact, not in this source-limit inventory.

| Constraint | Value | Source location |
|---|---:|---|
| Graph modules / native nodes | 64 maximum | `native/sidecar/session.cpp:609`; `native/document/runtime_patch.cpp:38` |
| Graph connections / cables | 128 maximum | `native/sidecar/session.cpp:609`; `native/document/runtime_patch.cpp:38` |
| Runtime output channels | 16; bus index 0–15 | `native/sidecar/session.cpp:668`; `native/document/runtime_patch.cpp:44,78` |
| Event-queue configuration | 2,048 events | `native/sidecar/session.cpp:262-264` and `native/include/wirescape/engine.h:23-27` (`ws_engine_config.max_events`) |
| Maximum queued entries examined per render call | 256 | `native/include/wirescape/engine.h:63-65` |
| Pending protocol commands | 256 | `native/sidecar/protocol.h:15`; `docs/specs/ENGINE_PROTOCOL.md:18-21` |
| JSON protocol line / native patch size | 2,097,152 UTF-8 bytes | `native/sidecar/protocol.h:15`; `native/document/runtime_patch.h:6`; `docs/specs/ENGINE_PROTOCOL.md:17` |
| JSON nesting depth | 64 | `native/document/runtime_patch.cpp:32`; `docs/specs/ENGINE_PROTOCOL.md:17` |
| OSC input routes per patch | 32 | `native/sidecar/session.cpp:624` |

The N=16 graph requires 96 modules because each voice contains five modules, the summing tree contains 15 mixers and the graph contains one output module: `5*16 + 15 + 1 = 96`. The native 64-module limit is reached before DSP load is measured. N=8 uses 48 modules and 47 connections. This file records a graph capacity boundary, not a CPU or audible-dropout threshold.

## Delay v2 state save capacity

- **Source:** lab commit [`8c9bb10`](https://github.com/kalharbi11/wirescape-lab/commit/8c9bb10d9eb8acf616395404c26ed0c3964e19d2), 2026-11-25 ET. Source inspection on Windows. The [Architect review](https://github.com/kalharbi11/wirescape-lab/pull/539#issuecomment-7157010908) cites the hosted device-off capacity preflight test.
- **Capacity row:** `modules/delay/dsp.h` sets a 1,048,576-byte cap. A v2 save uses `144 + 8 × size` bytes, where `size = ceil(2 × sample_rate_hz) + 8`. The largest fitting ring size is 131,054 frames, corresponding to 65,523 Hz. Above that rate, including 88.2 and 96 kHz, the save preflight returns `WS2_CAPACITY` before writing the payload.
- **Follow-up from review L1:** characterize high-rate Delay state in the stopped-graph replacement path. The snapshot uses `old.save_state(id)` at [`host/sidecar/session.cpp:518`](https://github.com/kalharbi11/wirescape-lab/blob/8c9bb10d9eb8acf616395404c26ed0c3964e19d2/host/sidecar/session.cpp#L518).

The native `noteOn`/`noteOff` and `setParam` paths report `busy` on event-queue failure (`native/sidecar/session.cpp:1075-1078,1099-1100`); successful live-event command acknowledgements establish queue acceptance, not completed rendering (`docs/specs/ENGINE_PROTOCOL.md:69-104`).
