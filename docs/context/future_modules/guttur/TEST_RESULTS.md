<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR C++ verification report

**Build type:** standalone Linux x86-64 C++17. The module adapter is an additive Wirescape ABI2 integration draft, not a merged/tested Wirescape module.

## Verified checks

- Standalone CMake + Ninja build: PASS.
- `ctest --test-dir build --output-on-failure`: PASS. Tests include sample rates 44.1/48/96 kHz, finite/ceiling-bounded outputs, deterministic reset, versioned state validation, stale 64-bit note IDs, maximum 16 note records, delayed-release cleanup, and zero `operator new` calls inside `process`.
- Block-size exact equality (same note and parameter timeline): PASS for **1 / 17 / 128 / 512 / 4096** frames, including parameter changes and note events between control ticks.
- AddressSanitizer + UndefinedBehaviorSanitizer standalone tests: PASS.
- Wirescape adapter compiled and basic `ws2_descriptor` callback smoke-tested against a local ABI-compatible shim: PASS, including stereo outputs and fixed latency. **Not a substitute for a full in-repository build/CI**.

## JavaScript reference comparison

Run `node tools/render_js_reference.js --output-dir renders_js`, `./build/guttur_offline --output-dir renders_cpp`, then `python tools/compare_renders.py renders_cpp renders_js`.

The original uploaded ZIP contained `guttur-worklet.js` and `index.html`; it did **not** contain the requested separate `render.js`/`metrics.py`. The accompanying tools reproduce these independently authored 2-second scenarios and compute RMS/correlation using PCM16 WAV. They **do not** compute LUFS or Praat jitter/shimmer/HNR.

| Case | JS RMS | C++ RMS | Sustain Δ dB | Whole Δ dB | Sustain correlation |
|---|---:|---:|---:|---:|---:|
| plain | 0.03445 | 0.03445 | +0.00 | +0.00 | 1.000 |
| clean | 0.04869 | 0.03869 | +0.04 | -2.00 | 0.971 |
| weathered | 0.04268 | 0.03858 | +0.43 | -0.88 | 0.837 |
| raspy | 0.04418 | 0.03448 | -0.20 | -2.15 | 0.730 |
| chant_voice | 0.05329 | 0.04188 | -0.26 | -2.09 | 0.800 |
| growl | 0.04431 | 0.03381 | -0.52 | -2.35 | 0.691 |
| fry | 0.04373 | 0.03381 | -0.10 | -2.23 | 0.383 |
| ayn | 0.04679 | 0.03550 | +0.11 | -2.40 | 0.820 |
| ring | 0.05712 | 0.04559 | -0.66 | -1.96 | 0.840 |
| whisper | 0.03183 | 0.02537 | +0.17 | -1.97 | 0.460 |
| small | 0.05473 | 0.04380 | -0.15 | -1.93 | 0.952 |
| kargyraa | 0.03990 | 0.03139 | +0.35 | -2.08 | 0.816 |
| ensemble16 | 0.05908 | 0.04312 | -0.29 | -2.74 | 0.918 |

Plain deterministic residual: **-67.03 dB** relative to reference (sustain).
RMS dB differences are not LUFS or Praat measurements.

**Interpretation:** The plain, randomized-controls-disabled case has a measured **−67.03 dB residual**, which is better than the original −60 dB parity target. The other cases differ because the C++ note-release/voice-lifecycle policy is intentionally corrected and random generation is deterministic but not bit-identical. Whole-render RMS is often ~2 dB below JS because of release-tail differences; this is not evidence that the sustained vocal tone is 2 dB quieter. All numbers are from the paired two-second offline WAV tests, **not** perceptual preference measurements.

## Local CPU measurement (not Pi evidence)

Command: `./build/guttur_benchmark 3000`, x86-64 optimized build, 48 kHz, 128 frames, one and 16 simultaneously active rough vocal throats. Two separate runs are not directly comparable because the virtualized host introduces timing spikes.

| Throats | Median block | P95 | Worst observed | Block duration |
|---:|---:|---:|---:|---:|
| 1 | 26.23 µs | 30.20 µs | 348.32 µs | 2,666.67 µs |
| 16 | 195.86 µs | 241.07 µs | 2,261.14 µs | 2,666.67 µs |

The observed 16-throat worst case is **under one full audio period but above the 50%-period safety target (1,333 µs)**. This result is not a clean Wirescape Pi acceptance and is sensitive to process scheduling; an actual Pi 5, two-module test and priority-controlled soak are still required. `wirescape` has not been modified.

## Still unverified

- Full native ABI2 host/module integration build, deployment and packaging inside the user's Wirescape repository.
- Raspberry Pi 5/ARM64 realtime headroom, Windows/MSVC compile and sanitizers on those targets.
- End-to-end comparison with the absent owner `metrics.py`, including Praat jitter/shimmer/HNR, LUFS and the original aliasing/intermodulation scoring scripts.
- Listening tests of high-pitch vowels, aggressive growl/fry, automation mode switches and sustained 16-throat scenes.

No high-confidence claims of parity in these areas are made.
