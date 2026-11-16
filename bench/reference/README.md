<!-- SPDX-License-Identifier: GPL-3.0-only -->
# T1.1: Frozen actual ABI1 reference outputs for independent ABI2 comparisons

Issue [#67](https://github.com/kalharbi11/wirescape-lab/issues/67), M0 r2 R5, class B.
Source captures were produced by passing live ABI1-vs-ABI2 tests at
**`0aa468346ed1f3260b7efe8748ff181e22a64674`**, not by the later fixture
commits. Their actual numeric outputs were compared and source-hashed on three
GitHub-hosted architectures. The legacy ABI1 engine and module source trees
remain intact; this task does not implement T1.2.

## Comparison matrix and preserved assertions

| Comparison target | Frozen capture | Unchanged strength |
| --- | --- | --- |
| `abi2_integration_tests` | 2 steady/scripted 16,384-frame mono renders, 48 kHz, 256/block; actual ABI1 engine 8-node graph | Entire raw `memcmp==0` against current engine2 ABI1-module shim, plus untouched polyphony, pitch, event, release, stereo, and allocations |
| `abi2_module_tests` | 13 original legacy modules × 3 rates × 3 blocks × 2,048 samples (117 cases) | Modules 0–4 retain `worst<=1e-6`; other eight retain `worst==0`. Matrix/reset, scalar VCA, LFO phase, coefficient and noallocation assertions unchanged |
| Eight `abi2_*_tests` utility ports | 8 modules × 3 rates × 3 channel counts × 3 blocks × 4 impulse/sine/sweep/unpatched patterns (864 cases), 2 reset passes | Each formerly compared sample now checks `actual==frozen` (noise poly-channel exception retained), with unchanged descriptor ID/bounds, reset/state, noalloc and finite/extreme tests |
| `abi2_returned_filter_stress` | Unchanged impulse and modulation/release test functions applied to the ABI2 ladder bridge | Original filter stress validations remain; its renamed legacy entrypoint is discarded by test-target-only linker section GC, not linked to ABI1 engine |

The noncomparative original assertions remain in the same test files. The
independent ABI1 library is **not** linked to the comparison executables.
A CMake configuration-time check recursively traverses `LINK_LIBRARIES` and
`INTERFACE_LINK_LIBRARIES` for all 11 comparison targets and fails if
`wirescape_engine` is reachable. Runtime engine2 compatibility testing
still uses ABI1 **module descriptors**, intentionally; T1.2 owns their removal.

## Frozen data and provenance

- `native/tests/fixtures/abi2/abi1_reference_hash_manifest.json`: 983
  source case names, SHA-256s, lengths, 8 descriptor snapshots, capture
  Git SHA, runner/compiler/OS/flags and original artifact IDs.
- `native/tests/fixtures/abi2/refs/`: 13 SPDX-header, base64-wrapped common
  LZMA corpus fragments and one Windows override fragment. The common
  source comprises 45,400,064 bytes before compression; Windows overrides
  carry only the **18** differing module block-256 cases (172,032 bytes).
  The same 983 captured reference streams matched on Linux x64 and ARM64;
  Windows differs in precisely those 18 cases, which are preserved as measured.
- `bench/reference/unpack.py`: verifies the LZMA SHA-256, uncompressed corpus
  SHA-256 and every one of 983 original-case SHA-256s; rejects missing,
  corrupt, unexpected or platform-mixed data; validates original descriptor
  hashes. Writes temporary `.f32le` and `.desc` under the build directory
  for native test readers.
- `native/tests2/frozen_reference.h`: decodes raw little-endian IEEE 754
  32-bit words and parses the recorded legacy descriptor IDs and binary32
  parameter bounds at test startup; it never calls ABI1 engine functions.
- `bench/reference/test_unpack.py` and `test_freeze.py`: synthetic
  integrity tests and full corpus hash/Windows-difference regression tests.
  No audio/MIDI hardware or LAN is used.

Capture sources and archival runs: GitHub Golden workflow
[43787767786](https://github.com/kalharbi11/wirescape-lab/actions/runs/43787767786),
actual source commit `0aa4683`, x64 artifact `14191511302`, ARM64
`14191288653`, Windows `14191418554`. Numeric source facts for earlier
independent Linux captures remain under `facts/dsp/abi1_t11_capture_*.json`;
they retain their own older measured source hashes, not the frozen corpus
commit. The fixture manifest, rather than those earlier summaries, identifies
the three inputs that generated the final committed data.

## Devices-off validation

The build's `abi2_frozen_reference_unpack` target verifies all source hashes
before comparing PCM; `abi2_reference_freezer_tests` exercises the integrity
loader and tamper refusal. The existing native CTest suites and the same-runner
Golden workflow are unchanged. Review must verify actual **exact-head** CI
and 24 unchanged golden renders per platform, plus printed
`T1.1 comparison links` dependency lists; no result is presumed by this
document.

Only the lead/Fable can merge within the accepted M0 contract. ABI1 engine,
library, legacy module and benchmark targets have not been deleted.
