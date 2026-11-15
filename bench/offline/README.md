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

Run from a clean checkout of `kalharbi11/wirescape-lab` on Linux x64. All commands below are single entry points; outputs are written to ignored `build_reports/l4/` and do not contain device captures. No command passes `--confirm-audio`, `--confirm-midi` or `--confirm-lan`. UI preview binds only `127.0.0.1`.

Prerequisites: Python 3.9+, Node 22, npm, CMake, Ninja, C++17 compiler, Graphviz `dot`, `cloc` and Python `lizard`. Install `lizard` and `cloc` in your usual isolated tooling environment. For Playwright/desktop runs install the lockfiles (`cd apps/studio && npm ci`; `cd ../desktop && npm ci`) and a matching Chromium, then build Studio/Electron (`cd apps/desktop && npm run build`). Set `WIRESCAPE_CHROMIUM` to the Chromium executable if it differs from `/opt/pw-browsers/chromium`.

| Measurement | Clean-checkout command | Output |
|---|---|---|
| Repository LOC, complexity, long lines, includes, residue, CMake graph/SVG, dependencies and binary inventory | `python bench/offline/repo_facts.py` | `build_reports/l4/repo/` |
| Native Release binaries | `python tools/dev.py build --headless --config Release` then rerun `python bench/offline/repo_facts.py` | `build_reports/l4/repo/binary_sizes.csv` |
| Test inventory and run wall-times, all devices off | `python bench/offline/test_facts.py --execute` | `build_reports/l4/tests/summary.json` |
| 1,000 sidecar `setParam`, 100 connect/disconnect rounds, bundled graph loads | `python bench/offline/protocol_facts.py` | `build_reports/l4/protocol/summary.json` |
| Sidecar idle / largest bundled patch RSS (Linux `/proc`) | `python bench/offline/memory_facts.py` | `build_reports/l4/memory/summary.json` |
| FakeEngine Playwright knob/cable rAF intervals and traces at 50/100/200 modules | `node bench/offline/ui_frames.cjs` | `build_reports/l4/ui/` |
| Electron `--null-audio` startup, renderer paint and process-tree RSS across 10 runs | `xvfb-run -a node bench/offline/electron_startup.cjs` | `build_reports/l4/startup/summary.json` |

The protocol and memory commands require `build/native/wirescape-engine`, produced by the Release build above. The app commands require `apps/studio/dist/` and `apps/desktop/build/`, produced by the Electron build above. Run `python bench/offline/test_facts.py` without `--execute` to list available suites without executing tests. `ctest -N` is used for CTest inventory when the CMake build directory exists.

The UI collector records `requestAnimationFrame` interval percentiles, not GPU compositor tracing timestamps. The Playwright ZIP traces accompany each interaction. The startup collector uses a temporary Linux Bash wrapper that tees Electron stderr to an isolated file while forwarding it to Playwright's inspector handshake. It records the main-process `app.whenReady()` → native-engine hello duration printed as `boot-to-first-hello-ms`, and renderer performance paint time relative to the launch wall clock; these clocks are distinct and the metadata identifies both. The collector fails if fewer than ten hello timings are captured, even if renderer first paint succeeds. The temporary stderr logs are deleted after each run. Percentiles use nearest-rank method. Do not interpret unavailable, failed or refused operations as successful timings.

Results must be produced on the same machine from the same commit before comparing run times or binary sizes. Outputs under `build_reports/` may contain local paths; do not commit them. No measurement has been run by the author in a local checkout for this issue.

## Hosted CI fact generation

The dedicated `.github/workflows/facts.yml` uses three GitHub-hosted runners: `ubuntu-latest` (x64), `ubuntu-24.04-arm` (ARM64), and `windows-latest` (x64). It installs Python 3.12, Node 22, pinned CMake/Ninja, `cloc`, `lizard`, Graphviz, Studio/Electron and Chromium, builds Release native/desktop and runs the L4 collectors. Linux app measurements use `xvfb-run` and a null-audio sidecar. Linux x64 and ARM64 run the complete `python bench/offline/run_all.py --out-dir build_reports/l4/full` command, **without** `--quick`. Windows records an unavailable reason for Linux-only RSS/startup and the Linux-only full L2 lane.

To rerun a single-host fact stage after the commands above, use `python bench/offline/ci_stage_facts.py --runner linux-x64 --input build_reports/l4 --output .facts-staged/facts` (substitute `linux-arm64` or `windows-x64` for the runner). This stages provenance-attributed JSON and repository CSV/SVG tables into `.facts-staged/facts/<area>/ci-<runner>/`. Raw traces, suite logs and any paths local to the build host remain under `build_reports/l4`, outside committed facts.

The workflow responds to `workflow_dispatch`, pushes to `main` that change `bench/**`, and pull requests that change the collectors/workflow. Pull-request runs only validate and upload artifacts. Once this workflow exists on the default branch, use **Actions → Generate device-off facts → Run workflow** to dispatch it. Dispatch/main-push runs upload three runner-scoped artifacts, then non-force-push the measurements to `facts-auto` and create or update its PR against `main`. If GitHub rejects PR creation, the branch remains and the publishing step emits a warning.

The run-scoped facts hold Git SHA, runner image, CPU model, OS, architecture, ET date and device-off scope. A missing collector/unsupported platform is recorded as `status: unavailable`; a failed matrix job remains failed rather than being reported as a successful measurement. The workflow does not access audio/MIDI devices or create LAN listeners.
