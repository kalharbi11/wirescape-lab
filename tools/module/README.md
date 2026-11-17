<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Module tools v0 — MT1 (check and describe)

Run from the repository root, without hardware or network access:

```sh
python tools/module/wsmod.py check native/sdk/template --json
python tools/module/wsmod.py test native/sdk/template --json
python tools/module/wsmod.py render native/sdk/template --json
```

`check` builds a shared library and a same-image runner from the folder's `module.cpp`, then invokes the runner's `describe` command to validate the actual exported descriptor. It checks registration (C1), SPDX (C2), banned headers (C3), descriptor counts/IDs/ranges (C4), optional legacy `module.json` equality (C5), and advisory portable symbols/cross-compilation (C6). `test` and `render` are **reserved stubs** until MT2 and MT3, respectively: they return 4, not a fabricated pass. Out-of-tree module folders are allowed; external source paths are never written into JSON. The compile runs offline and never opens audio, MIDI or LAN. Stock Macro Oscillator is explicitly `build_unsupported` and is not downloaded. The standard library is the only Python requirement; C++17, CMake and a supported generator are needed for builds.

Exit codes: **0** no FAIL (C6 warnings do not fail), **1** failed check or `--strict` non-advisory WARN, **2** invalid arguments/folder, **3** module build/describe failure, **4** missing environment or as-yet-unimplemented MT2/MT3 stage. Use `--full` for the future MT2 matrix or `--keep-build DIR` to retain generated CMake files. Default build outputs stay under the configured build folder, never in source.

`--json` emits deterministic `wsmod/1`: `module`, `platform`, `mode`, `results`, `summary`, `exit_code`. Every FAIL/WARN has `what` (problem), `where` (source/field), and `fix` (remediation); C6's unavailable cross tools are advisory. The ABI boundary is solely `runner/abi_ws2.h`; later MT2 and MT3 implement their separate runner/Python files, without changing the CLI. New tests live in the tool's own tree; MT1 has **no CI test hook** and requests an SR8-authorized *new advisory workflow* rather than editing existing workflows.
