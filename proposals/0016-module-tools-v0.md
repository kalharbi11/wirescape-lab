<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0016 — Module tools v0: check, test and render for one module folder

Fable, 2026-11-16 (ET), against `main` at `b02db25`. Inventory and first draft by an Opus helper,
reviewed and ruled on by Fable. Nothing was built or run for this note. Contract: `M6`.
It brings `0003` section 5 forward (owner decision 3 in `0002`) on today's module header, in new
paths only, so it runs beside the engine rebuild.

## Today (observed)
1. **How modules build today.** Every `ws2_<name>` is a `SHARED` library over the folder's `module.cpp`, linked to the
   INTERFACE target `wirescape_sdk2`, which adds only the include dirs `native/sdk` and `native/include`
   (`native/engine2/CMakeLists.txt:3-5`). The lists are written by hand: 13 in one foreach (`:108-111`), 3 OSC/monitor (`:99-106`),
   groove and host_keyboard (`:90-93`), 10 folders with their own CMakeLists (`native/modules2/blend/CMakeLists.txt:2-3`),
   the MIDI trio in `native/io/midi/CMakeLists.txt:59-61` (linked to `wirescape_voice2`), and macro_oscillator through
   `add_subdirectory` (`engine2/CMakeLists.txt:237`). 34 catalogue entries = 32 `native/modules2/*` folders + 2 SDK examples
   (`facts/code/module_build_registry.md` §2). `module.cpp` is usually just `#include "dsp.h"` + `WS_REGISTER_MODULE(T)`
   (`native/modules2/vco/module.cpp:1-3`).
2. **Entry symbols.** `ws_module2_entry` / `ws_module2_abi_version` are exported with `WS2_EXPORT`
   (`native/include/wirescape/module2.h:109-117`). The test loader dlopens `libws2_<name>` and checks version==2
   (`native/tests2/module_loader.h:57`). The descriptor holds 10 callbacks (`module2.h:94-108`). Voices = `ws2_process.channels`,
   ≤16 (`module2.h:17,87-93`).
3. **Stock folders are not standalone.** Their includes leave the folder: `../port_state.h` (clock, mixer, noise, output,
   ladder, slew, scale_offset, function_envelope), `../../voice/note_to_cv.h` (host_keyboard, midi_to_cv, notes_to_cv; this
   needs `native/voice/allocator.cpp` at link time, `engine2/CMakeLists.txt:17,93`), `../../engine2/midi_release.h`
   (midi_in), `../../io/osc/*.h` (osc_in, osc_out, monitor). All of these except allocator.cpp are header-only.
   macro_oscillator needs a FetchContent download plus patches and the `macro_upstream` static library
   (`native/modules2/macro_oscillator/CMakeLists.txt:1-36`). Chord refuses `prepare` unless it gets 4 config bytes
   (`native/modules2/chord/dsp.h:53-54`). Macro refuses every rate except 48 kHz (`macro_oscillator/dsp.h:57-58`).
4. **native/sdk is not self-contained.** `wirescape_sdk.h:3` includes `wirescape/module2.h` from `native/include`. The
   documented out-of-tree CMake failed at step 3 on Linux and Windows because it references
   `../../tests2/allocation_watch.cpp` (`facts/code/out_of_tree_trial.md` table row 3, stderr block).
   `native/sdk/examples/test_support.h` (MIT) provides a fixed arena, `Fixed<>`, and state sink/source (`:14-64`).
5. **Harness code that can be reused without editing it.**
   - `native/tests2/allocation_watch.{h,cpp}` (MIT): replaces the global `operator new`/`new[]`/aligned-new and counts
     calls inside a scope (`allocation_watch.cpp:12-40`). It does not count `malloc`.
   - `native/tests2/dsp_fixture.h:17-35` (GPL): a fixed-storage host with a 32 KiB pool, 6 ports × 16 ch × 256 frames,
     sine inputs, initial parameter values. It includes 13 stock `dsp.h` files directly (`:3-15`), so it cannot be included for an
     arbitrary module. It is a pattern to copy, not a header to include.
   - `native/tests2/module_tests.cpp`: the existing matrix is a determinism/reset loop (`:12-18`), NaN in → `WS2_INVALID` with
     outputs zeroed and marked constant (`:32`), and no-alloc (`:232`). All of it runs on descriptors compiled *into* the
     test executable (`:10`), not on dlopened libraries.
   - Portable build flags: `-fno-exceptions -fno-rtti` / `/EHs-c- /GR-` (`engine2/CMakeLists.txt:51-57`).
   - Banned-include list and regex: `tools/foundation/tests/test_banned_includes.py:8-11`. Symbol classifier:
     `bench/portability/probe.py:39-50` (`symbol_flags`, stdlib only: double/softfloat, float libm, heap, `__cxa_guard_`).
   - M3 MB1 plans `wire-describe` (descriptor → JSON), and MB2 deletes every `module.json`
     (`proposals/0009-module-build-and-registry.md:39-41,55-56`).
6. **Sound metrics (T0.5).** `bench/offline/metrics.py` is a library of pure functions: `basic` (peak/RMS/DC/nonfinite, `:25`),
   `click_events` (`:38`), `folded_alias_frequencies` and `oscillator_metrics` (alias floor, `:120,138`), `sweep_residual_metrics`
   (zipper indicator, `:282`), `step_metrics`, `envelope_metrics` (`:410,426`). It imports **numpy and scipy** (`:6-7`;
   `bench/offline/requirements.txt`). `read_audio` accepts only stereo float32 RIFF at one rate (`:12-23`). The "denormal" probe
   feeds 1e-30, which is a normal float; the R2 tail probe links against `wirescape_engine2` (`bench/offline/README.md` M4 and R2
   paragraphs). `bench/continuity/metrics.py` is stdlib only (`:36-39`) but measures edit continuity.
7. **tools/dev.py** offers doctor, snapshot, report, check, build, test, benchmark, render, launch, accept (`:494-540`). Toolchain
   discovery is `tools/foundation/helpers.py:145-171` (cmake, ninja/make, VS generator, ctest). CI installs `cmake==4.2.3
   ninja==1.13.0` from pip (`.github/workflows/ci.yml:49`) on ubuntu-latest, ubuntu-24.04-arm, and windows-latest (`ci.yml:63-65`).
   M1 S4 owns `tools/dev.py` and deletes `native/cli` (`docs/workflow/milestones/M1.md:19`).
8. **Cortex-M7 facts** were produced by `bench/portability/probe.py` running in the advisory `.github/workflows/portability.yml`
   (pinned arm-none-eabi 14.2.rel1; `-mcpu=cortex-m7 -mthumb -mfloat-abi=hard -fno-exceptions -fno-rtti -Os`). The output is in
   `facts/repo/cortex-m7/{README.md,modules.json}`: 34 modules + template, 70 compiles, all compile.
9. **No `wirescape` CLI entry point exists.** The only executables are `wirescape_cli` (`native/CMakeLists.txt:30`, ABI1, removed in S4)
   and `wirescape-engine` (sidecar, `:155`). There is no pyproject or console_scripts entry. The name `wirescape module …` exists only
   in `proposals/0002-plan.md:119,193-203`, `0003 §5`, and `0004:11`.
10. **Locked paths.** M1: `native/engine2`, `native/control`, `native/tests2` (S3), `native/sidecar` (S5),
    `native/{src,modules,tests,cli}`, `tools/dev.py`, `tools/capture` (S4), and the whole tree in S6, which needs every other
    product PR merged or parked (`M1.md:13-26`). CI1.3 is the single writer of `ci.yml`. M3/M5 are queued on `native/`,
    `apps/`, `docs/specs`, `tools/protocol`, and "a new workflow, bench/ or tools/ci/" (MB3).

## Design
**CLI.** `python tools/module/wsmod.py {check,test,render} <folder> [--json] [--full] [--keep-build DIR]`. A thin `wsmod.py`
dispatches to `check.py`, `matrix.py`, `render.py`. Later it becomes `wirescape module …` with no change to behaviour: S6 or the
Wire-API PR adds one console entry or a `wirescape` launcher that calls `wsmod.main(argv)`. The flags and JSON schema are the
contract, and the entry name is not. `new` and `dev` are out of v0.

**Build and load: compile together, call the entry symbol.** For each folder the tool writes a throwaway CMake project
into `build/module-tools/<folder-hash>/`. It builds two targets: (a) `SHARED` from `module.cpp` (proves the deliverable links,
gives `check` its exports), and (b) the **runner executable** = tool-owned `runner/*.cpp` + the module's `module.cpp` + an
allocation counter. The runner reaches the module only through `extern "C" ws_module2_entry()`, the same symbol the loader uses
(fact 2), so it tests the C ABI, not the C++ wrapper. Reasons for compiling together instead of dlopen: the global
`operator new` override only sees a module's allocations when it is in the same image. On Windows a DLL binds its own CRT
`new`, and on Linux the exe would need `ENABLE_EXPORTS`. The existing no-alloc test works this way too (fact 5). It also keeps
one code path on all three platforms. Include dirs come only from `layout.json` (sdk, abi include, module folder). The folder
is compiled **in place**, so stock `../port_state.h` paths resolve. `layout.json` also lists per-stock-folder extras
(`allocator.cpp` for the three voice users) and a 4-byte config fixture for Chord. macro_oscillator is `build_unsupported` in v0
(Q2). The tool calls cmake/ninja found by `tools/foundation/helpers.discover_toolchain` (imported, not edited). Release, `-O2`.

**Isolation (contract rule).** `runner/abi_ws2.h` is the **only** file that names `ws2_*` / `module2.h`. It implements a
neutral `HostModule` interface: describe, create(rate, max_block, voices, config), process(frames, in, params, events, out),
reset, save, load, destroy. `tools/module/layout.json` is the **only** file that names repo paths. The Wire header change adds
`abi_wire.h` and switches one `#include`. S6 edits one JSON file.

**Test matrix** (runner subcommand `matrix`; Python drives it, parses JSON lines, words messages from `messages.json`).
Stimulus: signal inputs get a deterministic sine plus noise per port and channel. Event inputs get scripted note-on/off per voice.
Params start at their initial values. Seed 42. Every message is `WHAT / WHERE / FIX`. WHERE = rate, block, voices, port|param, channel, first frame.
| # | Test | Detected by | WHAT … / FIX … (template) |
|---|---|---|---|
| T1 | descriptor sane | runtime describe: ids `[a-z0-9_.]+`, unique per list, min<max, initial in range, finite, counts ≤ `WS2_MAX_*` | "param `{id}` initial {v} outside [{min},{max}]" / "set initial inside the range in `ws::param(...)`" |
| T2 | rates 44.1/48/96k | `prepare` result at each rate | refusal at 48k = FAIL; at others = WARN "refuses {rate} Hz" / "support it or say so in README; hosts will not load it at that rate" |
| T3 | block sizes 1,17,64,256 | `process`≠OK, or out channels > max | "process returned {code} for {n} frames" / "never assume a block is a multiple of 4/16; use `b.frames()`" |
| T4 | voices 1/4/16 | outputs for voice c differ from same stimulus alone in voice 0 (POLY outputs only) | "voice {c} leaks into voice {d}" / "index per-voice state by channel; arrays sized `WS2_MAX_CHANNELS`" |
| T5 | determinism | two fresh instances, same input, bit-compare | "two fresh instances differ at …" / "seed randomness from `config.seed`; no static mutable state" |
| T6 | reset = fresh | run 3 blocks, reset, rerun vs fresh; bit-compare | "after reset() output differs at frame {f}" / "reset() must restore every member process() changes" |
| T7 | state round trip | save after K blocks → load into fresh → continue both; truncated load must return ≠OK without crash; `UNSUPPORTED`=skip | "loaded copy diverges at frame {f}" / "save every member that affects future output, in the same order load reads it" |
| T8 | no alloc in process/reset | counter >0 inside process/reset scope; `host.alloc` called outside create/prepare | "{n} heap allocations inside process()" / "allocate in prepare() via `s.alloc`; no std::vector/string/new on the audio path" |
| T9 | NaN/±Inf in → finite out | inject per input/param, all outputs finite. Pass also if `WS2_INVALID` with zeroed constant outputs (fact 5) | "NaN on `{port}` produced NaN on `{out}`" / "clamp or reject non-finite inputs; see `std::isfinite` guard in SDK template" |
| T10 | denormal decay | FTZ/DAZ **off** in runner, 1 s signal then bitwise 0: count subnormal outputs, time to −60 dB / exact silence | v0 REPORT-ONLY (WARN): "{n} subnormal samples, settles in {t} s" / "add a tiny DC offset or flush state below 1e-15" |
| T11 | param extremes | each param at min, max, steps/options; constant and per-sample buffers | FAIL nonfinite; WARN \|out\|>4 FS: "param `{id}`=max gives peak {p}" / "limit gain or document the range" |
| T12 | fast sweeps | per-sample min→max ramp every 64 frames, per param with `MODULATABLE` | FAIL nonfinite; report click count (fact 6) as WARN |
| T13 | block-size independence | same 1 s at 256 vs 1/17/64; max abs diff | bit-equal PASS; diff ≤1e-5 PASS-with-note; larger WARN "output depends on block size (max {d})" / "update coefficients per sample or smooth across blocks" (Q4) |
Quick (default, target <10 s): 48k only; blocks 17, 256; voices 1, 4; T1–T9; T11 min/max. `--full`: the whole matrix + T10, T12, T13.
**Exit codes:** 0 no FAIL (WARNs allowed); 1 ≥1 FAIL (`--strict`: also WARN); 2 usage/folder invalid; 3 module failed to build
(compiler stderr quoted, first error first); 4 environment missing (no compiler/cmake), with a fix line.
**`--json`:** `{schema:"wsmod/1", tool_commit, abi:"ws2", module:{id,folder}, platform, mode, results:[{test, status:
pass|fail|warn|skip, what, where:{…}, fix, metrics:{…}}], summary:{pass,fail,warn,skip}, exit_code}`. Stable keys, sorted output,
no timestamps in results (CPU numbers only in `render`), so outputs can be diffed and a later watch mode can reuse it.

**render.** `render <folder> [--stimulus tone|noise|notes|silence] [--seconds 2] [--rate 48000] [--block 256] [--voices 1]
[--param id=v …] --out x.wav` (refuses an existing file). The runner writes a stereo float32 WAV in the format that
`bench/offline/metrics.read_audio` accepts (fact 6). Summary: peak, DC, RMS, nonfinite, and CPU per block (median/p99/max ns and
% of block period, timed in the runner over process only), all stdlib or C++. Clicks (`click_events`) and alias floor
(`oscillator_metrics`, only with `--fundamental HZ` or the tone stimulus) are imported by path from `bench/offline/metrics.py`
if numpy/scipy are installed. Otherwise the field reads `"unavailable: pip install -r bench/offline/requirements.txt"`, never 0.
`--patch` (render inside a small patch) is out of v0 because it needs the engine.

**check (static, no execution except the describe).** C1 `module.cpp` exists, `WS_REGISTER_MODULE` exactly once. C2 SPDX
line on every source, reported per file (rule MIT under `native/sdk`, GPL elsewhere applies in-tree only). C3 banned
includes, using the list imported from `test_banned_includes.py` (path in layout.json; `tests.cpp` exempt as today). C4 T1 via
the runner's `describe`. C5 `module.json`, if present, agrees with the descriptor on id, name, and port/param ids (transitional,
deleted by MB2). C6 **portable-tier symbols, REPORT-ONLY**: compile `module.cpp` alone with portable flags, list undefined
symbols (`nm -u`; Windows `dumpbin /symbols` or `llvm-nm` if present, else "unavailable"), classify with `probe.symbol_flags`.
Also use `arm-none-eabi-g++` if on PATH. Never fails the exit code in v0.

## Rulings on the open points
1. **Stock modules are compiled in place.** 33 of 34 need no native CMake edit; the sweep proves
   it or lists the exception as a fact.
2. **`macro_oscillator` is `build_unsupported` in v0.** Revisit after M3 MB2.
3. **Config fixtures** for stock modules that refuse an empty config live in `layout.json`. The
   Wire module header will declare a default config (`0012`).
4. **Block-size independence (T13) is warn-only in v0.** The stock sweep gives the distribution;
   a tolerance is set from it, by Fable, before the test may fail a module.
5. **Non-finite input (T9):** a module passes either by returning `WS2_INVALID` with zeroed
   constant outputs or by producing finite output. The result records which.
6. **Heap use that the `operator new` counter cannot see.** On Linux the runner is also linked
   with `--wrap` for `malloc`, `calloc`, `realloc` and `aligned_alloc`, counted in the same scope.
   On Windows a raw `malloc` in `process` shows only in the symbol report (C6) in v0. The message
   says so.
7. **The rename (M1 S6).** M6 pull requests are merged or parked before S6 opens. After S6 the
   lead files one class-A task that updates `tools/module/layout.json` and shows `wsmod test` on
   the template green. S6 itself is not changed.
8. **The Wire header.** The pull request that introduces it adds `runner/abi_wire.h` and moves
   the mutation suite and the sweep to it. Test ids, messages and the JSON keys do not change.
   `describe` and M3 MB1's `wire-describe` must print the same JSON; whichever lands second
   adopts the first one's keys.

What would overturn the build choice (compile together, call the entry symbol): a platform where
the module must be tested as the shared library an app will load. Then the runner gains a
load-at-run-time mode and the allocation test stays compile-together.

Signed: Fable, 2026-11-16
