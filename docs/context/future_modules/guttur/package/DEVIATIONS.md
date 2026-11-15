<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Deviations and improvements from the JavaScript reference

The JS source is a reference for **synthesis architecture and sonic identity**, not a requirement to reproduce its runtime bugs. These are deliberate changes or limitations, not silently applied algorithm substitutions.

1. **Removed scheduling subsystem (requested).** SCENES, GESTURES, layer patching, chant/crowd sequencer and percussion do not exist in the C++ API. All singer-group DSP is retained. There is no external `setScene`, `setLayer`, `setEvents`, or `transport` method.
2. **16-throat global budget (requested).** The original JS uses configurable maximum singer counts; this build allocates 16 fixed Singer DSP slots and up to 16 note-owner records. Group size remains 1–8. Requests exceeding 16 active throat slots steal older singer voices with a bounded 128-sample crossfade policy.
3. **Persistent control timing.** JS slices work into 128-sample chunks relative to the current `process()` call. C++ tracks absolute sample position, preserves unfinished control blocks, and is sample-equivalent across host callback partitions. This can change automation transition timing compared with JS.
4. **Delayed followers and note-off lifecycle.** A note-off does not silently lose or leak singers that have not yet reached their delayed onset. Pending follower starts/releases are tracked explicitly and retired deterministically. This produces a different decay and tail from the current JS reference in some presets. This is why whole-render RMS can differ by ~2 dB even when sustained RMS agrees closely.
5. **Voice identity.** Added explicit opaque 64-bit note IDs, duplicate/stale identity handling, and bounded note tables. The Wirescape adapter maps its 32-bit event IDs and source identity into private handles.
6. **Runtime-safe allocation.** Persistent buffers, FFT scratch and DSP state are allocated in `prepare`, optionally through the Wirescape memory arena. The JS engine uses managed arrays/objects and is not subject to the C++ callback allocation contract.
7. **Deterministic random generators.** JS `Math.random` and process-global randomness are replaced by per-throat xorshift32 streams with a deterministic seed. `hash`/`h01` retain their 32-bit arithmetic. Randomized renders therefore should match in *statistics*, not in exact samples.
8. **Master/wet smoothing (enhancement).** Abrupt changes in master volume and reverb wet level now ramp over the 128-sample control quantum, limiting zipper clicks during automation. Initial preset settings are applied immediately. The glottal, tract and fixed preset values remain unchanged.
9. **Realtime CPU optimization (enhancement).** Sample-rate-dependent exponential envelope/limiter coefficients and constant grit gains are calculated once during preparation or at control ticks, not thousands of times per audio block. This changes no intentional synthesis behavior; floating-point roundoff can differ marginally.
10. **Portable aligned allocation.** Standalone Windows MSVC builds use `_aligned_malloc`/`_aligned_free` where the C++17 `std::aligned_alloc` implementation is missing. The Wirescape path uses the host arena.
11. **Patch state vs continuation.** State serialization stores parameters, seed and preset trim, not complete filter/delay/voice history. Loading resets audio state. This makes a saved patch repeatable but does not resume a note midway through its physical waveform.
12. **Telemetry.** A non-blocking live struct is available only to the render owner. Wirescape's existing ABI2 does not provide arbitrary structured internal-voice telemetry; no cross-thread telemetry hook has been invented.

## Known open issues

- A fully built, linked, and CI-tested module inside the target `kalharbi11/wirescape` checkout has **not** been produced by this standalone package test; the distributed adapter passes a local ABI-compatible callback shim, not complete engine integration.
- No Raspberry Pi 5/ARM64 CPU evidence, Windows compiler run or multihost audio callback soak has been performed. The supplied local benchmark is a desktop/container indication only.
- Filter coefficient changes (`body`, `air`, room geometry) and the nonlinear `gritAfter` mode switch may still create audible transitions under extreme automation. They need automated transient characterization and listening tests before promising click-free behavior for every parameter change.
- No owner-provided `render.js` or `metrics.py` appeared in the uploaded GUTTUR ZIP. JS/C++ RMS, residual and correlation are available, but a claim of full Praat or original metric-harness parity would be unfounded.
- The owner must select and document a licence before sharing/distributing under a specific licence, and must resolve the in-repository GPL code/provenance expectations before merging into Wirescape.
