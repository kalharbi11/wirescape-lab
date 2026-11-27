<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Ladder Filter (ABI 2)

Four-pole ladder-inspired nonlinear low-pass filter

The four private double poles, previous-stage feedback, exact tan/tanh calls, double parameter ramps, linear drive=0 branch, finite-input handling and explicit 1e-20 tail cut are copied in the original operation order. No voice SIMD or coefficient approximation is introduced.
Run `abi2_ladder_tests` for exact references, the rate/block/channel matrix, state and allocation checks.

S7.8 uses an instantaneous linear feedback solve with resonance-dependent prewarp; at zero resonance the original arithmetic is preserved. `abi2_ladder_tests` additionally measures peak frequency and passband at 44.1/48/96 kHz and maximum-resonance step bounds. See DESIGN.md.
