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

The ABI2 engine benchmark is fixed to 256 frames; its other block-size cells are not interpolated. `wirescape_soak` publishes median, percentiles and maximum but not arithmetic mean. The CPU module probe takes saw and noise signals only, so the requested 1e-30-vs-normal denormal CPU comparison is explicitly recorded as unavailable, not estimated. Modules lacking an audio or CV output and unsupported configurations are also recorded with a reason. The pure FFT measurements quantify the non-harmonic residual; they cannot independently distinguish alias products from noise or other distortion.

The JSON files preserve structured metrics, source-probe failures and unavailable measurements. Markdown summaries contain numeric tables and measurement provenance; no synthetic numbers are introduced for inaccessible measurements. Valgrind is optional; the callgrind result is unavailable if it is not installed. On CI, output is attached as an artifact and the job is non-required.
