<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Mixer (ABI 2)

Two mono audio inputs summed at independent Level A and Level B gains; unpatched inputs contribute silence.

Two poly audio inputs sum with per-voice levels. Missing inputs read zero.
Use `abi2_mixer_tests` for the exact reference and state matrix.
