<!-- SPDX-License-Identifier: GPL-3.0-only -->
# T1.1: ABI1 reference capture for frozen ABI2 comparisons

Issue [#67](https://github.com/kalharbi11/wirescape-lab/issues/67) is class B.
This directory contains test-only capture/fixture-validation helpers. It does
not modify the engine or change the original live ABI1 comparison assertions.

## Source comparisons inventoried

| Test / target | ABI1 reference input | Compared output | Original check |
|---|---|---|---|
| `abi2_integration_tests` | ABI1 `ws_engine` with 8 legacy nodes, steady and 4 scheduled changes (777, 2011, 3245, 4479 frames), 48 kHz, 256 frames/block | 16,384 binary32 mono samples per case; engine2's ABI1 shim as actual | Complete bitwise `memcmp==0`, no tolerance |
| `abi2_module_tests` | 13 legacy module descriptors, 44.1/48/96 kHz, blocks 1/17/256, 2,048 frames per case, one channel | Every output port/sample from the legacy module versus ABI2 `DspFixture` | Modules vco/lfo/vcf/adsr/vca max absolute difference ≤1e-6; remaining 8 exactly 0 |
| `abi2_{clock,function_envelope,ladder,mixer,noise,output,scale_offset,slew}_tests` | Legacy module per channel, 3 rates × 3 channel counts × 3 blocks × 4 patterns × 2 resets, 1,024 frames per reset | Every original exact-equality output from ABI1 versus ABI2 (noise excluded for voices beyond channel 0) | `actual == legacy` at every compared sample; descriptor IDs, bounds and counts also exact |
| `abi2_returned_filter_stress` | ABI1-shaped descriptor bridge backed by ABI2 ladder; unchanged `native/tests/returned_filter_stress.cpp` cases | Impulse/modulation stress on ABI2 returned-filter adapter | Original stress assertions (not one of the module-loop sample comparators) |

The same test files independently check polyphonic stealing and release, frame-
accurate event timing, pitch, state save/load refusal/roundtrip, deterministic
reset, transport, coefficient updates, finite values, VCA signed-zero and exact
scalar behavior, zero allocations during DSP processing and unwinding. These
unrelated tests remain active and are **not** replaced by fixture hashes.

**Current build dependencies:** the original `abi2_integration_tests` CMake
target directly links `wirescape_engine`; `abi2_returned_filter_stress` also
links it. The ordinary module and utility targets dynamically load ABI1 module
descriptors but do not link that engine library. Separate
`abi2_benchmark`/`abi2_cost_probe` targets also link the ABI1 engine, and
remain outside the T1.1 comparison-target scope.

## Capture protocol (temporary)

During CI Release builds, `abi2_reference_capture` invokes the *passing live
comparison tests* with the opt-in `ABI1_REF_CAPTURE_DIR` test environment set.
The legacy output words are serialized explicitly in little-endian order;
the source tests' exact comparison/tolerance checks still execute. No
device-facing paths are used.

`freeze.py` requires 983 case files: 2 integration, 117 module, 864 utility.
It verifies case names, alignment and lengths, then emits machine-scoped
`abi1_<machine>_<suite>_<group>.json` candidates. Each candidate records
the Git source commit actually checked out, CPU, OS, compiler ID/version,
release build flags, rate/channel/block/pattern metadata, exact source byte
count, SHA-256, and `zlib9+b64` IEEE binary32 little-endian content.
The Golden same-runner workflow retains candidates as `golden-diagnostics`
JSON without retaining large WAVs; the golden build prints machine-scoped
`ABI1_FREEZE_BEGIN/CHUNK/END` records for promotion after verification.

`unpack.py` verifies the committed source SHA and every per-case digest
before writing build-local binary32 words. Missing, truncated, mixed-machine,
duplicate or corrupted data are fatal. The pack/unpack synthetic tests are
registered as a device-free CTest case.

## Readiness

These are **capture candidates**, not accepted frozen fixture comparisons,
until CI has provided real, per-platform data and the tests are converted to
load that frozen data. The final T1.1 tests must run with their reference side
not linked to or calling the ABI1 engine; retain all original tolerances and
unrelated assertions. No ABI1 engine or module deletion is authorized.
Only Fable merges this class B task.
