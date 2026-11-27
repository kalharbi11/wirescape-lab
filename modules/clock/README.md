<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Clock (ABI 2)

Sample-rate patchable control pulse oscillator

Free-running double phase with the ABI1 epsilon at duty boundaries. BPM retains the 5 ms ramp; tick lengths round with floor(value + 0.5), run thresholds at 0.5, and reset changes phase on a rising >=0.5 edge only. With `sync` at 1 (stepped, default 0) the phase follows the host transport beat and the output stays low while the host is stopped; `sync` 0 keeps the free-running path (0008 decision 7).
Run `abi2_clock_tests` for exact references, the rate/block/channel matrix, state and allocation checks.
