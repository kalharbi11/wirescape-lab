<!-- SPDX-License-Identifier: GPL-3.0-only -->
# fx.reverb: design and provenance

**Original code**, GPL-3.0-only. No third-party source code or Clouds/Mutable Instruments code is copied.

The network uses the classic lossless feedback-delay-network construction and Schroeder input allpasses. Textbook references:
- Jot and Chaigne, *Digital Delay Networks for Designing Artificial Reverberators*, AES 1991: lossless feedback mixing, line-dependent damping and time constants.
- Stautner and Puckette, *Designing Multi-Channel Reverberators*, Computer Music Journal 6(1), 1982: multichannel delay-network mixing.
- Schroeder, *Natural Sounding Artificial Reverberation*, Journal of the AES 10(3), 1962: allpass diffusion.

## Topology and decisions

Eight mutually distinct prime lengths (48 kHz bases: 1499, 1741, 1999, 2281, 2617, 3011, 3469, 4789 samples) are recalculated for the rate and `size` every 64 absolute samples. A 50 ms one-pole glide plus fractional linear taps avoids discontinuous jumps. At size 1 the longest line is ~100 ms. The orthonormal 8×8 normalized Hadamard butterfly preserves energy when frozen. The normal-feedback coefficient per line is `exp(-ln(1000) × line_samples / (rate × RT60))`, so *amplitude* falls by 60 dB over RT60 irrespective of size. One-pole feedback damping is removed in freeze.

Two allpass sections per input side and separate up-to-250 ms predelays precede alternate-line excitation. Input is attenuated as freeze approaches, the feedback gain approaches 1 over 20 ms, and motion is likewise suspended. Two fixed-phase, slow sine LFOs modulate the fractional taps deterministically. The two wet projections are orthogonal before optional mid/side width collapse. Wet/dry gains use cosine/sine equal power; at Mix=0 output bypasses the math to preserve exact dry bits. A conservative ±8 internal safety ceiling and ±2 final output ceiling are present only for pathological signal levels.

Line, predelay and allpass memory uses `WS2_LARGE` allocated in `prepare`; no state allocation, I/O, locks, exceptions, or random seed in the callback. State only contains a version word: loading it resets the delay buffers intentionally, rather than promising audio-tail continuation.

**Listening note:** No physical-audio listening was performed by the builder. Review room-to-hall colour, stereo width at fully wet, and freeze on/off transitions after a sustained chord on the owner device.

## S7.1 correction 2/2: unchanged internal 48 kHz clock

The original non-48 kHz prime re-rounding changed room geometry. Correction 1 fixed the physical-time lengths but empirically scaled damping by `pow(48000 / rate, .75)`, fitting the default damping=0.4 row only. Architect A13 verified its high-severity regressions at 0.7 and 0.9. This multiplier changed damping colour. The 96 kHz network also applies twice the number of feedback-filter iterations per physical second and excites a different Nyquist band. The 96 kHz suffix-envelope mismatch is not simply a pole-time-constant conversion: matching the pole alone also failed.

Correction 2/2 **removes all damping rate calibration**: for non-48 kHz host rates the tank is processed on the original 48 kHz clock. Eight delay lines, their feedback filter, four allpass diffusers, predelay and LFO advance at exactly 48k. A scalar phase accumulator maps each host sample to zero, one or more tank ticks; the current host input and parameter values are held across those internal ticks. The latest wet tank sample is held between ticks. Dry signal, Mix and Width remain processed at every host sample. A zero-Mix signal therefore bypasses the tank and retains exact dry PCM. All persistent storage comes from host allocations in `prepare`; callback processing allocates nothing.

At **exactly 48 kHz**, the existing sample loop is taken directly, preserving the old 48 kHz arithmetic and output path, along with module IDs, port order, parameter/state versions and freeze semantics. A local standalone C++ reproduction matched the Architect's old four-setting numerical values and predicted less than 0.03% R2 spread for damping=0.1/0.4/0.7/0.9 with the fixed internal clock. This is **diagnostic only**; actual hosted base/head values and CI must establish acceptance. The original default <=5% folder assertion is unchanged; the same metric now reports 0.1, 0.7 and 0.9 with a stronger 1% guard at size 0.5 and default decay.

**Review trade-off:** sample-held wet reconstruction can introduce spectral images/droop at higher host rates; freeze and motion are quantized to the tank's original 48k tick, while dry, Mix and Width retain host-rate resolution. This is explicit and not claimed as a separate wideband sound-quality acceptance. D5/production R2 from #193 pinned to `8823c78` is **stale for the new source**. New source-pinned R2 and D5 evidence, 48k Golden x3, instruction cap, Cortex-M7, independent reviewer approval and durable release publication remain outstanding; S7.2 has not started.
