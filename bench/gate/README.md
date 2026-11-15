<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Device-free Callgrind instruction gate (M5)

This harness counts Valgrind Callgrind **Ir per audio processing block**. It does not
open audio/MIDI devices, bind LAN sockets, or capture audio files in the repository.
Run on Linux x64 or ARM64 with Python 3.12, CMake, Ninja, Valgrind, NumPy and SciPy.

From a clean checkout, run:

    python bench/gate/instructions.py --machine linux-x64 --output build_reports/instructions/linux-x64.json

The script performs a Release headless native build with -g for debugging
information, retains Release optimization, and runs the five existing
ABI1/ABI2 cost-probe modes plus **all 24 bundled golden-render patches** and
**1/8-voice isolated module probes** for every ID in the known-module catalogue.
The bundled patch list and C4 key-on script are shared with
bench/golden/render.py (sources() and events_for_patch()).

Each datum is a difference between two Callgrind Ir totals, divided by their
block-count difference. Fixed ABI probe modes use 10 vs 30 × 256-frame blocks;
patch renders and module probes use 12 vs 24 × 128-frame blocks at 48 kHz.
The patch script includes the golden note-off event at frame 240000, but the
short profiling windows measure the **note-on phase only**. Full 10-second
golden audio render validation remains a separate test. Patch Ir also includes
the renderer's per-block output/wave writing overhead, not just DSP processing.
These choices bound Valgrind work to the 15-minute hosted job budget; they do
not replace exhaustive process profiles.

The JSON contains the actual checked-out commit, ET date, architecture,
Valgrind version and measured Ir per block. An unavailable probe is recorded
with a reason, never fabricated. No machine-specific raw paths or stdout/stderr
are published. build_reports/ is ignored; output holds numbers and provenance.

## Establish architecture baselines

1. Run the advisory workflow on the measurement PR (both Linux architectures).
2. Download instruction-current-linux-x64 and instruction-current-linux-arm64
   artifacts. Validate every fixed and bundled row was measured; note any
   unavailable isolated module rows.
3. Commit the verified files as facts/perf/linux-x64/instruction_baseline.json
   and facts/perf/linux-arm64/instruction_baseline.json unchanged, preserving
   their original run commit, machine, date and Valgrind version. Do not
   regenerate fake values or copy the x64 file into ARM64.
4. Rerun the workflow to ensure both architecture-matched baselines compare.

Use the following to print the ten largest absolute percent changes and fail
for an increase **greater than +3%** (default), missing or regressed measured
rows, or a machine/method mismatch:

    python bench/gate/compare.py baseline.json current.json --threshold 3

The --markdown option creates a job-summary table.

The workflow runs on PRs touching native/** (and on gate changes and main),
with an advisory continue-on-error **comparison** step. Build and measurement
failures remain visible and fail the job. Synthetic comparison tests exercise
a deliberate +4% slowdown without modifying or committing product code.

The two Linux platforms use separate baselines: instruction sets differ,
and the comparator rejects a cross-architecture comparison.
