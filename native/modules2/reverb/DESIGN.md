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

## S7.1 rate-corrected damping

The original non-48 kHz tank independently rounded eight line lengths to primes after scaling to the host rate. That changed the echo geometry nonlinearly and made the R2 suffix-envelope -60 dB crossing rate-sensitive. The corrected non-48 kHz tank instead uses **fractional taps** at `original_48k_prime_length × sample_rate / 48000`, preserving each actual 48 kHz line's physical time, including size automation. The four input diffusion windows scale their whole original 48 kHz length (including guard samples) instead of adding two unscaled samples after a rate-dependent rounding.

The initial S7.1 attempt applied a mathematically ordinary one-pole time-constant normalization, `pow(pole,48000 / rate)`. This **failed actual hosted R2**: at 44.1/48/96 kHz the captured metric was **295.80499 / 245.35417 / 169.43750 ms (51.504 % spread)**, and is retained in PR #184's CI diagnosis. The R2 metric is a suffix-maximum of an impulse response, not a single-pole RT60; network geometry also determines its last above-threshold echo. The corrected physical-time geometry uses a **fixed measured-rate calibration** `clamp(damping * pow(48000 / sample_rate, .75), 0, 1)` outside 48 kHz. The empirical exponent is deliberately documented, never presented as a general mathematical pole equivalence, and must meet the original **≤5 %** hosted R2 gate without changing the 48 kHz signal. The multiplier is computed in `prepare`, not in the realtime callback; sample-accurate modulation and freeze remain live.

At exactly 48 kHz, the original integer-prime tap calculations, diffuser counts and per-sample pole processing all remain numerically identical, so no sound-change declaration is permitted. The original module parameters and saved state are untouched, and the folder regression reconstructs the R2 one-second pre-silence + two-second suffix-maximum crossing at 44.1, 48 and 96 kHz.

This is **S7.1 only**. Wet makeup, the full-scale clamp, parameters, ports and all gain-staging work remain unchanged for the separately gated S7.2 task.
