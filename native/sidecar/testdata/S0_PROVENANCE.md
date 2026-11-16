<!-- SPDX-License-Identifier: GPL-3.0-only -->
# M1 r2 S0 — actual sidecar snapshot provenance

**Source capture:** `facts/device/results/pi5/2026-11-14-cd9a6a5-device-off/compare-null/engine-protocol.ndjson`,
lab commit `cd9a6a5d447bf6c078df0c9b9f9f5df869e71ff2`, 2026-11-14 ET,
Linux ARM64 Pi 5, **null-sink process / no physical audio or MIDI device**.
Source `manifest.json`: `engine_hello_validated: true`, `mode: null_sink_process`,
`measured: false`. All captured message fields are actual sidecar protocol output,
not a synthetic catalogue. The snapshot source precedes M1 S0; comparing against
the current implementation is intended to detect changes to I7, not update expected bytes.

| Test fixture | Exact source, byte selection, test control |
| --- | --- |
| `s0_catalogue.ndjson` | Original first-line `hello.catalogue` JSON *raw byte range* from the full on-wire `hello`, plus terminal newline; 34 complete modules, ports and parameters. No key sorting, rounding, filtering or object reconstruction. The production `nlohmann::json::dump()` serializer must reproduce those bytes exactly. |
| `s0_status.ndjson` | Original **entire** first `status` wire message (line 4); the **only** reference change is replacing its random `session` value `2051839750-298415007150` with the explicitly fixed test-only session token `s0-fixture-session`. No field is stripped or normalized. Every other byte, including `gen`, full audio/MIDI/OSC status and numeric spellings, is retained verbatim. |
| `s0_setparam_request.ndjson` | Pinned test-created strict protocol request `setParam(moduleId=9,paramId=frequency,value=440)` after adding the native `essentials.vco` node at id 9. This is a deterministic test input, not claimed to be a historical Pi capture. |
| `s0_setparam_reply.ndjson` | Pinned complete `Session::reply` serialization for the preceding real control request at generation 1, with the same fixed test-only session token. Initially derived from `native/sidecar/session.cpp::Session::reply`; only a successful hosted `abi2_sidecar_snapshot_tests` verifies it as *actual emitted serializer bytes*. No production device/protocol path is altered. |

**Test-only determinism:** `native/CMakeLists.txt` generates a separate
`s0_snapshot_session.cpp` into the **build directory** from the current
`native/sidecar/session.cpp`. The sole behavioral substitution is the constructor's
`token_ = std::to_string(random()) + "-" + std::to_string(app_engine_clock_ns());`
to `token_ = "s0-fixture-session";`; the test-only binary also pins
`WIRESCAPE_ENGINE_SHA` to `s0-fixture-build`. Its relative include path
is adjusted for the generated file's binary-directory location. Neither the
product sidecar nor its parser, JSON encoder, catalogue, IDs or protocol changes.
There is **no output normalization**: `snapshot_tests.cpp` compares literal
`Json::dump() + "\\n"` from the real `Session` implementation to every
fixture byte. The actual sidecar transport uses that same `Json::dump()`.
Snapshot mismatches fail; no test automatically regenerates expected data.

**Device policy:** tests run at `--null-audio` equivalent with audio,
MIDI and LAN disabled; no hardware, OSC network bind or localhost client is
needed. No physical/timestamp measurements are inferred. The complete
status message is sampled before starting the null sink to keep input state
deterministic; the parameter round trip starts only the in-process null sink.
The status case, not the nondeterministic telemetry `time` field, satisfies
S0's permitted "one meter/status message" alternative.

**Future I7/I8 review:** changing any byte requires a review of the exact
protocol/catalogue difference and source provenance. The historical capture is
not a golden oracle for performance or musical sound; it is a byte tripwire.
JSON/NDJSON files deliberately have no embedded license comment because
adding one would corrupt the original protocol bytes; this provenance file
carries their GPL-3.0-only SPDX statement.

Signed: gpt-builder4, 2026-11-16
