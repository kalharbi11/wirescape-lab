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

---

## L4 reproducible offline inventory (devices off)

Run from a clean checkout of `kalharbi11/wirescape-lab` on Linux x64/ARM64 or Windows x64. All commands below are single entry points; outputs are written to ignored `build_reports/l4/` and do not contain device captures. No command passes `--confirm-audio`, `--confirm-midi` or `--confirm-lan`. UI preview binds only `127.0.0.1`.

Prerequisites: Python 3.9+, Node 22, npm, CMake, Ninja, C++17 compiler, Graphviz `dot`, `cloc` and Python `lizard`. Install `lizard` and `cloc` in your usual isolated tooling environment. For Playwright/desktop runs install the lockfiles (`cd apps/studio && npm ci`; `cd ../desktop && npm ci`) and a matching Chromium, then build Studio/Electron (`cd apps/desktop && npm run build`). Set `WIRESCAPE_CHROMIUM` to the Chromium executable if it differs from `/opt/pw-browsers/chromium`.

| Measurement | Clean-checkout command | Output |
|---|---|---|
| Repository LOC, complexity, long lines, includes, residue, CMake graph/SVG, dependencies and binary inventory | `python bench/offline/repo_facts.py` | `build_reports/l4/repo/` |
| Native Release binaries | `python tools/dev.py build --headless --config Release` then rerun `python bench/offline/repo_facts.py` | `build_reports/l4/repo/binary_sizes.csv` |
| Test inventory and run wall-times, all devices off | `python bench/offline/test_facts.py --execute` | `build_reports/l4/tests/summary.json` |
| 1,000 sidecar `setParam`, 100 connect/disconnect rounds, bundled graph loads | `python bench/offline/protocol_facts.py` | `build_reports/l4/protocol/summary.json` |
| Sidecar idle / largest bundled patch RSS (Linux `/proc` or Windows `psutil`) | `python bench/offline/memory_facts.py` | `build_reports/l4/memory/summary.json` |
| FakeEngine Playwright knob/cable rAF intervals and traces at 50/100/200 modules | `node bench/offline/ui_frames.cjs` | `build_reports/l4/ui/` |
| Electron `--null-audio` startup, renderer paint and Electron process RSS across 10 runs | Linux: `xvfb-run -a node bench/offline/electron_startup.cjs`; Windows: `node bench/offline/electron_startup.cjs` | `build_reports/l4/startup/summary.json` |

The protocol and memory commands require the Release sidecar executable: `build/native/wirescape-engine` on Linux or `build/native/Release/wirescape-engine.exe` on Windows. Windows memory collection also requires `psutil`. The app commands require `apps/studio/dist/` and `apps/desktop/build/`, produced by the Electron build above. Run `python bench/offline/test_facts.py` without `--execute` to list available suites without executing tests. `ctest -N` is used for CTest inventory when the CMake build directory exists; Windows uses `-C Release` for inventory and execution. Failed suite runs preserve the final 40 output lines after path redaction in staged `tests.json`.

The UI collector records `requestAnimationFrame` interval percentiles, not GPU compositor tracing timestamps. The Playwright ZIP traces accompany each interaction. The startup collector uses a temporary Linux Bash wrapper that tees Electron stderr to an isolated file while forwarding it to Playwright's inspector handshake. It records the main-process `app.whenReady()` → native-engine hello duration printed as `boot-to-first-hello-ms`, and renderer performance paint time relative to the launch wall clock; these clocks are distinct and the metadata identifies both. On Linux the collector fails if fewer than ten hello timings are captured, even if renderer first paint succeeds. On Windows Electron's `app.getAppMetrics()` records Electron working-set RSS and the collector requires ten first-paint and RSS samples; an early boot-hello timing that precedes Playwright's stderr listener is recorded as unavailable with the precise capture limitation. The temporary stderr logs are deleted after each run. Percentiles use nearest-rank method. Do not interpret unavailable, failed or refused operations as successful timings.

Results must be produced on the same machine from the same commit before comparing run times or binary sizes. Outputs under `build_reports/` may contain local paths; do not commit them. No measurement has been run by the author in a local checkout for this issue.

## T0.12 UI CPU/performance attribution (FakeEngine, devices off)

The separate `ui_profile.cjs` collector reuses the 50/100/200-module
patches and knob/cable gesture shapes from `ui_frames.cjs`; it does not
modify `run_all.py`. Each workload uses **six independent repetitions**,
one complete 30-step mouse drag per repetition in a fresh preview page, with
rAF interval samples only during the instrumented window. It records a real
Chromium CDP `Profiler` CPU sample profile and a separate `Tracing`
renderer-main-thread performance trace, **not** a Playwright ZIP interaction
trace. A missing browser/timeline signal is recorded as unavailable.

From a checked-out commit with Studio dependencies, built `apps/studio/dist`
and Chromium installed:

```sh
node bench/offline/test_ui_profile_parse.cjs
node bench/offline/ui_profile.cjs --repeats 6 --output build_reports/ui-profile
```

The preview server binds **127.0.0.1** only and Studio uses FakeEngine.
No audio/MIDI device, sidecar, process-loopback or LAN socket is used.
The collector writes `summary.json`, per-trial `trials.json`, and raw
`*.cpuprofile` and `*.trace.json` in `build_reports/ui-profile/`.
These raw files are not committed: the advisory
`.github/workflows/ui-profile-advisory.yml` uploads them with 7-day retention.
Each summary gives source SHA, New York date, runner, CPU, Chromium version,
viewport, sample count, gesture repetitions, and a link to the exact
workflow artifact when staged in `facts/app/`.

`ui_profile_parse.cjs` computes nearest-rank rAF frame p50/p95/max;
CDP CPU self-time by sampled function/URL/line; and disjoint
renderer-main-thread Trace Event duration in script, style, layout,
paint and unattributed busy categories. Empty CPU profiles or profiles
without positive-duration samples with valid call frames are **unavailable**,
not measured zero. The parser saves every per-trial function's raw sampled
microseconds in the short-retention `trials.json`, sums **all** such entries
across trials, and only then truncates the displayed aggregate top ten.
The collector fails its advisory job when any workload lacks a completed
drag, measured CPU samples or a measured renderer trace, preserving
diagnostic records rather than claiming successful attribution. Chromium trace markers define
the measurement window when available; otherwise the summary explicitly
states the imprecise fallback. The CPU sampler is statistical (1 ms interval);
trace nesting is resolved by category priority and does not account for
compositor/GPU threads. Unobserved time is not necessarily idle.
Instrumenting a page alters its performance; attribute rather than
compare uninstrumented baseline absolute frame timings. The standalone
`test_ui_profile_parse.cjs` uses synthetic known-answer CDP objects
and does not start a browser, process or network connection.

## Hosted CI fact generation

The dedicated `.github/workflows/facts.yml` uses three GitHub-hosted runners: `ubuntu-latest` (x64), `ubuntu-24.04-arm` (ARM64), and `windows-latest` (x64). It installs Python 3.12, Node 22, pinned CMake/Ninja, `cloc`, `lizard`, Graphviz, Studio/Electron and Chromium, builds Release native/desktop and runs the L4 collectors. Linux app measurements use `xvfb-run` and a null-audio sidecar. Linux x64, ARM64 and Windows x64 run the complete `python bench/offline/run_all.py --out-dir build_reports/l4/full` command, **without** `--quick`. Windows uses native Electron process metrics and `psutil` RSS instead of Linux `/proc`; Callgrind remains unavailable on Windows and is reported in its own `instruction_cost` row. The Windows matrix verifies that test suites, startup, RSS, DSP and CPU sections contain measured results.

To rerun a single-host fact stage after the commands above, use `python bench/offline/ci_stage_facts.py --runner linux-x64 --input build_reports/l4 --output .facts-staged/facts` (substitute `linux-arm64` or `windows-x64` for the runner). This stages provenance-attributed JSON and repository CSV/SVG tables into `.facts-staged/facts/<area>/ci-<runner>/`. Raw traces, suite logs and any paths local to the build host remain under `build_reports/l4`, outside committed facts.

The workflow responds to `workflow_dispatch`, pushes to `main` that change `bench/**`, and pull requests that change the collectors/workflow. Pull-request runs only validate and upload artifacts. Once this workflow exists on the default branch, use **Actions → Generate device-off facts → Run workflow** to dispatch it. Dispatch/main-push runs upload three runner-scoped artifacts, then non-force-push the measurements to `facts-auto` and create or update its PR against `main`. If GitHub rejects PR creation, the branch remains and the publishing step emits a warning.

The run-scoped facts hold Git SHA, runner image, CPU model, OS, architecture, ET date and device-off scope. A missing collector/unsupported platform is recorded as `status: unavailable`; a failed matrix job remains failed rather than being reported as a successful measurement. The workflow does not access audio/MIDI devices or create LAN listeners.
