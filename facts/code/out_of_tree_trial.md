<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Out-of-tree SDK module trial

| Field | Linux x64 | Windows x64 |
|---|---:|---:|
| Steps attempted per platform | 11 | 11 |
| Steps completed out of tree | 2 of 3 | 2 of 3 |
| First out-of-tree failure | Step 3 | Step 3 |
| Existing core files changed in disposable checkout | 6 | 6 |
| New module folder staged | native/modules2/trial_gain | native/modules2/trial_gain |
| In-tree steps completed | 8 of 8 | 8 of 8 |
| Native module callback tests | 1 passed | 1 passed |
| Null-sink hello includes trial.gain | yes | yes |
| Null-sink loadGraph trial.gain accepted | yes | yes |
| CI result (initial trial) | success | failed during report date formatting |

- **Lab source commit:** `a0e37c71bc034c8ab86359635aadabfc49fd4e3e` (GitHub pull request #27 CI checkout).
- **Date:** 2026-11-14, New York.
- **Machine:** GitHub Actions `ubuntu-latest` Linux x64 and `windows-latest` Windows x64, architecture X64; CPU model not recorded.
- **Audio device:** none. Native executable ran with `--null-audio --rate 48000 --block 256`. Sample rate in Hz; block in frames.
- **Source:** [GitHub Actions run 43662399536](https://github.com/kalharbi11/wirescape-lab/actions/runs/43662399536), Linux artifact `sdk-out-of-tree-linux-x64` (`trial.json` and `out_of_tree_trial.md`), Windows job log. All durations below are wall-clock seconds printed as `TRIAL STEP` records by `bench/sdk/out_of_tree_trial.py`.
- **Trial source:** `native/sdk/template`, renamed to `trial.gain`; `native/sdk` copied outside checkout. No new dependency or physical audio/MIDI device.

## Steps and per-platform timings

| # | Action / command | Documentation section | Location | Result | Linux (s) | Windows (s) | Repository files needed or edited |
|---:|---|---|---|---|---:|---:|---|
| 1 | Copy native/sdk to external directory | MODULE_BUILD_GUIDE §B.0; SDK_AUTHOR_GUIDE §1 | Out of tree | pass / pass | 0.002 | 0.156 | none |
| 2 | Copy SDK template, rename descriptor and manifest to trial.gain | MODULE_BUILD_GUIDE §B.1–B.2; SDK_AUTHOR_GUIDE §§1–2 | Out of tree | pass / pass | 0.001 | 0.016 | none |
| 3 | `cmake -S <external> -B <external>/build -DCMAKE_BUILD_TYPE=Release` using the documented CMake snippet | MODULE_BUILD_GUIDE §B.2; SDK_AUTHOR_GUIDE §§1,12 | Out of tree | fail / fail | 0.379 | 1.625 | `native/tests2/allocation_watch.cpp` referenced outside checkout |
| 4 | Copy generated trial_gain module folder into native/modules2 | MODULE_BUILD_GUIDE §B.2; SDK_AUTHOR_GUIDE §1 | Disposable checkout | pass / pass | 0.001 | 0.000 | New `native/modules2/trial_gain/` |
| 5 | Register native CMake, header, .inc and presentation data | MODULE_BUILD_GUIDE §B.3 #1–#4; SDK_AUTHOR_GUIDE §1 | Disposable checkout | pass / pass | 0.006 | 0.015 | `native/engine2/CMakeLists.txt`, `native/control/module_catalog.h`, `native/control/module_catalog.inc`, `apps/studio/public/catalogue-presentation.json` |
| 6 | `python tools/gen_ui_catalogue.py` | MODULE_BUILD_GUIDE §B.3 #5 | Disposable checkout | pass / pass | 0.047 | 0.031 | `apps/studio/public/wirescape_modules.json` |
| 7 | Append trial module to patch guide | MODULE_BUILD_GUIDE §B.4; SDK_AUTHOR_GUIDE §12 | Disposable checkout | pass / pass | 0.000 | 0.000 | `docs/PATCH_DESIGNER_GUIDE.md` |
| 8 | `python tools/gen_ui_catalogue.py --check` | MODULE_BUILD_GUIDE §B.5 | Disposable checkout | pass / pass | 0.040 | 0.047 | no additional edits |
| 9 | `python tools/dev.py build --headless --config Release` | MODULE_BUILD_GUIDE §B.5; SDK_AUTHOR_GUIDE §12 | Disposable checkout | pass / pass | 204.896 | 167.844 | existing registration files from steps 5–6 |
| 10 | `ctest --test-dir build/native -C Release -R ^abi2_trial_gain_tests$ --output-on-failure` | MODULE_BUILD_GUIDE §§B.2,B.5; SDK_AUTHOR_GUIDE §12 | Disposable checkout | pass / pass | 0.126 | 0.188 | new module tests.cpp; existing native test infrastructure |
| 11 | `wirescape-engine --null-audio`, v0 hello and loadGraph with trial.gain wired to essentials.output | MODULE_BUILD_GUIDE §§B.3,B.5; SDK_AUTHOR_GUIDE §12 | Disposable checkout | pass / pass | 0.044 | 0.093 | compiled native engine and sidecar; no engine/sidecar source edits |

## First recorded failure: exact stderr on both operating systems

The external directory contains `native/sdk` and the renamed template. The documented CMake test target references an allocation watcher outside those copied files.

```text
CMake Error at trial_gain/CMakeLists.txt:4 (add_executable):
  Cannot find source file:

    ../../tests2/allocation_watch.cpp


CMake Error at trial_gain/CMakeLists.txt:4 (add_executable):
  No SOURCES given to target: abi2_trial_gain_tests


CMake Generate step failed.  Build files cannot be regenerated correctly.
```

The script stopped the out-of-tree phase at step 3. Steps 4–11 used a temporary CI checkout. The six existing core files edited by the trial were the five registration paths above and `docs/PATCH_DESIGNER_GUIDE.md`. The new module directory was additional. No `native/sidecar/` or engine implementation sources changed.

The initial Windows run completed all eleven trial steps, then failed to emit the final `trial.json` file because its Python standard library lacked `America/New_York` time-zone data. The workflow therefore reported failure despite the eleven step outcomes. The script's date-handling fallback was changed after this run, without installing a new package. CI rerun evidence is tracked separately.

The SDK public header `native/sdk/wirescape_sdk.h` includes `wirescape/module2.h`, which resides in `native/include/wirescape/` rather than the copied SDK folder. The in-tree CMake target `wirescape_sdk2` supplies include paths for the SDK and native include folder (`native/engine2/CMakeLists.txt:3-5`); the stand-alone test stopped at the missing allocation-watch source before reaching compilation.
