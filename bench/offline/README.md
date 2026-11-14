<!-- SPDX-License-Identifier: GPL-3.0-only -->
# L4 reproducible offline inventory (devices off)

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

The UI collector records `requestAnimationFrame` interval percentiles, not GPU compositor tracing timestamps. The Playwright ZIP traces accompany each interaction. The startup collector records main-process boot-to-hello stderr and renderer performance paint time relative to the launch wall clock; these clocks are distinct and the metadata identifies both. Percentiles use nearest-rank method. Do not interpret unavailable, failed or refused operations as successful timings.

Results must be produced on the same machine from the same commit before comparing run times or binary sizes. Outputs under `build_reports/` may contain local paths; do not commit them. No measurement has been run by the author in a local checkout for this issue.
