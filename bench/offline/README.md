<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Offline fact pack

Run with devices off. Python 3.12 and a Release headless build are required.

```sh
python -m pip install -r bench/offline/requirements.txt
python tools/dev.py build --headless
python bench/offline/run_all.py --quick
python bench/offline/run_all.py
```

The command defaults to `build/native` and writes JSON plus Markdown summaries under `facts/perf/` and `facts/dsp/`. Use `--build-dir` and `--out-dir` for alternate locations. The run records the checked-out commit, local date in New York, CPU, operating system, compiler, rate and block sizes. Keep results from different machines separate when archiving them; CI uploads output without committing machine measurements.

`--quick` uses shortened render and soak windows; the full run renders each bundled patch for 10 seconds. The renderer has a 10-second-per-invocation maximum. Input scripts for keyboard patches are synthesized without hardware MIDI. Each test uses an isolated temporary directory. No executable is launched with audio or MIDI device flags.

The ABI2 engine benchmark runs separately at 64, 128, and 256 frames. `wirescape_soak` publishes median, percentiles and maximum but not arithmetic mean. The module CPU probe now records normal saw/noise versus constant 1e-30f inputs for each block size; 1e-30f is a normal binary32 value, not a subnormal. The `denormal_spikes` section reports measured p99 ratios without claiming subnormal floating-point handling. Failed soak cases include the original diagnostic and a correlated `loadGraph` acknowledgement or refusal from the real `wirescape-engine --null-audio` process. Sidecar transport failures are reported as unavailable, not as refusals. Modules lacking an audio or CV output and unsupported configurations are also recorded with a reason. The pure FFT measurements quantify the non-harmonic residual; they cannot independently distinguish alias products from noise or other distortion.

The JSON files preserve structured metrics, source-probe failures and unavailable measurements. Markdown summaries contain numeric tables and measurement provenance; no synthetic numbers are introduced for inaccessible measurements. Valgrind is optional; the callgrind result is unavailable if it is not installed. On CI, output is attached as an artifact and the job is non-required.

CI validates the mandatory artifact sections with `python bench/offline/verify_artifacts.py --out-dir <output-folder>` and uploads the generated `perf/soak_failures.md`, `perf/probe_failures.md`, and `perf/denormal_spikes.md` alongside their JSON data.
