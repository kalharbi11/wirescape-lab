<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Facts

Neutral data for the review. **No opinions, no "should", no ranking.**

Every entry has: what was measured, the number (with unit), how (command or script + options), the lab
commit (`sha7`), the machine (CPU, OS, audio device if any, rate, block) and the date (ET). Raw data goes
next to its summary as JSON/CSV. Quotes from other projects carry the URL and date read.

| Folder | Holds |
|---|---|
| `repo/` | code size, complexity, long lines, target/include graphs, residue scans, binary sizes |
| `perf/` | offline engine and module CPU, instruction counts, soak results |
| `dsp/` | offline sound measurements: aliasing, THD, filter response, DC, denormals, zipper, clicks |
| `device/` | owner-run results on the laptop and the Pi (real audio/MIDI): dropouts, CPU, latency, recordings' analysis |
| `app/` | startup, memory, UI frame times, protocol latency |
| `tests/` | test inventory, runtimes, CI durations and failures |
| `compare/` | other tools: features, SDK shape, export pipelines, published numbers |
| `code/` | `FACT_PACK.md`: LLM readings of the snapshot source (engine core, protocol, DSP, SDK) plus background knowledge, cross-checked; no execution. Tags and citation rules are in its §0 |

## L4 measurement coverage, 2026-11-14 (ET)

**Superseded for most rows:** hosted CI measurements at lab commit `7d3842d` are in the `ci-linux-x64`,
`ci-linux-arm64` and `ci-windows-x64` subfolders of `repo/`, `perf/`, `dsp/`, `app/` and `tests/`. The table
below records the state at `660556f`, before those runs.

Source: lab commit `660556fbfb6ef30f828c68e9a05afa38ce0ee957`. Measurement client: GitHub tree API; host: Linux x86_64 tool container, CPU model not identified; no audio/MIDI devices accessed.

This execution environment had no repository checkout and outbound GitHub DNS resolution failed. Only the GitHub tree metadata was read remotely; the code, tools and binaries could not be executed on a single checked-out machine. The device-free collectors in `bench/offline/` have been syntax checked; their runtime results remain unmeasured here.

| Requested measurement | Status and reason |
|---|---|
| LOC by folder/language, product/tests/tools | Unmeasured: no local source checkout or `cloc`; collector: `repo_facts.py` |
| Top 30 functions by complexity/length | Unmeasured: no checkout or `lizard`; collector: `repo_facts.py` |
| Native lines over 120/200 | Unmeasured: no checkout; collector: `repo_facts.py` |
| CMake target graph SVG and links/users | Unmeasured: cannot configure CMake without checkout; collector: `repo_facts.py` |
| Native engine2/control/sidecar include graph | Unmeasured: no checkout; collector: `repo_facts.py` |
| ABI1/Qt/issue reference/agent name residue recount | Unmeasured: no checkout; collector: `repo_facts.py` |
| Release sidecar, ABI1 library, module binary, Studio dist and Electron app folder sizes | Unmeasured: no Release build; collector: `repo_facts.py` |
| Dependencies, pin and licence inventory | Unmeasured: source lockfiles/CMake not present locally; collector: `repo_facts.py` records lockfile versions and explicit native pins, with missing licence fields identified |
| CTest, unittest, Vitest, Playwright Studio/desktop and protocol counts and wall times | Unmeasured: no checkout, build or installed test dependencies; collector: `test_facts.py` |
| Electron launch, hello, Studio first paint in 10 runs | Unmeasured: Electron artifacts absent; collector: `electron_startup.cjs` |
| Idle and largest-patch RSS for sidecar and Electron process tree | Unmeasured: executable and Electron artifacts absent; collectors: `memory_facts.py`, `electron_startup.cjs` |
| UI knob/cable frame times at 50, 100 and 200 modules | Unmeasured: browser and Studio build artifacts absent; collector: `ui_frames.cjs` records rAF intervals and Playwright trace |
| 1,000 setParam p50/p95/p99, per-patch loadGraph, live connect/disconnect | Unmeasured: sidecar executable absent; collector: `protocol_facts.py` |

The only captured repository metadata is `facts/repo/github_tree_inventory.json`, which reports bytes and blob counts, not lines of code or built artifact sizes.
