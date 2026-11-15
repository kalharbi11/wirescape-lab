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
**1/8-voice isolated module probes** for all 34 native catalogue entries. The
historical known-module ID fixture has only 33 entries; the collector explicitly
adds `osc.out` from its native manifest and validates the 34-entry runtime
registry. It fails if that inventory drifts.
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
3. Commit only verified numerical measurements from each native-architecture
   artifact as facts/perf/linux-x64/instruction_baseline.json and
   facts/perf/linux-arm64/instruction_baseline.json, preserving the original
   actual measurement commit, method, date and Valgrind version. Keep
   explicitly unavailable rows; never substitute zero or copy one architecture
   into another.
4. Rerun the workflow and inspect both advisory comparisons. Missing rows or
   unavailable baseline/current rows must fail the comparison, not read as
   measured zero-percent changes. A green overall workflow alone is not
   evidence of complete coverage because the comparison is advisory.

Use the following to print the ten largest absolute percent changes and fail
for an increase **greater than +3%** (default), missing or regressed measured
rows, or a machine/method mismatch. Historically unavailable rows always fail
closed (including unchanged unavailable cases):

    python bench/gate/compare.py baseline.json current.json --threshold 3

The --markdown option creates a job-summary table.

The workflow runs on PRs touching native/** (and on gate changes and main),
with an advisory continue-on-error **comparison** step. Build and measurement
failures remain visible and fail the job. Synthetic comparison tests exercise
a deliberate +4% slowdown without modifying or committing product code.

The two Linux platforms use separate baselines: instruction sets differ,
and the comparator rejects a cross-architecture comparison.

## Existing hosted measurements and coverage boundary

The original successful hosted [run 43767649579](https://github.com/kalharbi11/wirescape-lab/actions/runs/43767649579)
produced x64 artifact 14183261928 and ARM64 artifact 14183227333, each with
95 rows: five fixed modes, 24 bundled patch rows and 66 module/channel rows
(33 module IDs). Of these, 93 are numeric measurements; `essentials.chord`
for both one and eight channels reports `module_cpu_probe: create/prepare
failed` with process exit 2. The artifact `commit` is the real GitHub PR
merge commit `95fd429a73bc98417efe4f6e09833569e25731c2`, which merges
source head `4fcb1e65ebfe8217de49c0eef41d903d01dabd26`. The baseline
files preserve that original run/method provenance and both Callgrind Ir
totals; calculated per-block values are the original differences divided
by the original count windows. They do not claim a measurement on a later
commit.

The current 34-module collector requires 97 rows. The old baseline lacks
the two `osc.out` probe rows, and both chord rows are unavailable. This
is incomplete coverage, so the advisory comparator reports failures until
new validated architecture-specific measurements and any needed product/probe
triage are resolved. No excluded or failed row is treated as measured.

Same-runner sound comparison depends separately on unmerged issue #55. These
instruction measurements do not assert Phase 0 acceptance or merge readiness
for the engine restructuring.
