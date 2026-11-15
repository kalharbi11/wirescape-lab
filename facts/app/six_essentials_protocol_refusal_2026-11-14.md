<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Six Essentials demo: protocol loadGraph refusal

Source lab commit: `7d3842dc783915cf31aaf43bca508ebdcefb8a48`; measurement date ET: 2026-11-14. Analysis date ET: 2026-11-15; code inspected at lab main `84bd0fe947aeba096b81039d973f1c60cf6dd4dc`. Method: examine committed `facts/app/ci-*/protocol.json`, the unchanged `native/examples/Six_Essentials_Demo.json`, and `native/sidecar/session.cpp:602-605`. All runs used `wirescape-engine --null-audio` with no audio/MIDI devices or LAN sockets.

| Machine | CPU / OS | `loadGraph` code | Acknowledged | Recorded duration |
| --- | --- | --- | --- | ---: |
| Hosted Linux x64 | Intel Xeon 6975P-C; Linux 7.0.0-1016-aws x86_64 | `invalid` | no | 0.468528 ms |
| Hosted Linux ARM64 | CPU `0xd49`; Linux 7.0.0-1017-azure aarch64 | `invalid` | no | 0.343875 ms |
| Hosted Windows x64 | AMD Family 25 Model 17 Stepping 1; Windows Server 2025 | `invalid` | no | 10.994 ms |

`native/examples/Six_Essentials_Demo.json:2-3` declares `format=wirescape.native.patch`, `version=1`. Its modules use the v1 `type` and numeric `values` keys, and it has `outputNode` (`native/examples/Six_Essentials_Demo.json:5-12`). The sidecar's `Session::execution` requires `version == 2` (`native/sidecar/session.cpp:602-604`) and v2 module `module` fields (`native/sidecar/session.cpp:610-625`). The separate offline document loader accepts either v1 or v2 (`native/document/runtime_patch.cpp:34-36`). No changes to the demo patch were made.
