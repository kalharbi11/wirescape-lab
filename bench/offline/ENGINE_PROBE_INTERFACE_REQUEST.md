<!-- SPDX-License-Identifier: GPL-3.0-only -->
# M4 exact impulse and denormal-tail instrumentation request

Status: **proposed interface, not implemented**. Source: issue #51, PR #60.
The current `wirescape_render` produces WAV/event-counter data, not per-block CPU times.
The existing `abi2_module_cpu_probe` drives the same source mode for its entire run
and reports aggregate max/p99. Its `denormal` source is `1e-30f`, which is a
**normal** binary32 value, and it calls descriptors directly rather than
`Engine::process`. Neither interface establishes a 1 s signal followed by
10 s of exact zero-input tail processing under the engine's shipped FTZ mode.

## Requested Fable-owned native test interface (not class A builder scope)

Add a **device-free** executable, proposed
`native/engine2/tests/measurement_probe.cpp`, registered in
`native/engine2/CMakeLists.txt` as `abi2_measurement_probe` and linked against
the existing `wirescape_app_engine` / engine2 test dependencies.

CLI (proposed, not an existing command):

- `--module <id> --mode filter-impulse --output-tap <port> --rate <Hz> --block <frames> --cutoff <Hz> --resonance <max> --observe-seconds 3`
- `--module <id> --mode decay --rate <Hz> --block <frames> --excite-seconds 1 --zero-seconds 10 --seed 42`

**Common engine fixture:** a deterministic, test-only source output feeds the
selected module through its documented input port, then a test-only output
recorder reads the named module output. Do not register the test source in the
shipping module catalogue or alter example/Studio patch files. Use the real
`Engine::process` path for block timing. Its existing scoped guard in
`native/engine2/engine2.cpp` sets x64 SSE MXCSR mask `0x8040` (FTZ + DAZ)
and AArch64 FPCR bit 24 (FZ). Measure times *inside* this process call rather
than externally changing the floating point environment or claiming that a
direct-descriptor probe uses the engine's guard. If engine test injection or
internal timer visibility is needed, extend a **test-only API** in
`native/engine2/engine2.h`/`engine2.cpp`, without modifying runtime audio
paths for ordinary graph processing. Report the active mode and architecture
from within the guarded scope.

**Filter impulse mode:** emit amplitude 1.0 at exactly sample frame 0 and
bitwise 0.0 at every subsequent input sample. Verify
`excitation_nonzero_frames==1` before reporting a measurement. Configure
resonance to the descriptor maximum (VCF 0.95, Ladder 1), name the measured
output tap (VCF `low12`, Ladder `audio`), and calculate output RMS over
frames [2 s, 3 s). Output a single `filter_impulse_probe` JSON line with:
`module`, `status`, `rate_hz`, `block_frames`, `output_tap`,
`cutoff_hz`, `resonance`, `input_nonzero_frames`, `input_peak_fs`,
`tail_start_frame`, `tail_end_frame`, `tail_rms_fs`, `faults` and
`method_version`. A failure to inject one sample is a named failed status,
never a successful impulse result.

**Denormal decay mode:** for the *exactly* first `rate_hz` frames, drive a
bounded deterministic nonzero input; for the next `10*rate_hz` frames, supply
bitwise +0.0 to **every** input signal channel (including the second input).
Do not use `1e-30f` or alternate tiny inputs as a stand-in for silence. For
each engine process block collect the elapsed CPU duration in nanoseconds.
Record exact transition frame, total and partial-block frame counts, pre-tail
steady-state median block time (e.g. the [0.25 s, 0.75 s) excitation window),
and the maximum block time in the ten-second silent phase. Output a single
`denormal_decay_probe` JSON line with: `module`, `status`, `rate_hz`,
`block_frames`, `excite_frames`, `zero_frames`, `zero_input_verified`,
`ftz_state`, `baseline_window_frames`, `steady_median_ns`,
`silent_worst_ns`, `worst_to_median_ratio`, `faults` and
`method_version`. Mark modules without a usable excitation path with a
specific `unsupported_probe` reason; do not synthesize a time.

## Bench-only integration after Fable supplies native test executable

- `bench/offline/run_all.py`: invoke `abi2_measurement_probe` for all
  applicable modules, all three rates (44.1/48/96 kHz), and block sizes
  64/128/256. Save `filters.json` exact impulse rows and
  `perf/denormal_decay.json` with source command/version and engine FTZ state.
- `bench/offline/test_run_all.py`: synthetic stdout fixtures verify exact
  frame counts, named refusal rows, rejection of `zero_input_verified=false`,
  and error-code/stderr preservation.
- `bench/offline/test_metrics.py`: known-answer impulse, zero-input block
  timing and ratio calculations for a deterministic fake sample stream.
- `facts/dsp/ci-linux-{x64,arm64}/` and
  `facts/perf/ci-linux-{x64,arm64}/`: commit only the new hosted, provenance-
  attributed measurements after both Linux architecture runs are inspected.

No physical audio device, MIDI endpoint or LAN socket is needed or permitted.
Until the native interface exists, the current Clock source produces four
nonzero samples at 44.1/48 kHz and eight at 96 kHz, and is explicitly classified
as `not_exact_impulse`. The old tiny-input CPU rows are not 10-second tail
measurements.
