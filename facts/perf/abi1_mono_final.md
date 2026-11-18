<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Final S3 ABI1 reference measurements

Source date: 2026-11-17 ET. Recorded by gpt-builder4 in a cloud workspace through GitHub artifact downloads and Python zipfile/json/hashlib inspection; no audio/MIDI devices or LAN.

S3 reviewed head: `309bf8851008976070b899768db35eb1e500a6b1`; merged as `b87f8817de34818758c43d32b176acbc223dc038`. Q19 point 3 retires the ABI1 reference row in S4. These are the final actual S3 values; this file does not label the retired row measured on S4 or count it as a surviving comparison.

## Instruction counts

Run: [44028971378](https://github.com/kalharbi11/wirescape-lab/actions/runs/44028971378). Callgrind two-length difference, 10/30 blocks of 256 frames at 48 kHz. Base `cec70d7c6ee3cfe144c9525bba6ce7230048ac9c`; head is the reviewed source above. Ir/block is `(second total - first total) / 20`.

| Platform | Revision | Ir/block | Raw totals |
|---|---|---:|---|
| Linux aarch64 | base | 79168.35 | [2660365, 4243732] |
| Linux aarch64 | head | 79168.35 | [2659093, 4242460] |
| Linux x86_64 | base | 87889.65 | [3128857, 4886650] |
| Linux x86_64 | head | 87889.65 | [3125013, 4882806] |

## Benchmark timings

Run: [44028971187](https://github.com/kalharbi11/wirescape-lab/actions/runs/44028971187). The artifact records GitHub synthetic checkout `305930893dde53d47debde57fe0224c019bf649b`, whose second parent is the reviewed S3 head. PR159 documents the source-blob equality for benchmark/engine/build/validator paths and the intervening docs/facts/CI-only difference. This checkout pin is preserved rather than relabelled as a source-head execution.

The real standalone ABI1 engine measured `abi1_mono`; it did not call the removed Engine ABI1 shim. 48 kHz; 256 warmup blocks; 5 repetitions of 800 measured blocks. `mean_ns` is the median of the five repetition means, as emitted by the benchmark. The following values are copied from the actual artifact rows without rounding.

| Hosted platform | Block frames | mean_ns | p99_ns | worst_ns | Five repetition means, ns |
|---|---:|---:|---:|---:|---|
| Windows AMD64 | 64 | 2627.75 | 4000.0 | 27200.0 | [2627.75, 2630.75, 2624.75, 2622.25, 3160.5] |
| Windows AMD64 | 128 | 5198.0 | 7400.0 | 70300.0 | [5206.25, 5198.0, 5322.375, 5180.0, 5175.75] |
| Windows AMD64 | 256 | 10291.125 | 14700.0 | 47900.0 | [10260.875, 10245.5, 10334.75, 10291.125, 10307.625] |
| Linux x86_64 | 64 | 2579.33 | 2644.0 | 12709.0 | [2596.968, 2579.33, 2578.936, 2573.588, 2584.859] |
| Linux x86_64 | 128 | 5087.594 | 5198.0 | 14922.0 | [5081.629, 5079.701, 5089.151, 5089.234, 5087.594] |
| Linux x86_64 | 256 | 10092.504 | 16154.0 | 26810.0 | [10092.311, 10088.885, 10092.504, 10216.31, 10104.237] |
| Linux aarch64 | 64 | 2837.049 | 2952.0 | 6591.0 | [2842.926, 2840.881, 2837.049, 2836.963, 2835.497] |
| Linux aarch64 | 128 | 5563.604 | 5752.0 | 15127.0 | [5567.735, 5563.604, 5546.667, 5554.602, 5574.746] |
| Linux aarch64 | 256 | 10932.446 | 12527.0 | 22294.0 | [10939.228, 10944.256, 10932.446, 10922.819, 10920.965] |

## Artifact integrity and member hashes

Downloaded ZIP SHA-256 values match the GitHub artifact digest. Numeric JSON-member SHA-256 values were computed after opening each ZIP.

| Artifact ID | ZIP SHA-256 |
|---|---|
| 14304681604 | `55f6877c315eb7b465da3ffcc25c3114f09530ec5aac45f44992ac071268dab9` |
| 14305465508 | `685b627d863cc473a31c1b84f4c00d6517e4c59a20cfbcc01ffc6b85dda4b68d` |
| 14304872068 | `7fb29216198ec66ace4fab2e063d36c9691527fd4d8ea03debd11c7927189f42` |
| 14303549646 | `05c78242bf3059f1d7bfdcf75244db984c21862bb207219e307ec7a2de30ce2e` |
| 14303734478 | `f8ab677a46b765eada330457babe02d16684b0678c6e17f552c25b6b24036d97` |

| Artifact ID | Member | SHA-256 |
|---|---|---|
| 14304681604 | perf/engine_cpu.json | `e1416d955eed267c4a8343c5c99c1eade19b70354290862e32e903533a23e725` |
| 14305465508 | base-instructions.json | `c4cf9b499b97fd020aaac6452675bc61f09b068ad3318bfc59c4aec0e48d6050` |
| 14305465508 | head-instructions.json | `4bd972327f0fa0ea4e756f6cc79559cbebbe30fedee64b24c9e6cdb2ac4f373d` |
| 14304872068 | base-instructions.json | `d36b857ef9d0e995f46242284aec17c1c420fe7d0c006fd81242f60452a84a48` |
| 14304872068 | head-instructions.json | `3d2b1c3961e3bce60ff5cd1327fbd03c3b4d66bd14a44a13cea8d09f0cb7b4b7` |
| 14303549646 | perf/engine_cpu.json | `ba3b6e57e9539805bde6240f16c7fd37c44ea571c25e87fe1dcf3aedaf2897b3` |
| 14303734478 | perf/engine_cpu.json | `4444fd64fe7ee61ad4592cd61c1a3581ce979380f70d63e94127412c8f2d9f5f` |

Windows has no Callgrind measurement in this run; its paired artifact supplies generated link evidence only. This file makes no Windows instruction-count claim. Historical committed baselines remain unchanged. S4 retains the other 96 named IDs and the unchanged +1% measured-row limit; the two Chord unavailable rows remain unavailable, not measured passes.

## S4 Qt-free ABI1 96,000-sample capture (pre-deletion)

Read-only device-free hosted release build on Linux x64, 2026-11-17 ET: [M1 paired run 44134064502](https://github.com/kalharbi11/wirescape-lab/actions/runs/44134064502), job `134218653099`, artifact `14352740696` (`m1-stage-evidence-linux-x64`). This is the exact existing Qt-free `serialized_demo_equivalence` ABI1 render, not the 16,384-frame T1.1 shim reference. Test/capture source commit `fd0b9058e3515ea95e75c0a16a695fdf52b7e129`; comparison base `be928a112d3280a04e2cdce229df8e0315c1dd6c`. The artifact's `provenance.txt` records both actual checkouts matching those pins, machine `linux-x64`, runner `Linux/X64`, CMake 4.2.3, Python 3.12.16 and `-g` compilation flags. That hosted job concluded success.

The artifact archive is 290,548 bytes and has SHA-256 `deb5cf60646fc094b33f0fd05318908365ea4d0c96b3f6d8beb11dd3418cf6de`, matching GitHub's artifact digest. Member `qt_free_saved_v2_abi1_48000_128_96000.f32le`: **384,000 bytes**, exactly **96,000** IEEE 754 binary32 little-endian sample words from 750 × 128 ABI1 blocks at 48 kHz. The raw SHA-256 is `485456df74522320047a4ae9361e5de52042c15079ccb4549982fbe41d887419`, agreeing with the archive's `.sha256` sidecar. The sample stream contains 96,000 finite words, of which 73,152 are nonzero; maximum absolute sample is 0.06200799718499184. A raw Git blob made from those bytes has SHA-1 `4dc06c72035a30979ea84beacc7664999bce77b6` (precomputed from the bytes, **not** a claim of a published GitHub blob).

The same Linux x64 paired artifact reports 97 expected historical IDs, 95 measured and two Chord paired-unavailable exceptions, with no failures; those are **capture-head S3-reference** measurements, not S4 retirement evidence. The mandatory surviving-96-ID verification remains outstanding. The raw PCM member was extracted and hashed from the actual published artifact. Its repository fixture blob, manifest entry, frozen-reader comparison and S4 deletion are **not yet committed** as of this facts commit.


## S4 deleted ABI1-only test inventory and replacements

- `native/tests/engine_tests.cpp`: exercised removed `ws_engine` lifecycle/render; surviving `abi2_engine_tests` and the frozen Qt-free saved-document comparison enforce ABI2 behavior.
- `native/tests/module_tests.cpp`: ABI1 module v1 entry/build and legacy engine target only; `abi2_module_tests` and native `modules2/` cases survive.
- `native/tests/scale_offset_tests.cpp`: ABI1 scalar source/entry and legacy engine target only; `abi2_scale_offset_tests` and frozen utility references survive.
- `native/tests/lfo_tests.cpp`: ABI1 oscillator/LFO source and old engine target only; ABI2 module and runtime tests survive.
- `native/tests/returned_filter_stress.cpp`: legacy VCF/ladder target only; `abi2_returned_filter_stress` stays and uses committed frozen references.
- `native/modules/clock/tests.cpp`: ABI1 clock shared-module test; retained `native/modules2/clock/tests.cpp` and frozen clock fixtures.
- `native/modules/function_envelope/tests.cpp`: ABI1 envelope shared-module test; retained `native/modules2/function_envelope/tests.cpp` and frozen utility fixtures.
- `native/modules/ladder/tests.cpp`: ABI1 ladder shared-module test; retained `native/modules2/ladder/tests.cpp` and frozen utility fixtures.
- `native/modules/noise/tests.cpp`: ABI1 noise shared-module test; retained `native/modules2/noise/tests.cpp` and frozen utility fixtures.
- `native/modules/slew/tests.cpp`: ABI1 slew shared-module test; retained `native/modules2/slew/tests.cpp` and frozen utility fixtures.
- `native/modules/vcf/tests.cpp`: ABI1 VCF shared-module test; retained `native/modules2/vcf/tests.cpp` and frozen module fixtures.
- `tools/capture/test_capture.py` `EngineTests` (4): required deleted executable ABI1 reference renderer; the 96,000-sample Qt-free frozen comparison and surviving ABI2 tests cover the migrated testable seam.
- `tools/capture/test_capture.py` `RunnerTests` (16): mocked only removed manual/ABI1 capture CLI and transport implementation; the 11 synthetic offline `AnalysisTests` remain under `capture_offline_selftests`.
- `native/tools/capture/capture.cpp`: manual device endpoint executable, not a CTest or product target after S4; executable retired without executing devices.

Retained unchanged: `native/tests/golden_render.cpp` (AppEngine Golden), `native/tests/fixtures/` and its historic corpus/chunks, `native/tests2/frozen_reference.h`, and v1 file reader/header contracts for S5. `fixed/abi1_mono` is historical-only (no current measurement, numeric zero or pass); 96 surviving IDs including two explicitly unavailable Chord rows keep the same strict +1% threshold. Any comparison/Golden/fixture mismatch blocks acceptance; no hosted S4 green verdict is asserted by this inventory.

Signed: gpt-builder4, 2026-11-17
