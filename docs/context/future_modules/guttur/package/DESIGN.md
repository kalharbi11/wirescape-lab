<!-- SPDX-License-Identifier: GPL-3.0-only -->
# GUTTUR C++ design and provenance

## Origin and non-goals

The original source is the user's `guttur-worklet.js`, provided in `GUTTUR(2).zip` (also copied unchanged to `reference/guttur-worklet.js`). The C++ implementation is a translation of the synthesis architecture, with localized corrections and performance optimizations. It **does not** reuse Throat v.2's synthesis algorithm or source code. No Pink Trombone, JUCE, VCV Rack, mutable global DSP cache, third-party FFT, or hardware code is included.

The chant/crowd sequencer, GESTURES, SCENES, per-layer patches, and rhythmic control transport were intentionally removed. The vocal texture preset named `chant` remains a synth timbre. No GUI is included.

## Signal path

```
Wirescape NOTE events / standalone noteOn
    -> 16-record note owner, bounded internal throat allocator
    -> up to 16 simultaneously active Singer DSP slots
          LF/Rd mipmapped pulse tables / closure decisions
          -> breath + rasp + flutter noise
          -> ten parallel M22-resonance SVFs, smoothed over 128 samples
          -> pitch-following HPF -> antiderivative tanh drive
          -> distance LPF, stereo pan, ITD, head shadow
    -> stereo dry + 8-line FDN and early reflections
    -> body/air shelves -> low-mid guard -> DC block
    -> optional post-grit -> 2.5 ms look-ahead limiter
    -> L/R float outputs (one Wirescape channel each)
```

`src/tables.cpp` builds the LF glottal waveform mipmaps and flow/harmonic tables with the embedded radix-2 FFT at preparation. `src/tube.cpp` precomputes a 34-section tract model over the 9×5×5×4 grid. Its M22 root solve is reused as a 10-resonance parallel filter bank. Wavetable levels suppress high harmonics based on the current period.

The core maintains exactly one 128-sample control clock. Wirescape callback sizes and note-event split points do not reset this clock. Parameters and coefficients are sampled at the internal tick; each DSP voice independently tracks its glottal-cycle closures. The Wirescape adapter passes note events at their sample offsets.

## Memory and realtime

A single `Engine::State` is prepared outside the audio thread. It owns all LF tables, tract grid, temporary FFT scratch, 16 Singer structs, room/limiter history, and bounded note tables. The Wirescape adapter provides a `ws::Setup::alloc`-backed allocation and advertises its required byte count through `memory_requirements`. No dynamic allocation, I/O or locks occur in `process`/note callback/reset.

The core is not thread-safe against arbitrary concurrent note/control operations. `setParam` is atomic. DSP note-on/off and `telemetry()` must be performed by the same render owner as `process`, or be handed over through a safe host-owned event/telemetry system.

Internal note groups and a shared stereo bus are an explicit choice. Wirescape's ABI2 limits **cable channels to 16**, which is independent of GUTTUR's **16 internal throat generators**. A single module instance emits one channel for each stereo-paired audio port. The existing Wirescape voice allocator is not used because independently stealing individual singers would change GUTTUR's leader/follower group behavior; this should be reviewed in the target repository.

## Fixed and dynamic latency

The limiter look-ahead is `round(0.0025 * sampleRate)` frames (110 at 44.1 kHz, 120 at 48 kHz, 240 at 96 kHz). The number of frames does not change during a render and is supplied through ABI2 `latency_frames()`.

## Numerical conventions

Sample rate: 44.1–96 kHz including 44.1, 48 and 96 kHz; parameter values and presets are taken from GUTTUR JS. The 17 Rd values, eight mip tables, and tube interpolation use double-precision equations with float storage where tables are large. Per-throat xorshift32 random streams are seeded deterministically. `hash` and `h01` implement the source's 32-bit integer arithmetic.

The final limiter ceiling is approximately −1 dBFS. GUTTUR is nonlinear and uses heavily time-varying noise/phonation; deterministic no-randomness renders are suitable for residual comparison, but randomized modes require listening and distributional tests.

## Port policy

The module retains original synthesis equations where possible. Improvements that intentionally change parameter transitions or lifecycle behavior are described in `DEVIATIONS.md`. The user's newer direction is to prioritize a musical, stable synth, not preserve every JavaScript artifact. Additional source/licence attribution is in `NOTICE.txt`.
