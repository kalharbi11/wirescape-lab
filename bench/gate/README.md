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

## Verified 97-row hosted measurements and provenance

[Instruction gate run 43774054913](https://github.com/kalharbi11/wirescape-lab/actions/runs/43774054913)
tested source branch head `23d9de760e8809d6a90b2552abd078d1d104b6c7`
at actual GitHub PR merge commit
`d5ba23e1af128d689f9be3bd14c5bcb9b0961699`.
The matching artifact files are [x64 14185614245](https://github.com/kalharbi11/wirescape-lab/actions/runs/43774054913/artifacts/14185614245)
and [ARM64 14186240813](https://github.com/kalharbi11/wirescape-lab/actions/runs/43774054913/artifacts/14186240813).
Each has **97 rows**: 5 fixed modes, 24 bundled patches, 68 module
configurations (34 IDs × 1 and 8 signal channels). Each has **95 measured
numeric results** and **two explicitly unavailable `essentials.chord` rows**
(1 and 8 channels), with precise `exit 2: module_cpu_probe: create/prepare
failed` reasons. Both newly included `osc.out` rows are measured in each
artifact. The provenance fields report `callgrind-Ir-two-length-difference-v1`,
`valgrind-3.22.0`, 2026-11-15 ET, the architecture, and the original merge
commit above. The committed architecture baseline files were refreshed from
those exact artifacts, retaining the original Ir run totals and reason strings.

The previous run 43767649579 had 95 rows (5 fixed + 24 bundled + 66 module
configurations) because the historical known-ID fixture omitted `osc.out`.
Those older measurements are **not** the accepted 34-module baseline; the
two missing rows were not fabricated.

The exact artifact/committed-row equality was checked with row ID, both
Callgrind totals, and failure reason for every row. Per-architecture
FNV-1a-32 evidence fingerprints of the ASCII joined row representations
`id|total0,total1` (or `id|U:reason` for unavailable rows) are
`d84fb1f2` for x64 and `680c1fe0` for ARM64. These are verification
fingerprints, not cryptographic signatures.

## Why the chord rows cannot be measured with the current standalone probe

The failure is a specific **probe/configuration-interface gap**, not an
instruction count of zero. `native/modules2/chord/dsp.h` defines
`Chord::prepare(const ws::Setup&)` and refuses setup unless
`s.config.data` is non-null and `s.config.bytes == 4`. Those four bytes
are the little-endian `uint32_t` graph-instance identity tag; the normal
control-side adapter
`native/document/runtime_module_config.h::runtime_module_config_impl`
returns exactly those four bytes for `essentials.chord`.

The existing `native/engine2/tests/module_cpu_probe.cpp` constructs
`ws2_config{sizeof(ws2_config),rate,block,capacity,seed,nullptr,0}`
for every module, before calling `d->prepare()`. Its CLI accepts
`--module`, `--instances`, `--rate`, `--block`, `--channels`,
`--seconds`, `--seed`, `--input-mode`, `--param` and `--alternate`,
but **no** option to supply configuration bytes or a graph instance ID.
Changing the Python invocation, channel count, note script, or `--param`
cannot fix the null configuration. The benchmark retains both rows as
`status: unavailable`, and the comparator reports failure, not success.

**Smallest proposal for Fable (product-owned; not implemented here):**
In `native/engine2/tests/module_cpu_probe.cpp`, support a test-only
`--config-instance-id N` option for `essentials.chord`, encode `N`
as four little-endian bytes in stable storage that survives the call to
`d->prepare()`, and set the `ws2_config.data` and `.bytes` fields to
that storage and 4. Add a native device-free fixture that verifies rejection
without the config, successful prepare with it, and positive measured
Callgrind deltas at 1 and 8 channels. Then determine whether Chord's
event-only input/output also needs an event fixture to profile meaningful
note transformations: the current module CPU probe supplies zero event lists,
so it would otherwise measure idle Chord processing. No native changes are
permitted in this benchmark PR; resolve ownership/acceptance before replacing
the unavailable readings.

## Isolated `osc.out` measurement: no socket path

`bench/gate/instructions.py::module_rows` launches only the native
`abi2_module_cpu_probe` through Valgrind; it does not create a sidecar or
the network-capable `OutHost`. The standalone probe
(`native/engine2/tests/module_cpu_probe.cpp`) directly invokes the module
descriptor's create/prepare/process/destroy methods from
`native/control/module_catalog.h`, without constructing
`native/control/osc_out_host.cpp::OutHost`. The module implementation
(`native/modules2/osc_out/dsp.h`) defaults to a local `OutBus`
(`config.bus ? config.bus : &local_bus`) and only updates atomic counters
and event records. Its default config parser in
`native/modules2/osc_out/config.h` accepts zero bytes, and does not open
sockets. Only the separate sidecar-owned `OutHost::start()` /
`OutHost::loop()` creates and binds UDP sockets; it is **not used** by
this isolated benchmark path. These facts follow direct source inspection;
no live socket tracer was run. Do not substitute the sidecar OSC-Out host
or any device/network service for this probe. This measurement includes
only DSP-side bus updates, not UDP send or loopback transport cost.

## Dependency and gate interpretation

Because `essentials.chord` is unavailable in **both** the baseline and
current rows, the comparator intentionally exits nonzero. The workflow
`continue-on-error` makes that comparison advisory, so an overall green
collection job **does not** mean complete baseline coverage or a passing
comparison. No threshold reduction, replacement zeros, or exclusion of rows
is permitted. Same-runner golden A/B issue #55 (draft PR #64 at the time
of this documentation) is a separate unmerged dependency. Neither this
measurement nor the green collection jobs establishes Phase 0 acceptance.
