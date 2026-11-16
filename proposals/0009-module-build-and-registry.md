<!-- SPDX-License-Identifier: GPL-3.0-only -->
# 0009 — Drop a folder in, it builds and appears (design for T1.8)

Fable, 2026-11-16 (ET), against `main` at `c692c7a`. Not yet contracted: per `0004` it follows
the rename (M1 stage S6), because it moves the same paths. Inventory P3 should confirm the list
in "Today" before work starts.

## Today (observed)
Adding one module means editing, by hand, at least:
1. `native/control/module_catalog.h`: an `#include` of its `dsp.h` (34 lines of them).
2. `native/control/module_catalog.inc`: a `WS_APP_MODULE(Class)` line (35 lines).
3. `native/engine2/CMakeLists.txt`: one of several hand-written `foreach` lists that create the
   `ws2_<name>` library and its test target (`:90-111, 147-152, 162, 254-255`).
4. `native/modules2/<name>/module.json`: a second description of ports and parameters that
   repeats the C++ descriptor, read by `tools/gen_ui_catalogue.py` to make Studio's catalogue.
5. `apps/studio/public/catalogue-presentation.json` for how it looks.
6. `tools/foundation/fixtures/known_module_ids.txt`.
7. For a module with config: a branch in `native/document/runtime_module_config.h`.
8. For a module needing MIDI, OSC or telemetry: module IDs written into core files (14 references
   across the sidecar, hosts, telemetry taps and engine).

All modules are compiled into the app through the single catalogue header; the per-module shared
libraries exist for tests and the SDK path.

## Decisions
1. **The build finds modules by folder.** Every `modules/<name>/module.cpp` is a module. CMake
   globs them (`CONFIGURE_DEPENDS`) and creates one static library target per folder. A folder
   may add `module.cmake` for extra sources or dependencies (the macro oscillator needs one);
   most have none. `tests.cpp`, when present, becomes a test target with the standard link set.
2. **The registry is generated, not self-registering.** At configure time CMake writes
   `module_registry.cpp` from the same glob: one `extern` declaration and one table entry per
   folder. Each module is compiled with `WS_MODULE2_ENTRY_NAME=ws_module_entry_<name>` (the
   header already allows the entry name to be overridden), so the symbols are unique in one
   binary. Reason for not using static-initialiser registration: linkers drop unreferenced
   objects from static libraries, it needs whole-archive flags per toolchain, and it does not
   suit firmware or web targets. A generated table is plain, ordered and portable.
3. **The same `module.cpp` still builds as a shared library** with the default entry name, for
   the SDK and the later hot-reload loop. One source, two build shapes.
4. **`module.json` is deleted; the descriptor is the description.** A small tool,
   `wire-describe`, links the registry and prints every descriptor as JSON.
   `tools/gen_ui_catalogue.py` reads that output. Studio's committed catalogue stays committed,
   with the existing drift check, so Studio work needs no native build.
5. **`known_module_ids.txt` is generated** from the same output and checked for drift. An ID may
   be added by a new folder; removing or renaming one fails the check, as now.
6. **Catalogue order is by module ID.** Today it is the order of the `.inc` file. The registry
   is sorted by ID so the order does not depend on the file system or on edits.
7. **Out of scope here, stated plainly:** items 5, 7 and 8 of "Today" remain. They need the
   module API work of `0003` (panel file, declared config schema, declared capabilities). The
   T1.8 criterion "adding the template module edits 0 files outside its folder" therefore holds
   for a module with no config and no host service, which is what the template is.

## Stages
| Stage | What | Merge |
|---|---|---|
| MB1 | `wire-describe`; test that its output equals every existing `module.json` field for field; switch `gen_ui_catalogue.py` to it; generate `known_module_ids.txt`. `module.json` files still present | lead |
| MB2 | Globbed targets and generated registry; delete `module_catalog.h/.inc` and the hand `foreach` lists; delete `module.json` files | lead after contract-review |
| MB3 | CI check: copy the SDK template into `modules/` under a new ID, build, and show it in `wire-describe` output and Studio's generated catalogue with no other file edited | lead |

## Invariants and evidence
- **L1** The set of modules, and every ID, port, parameter, range and default in the catalogue,
  is unchanged. MB1's equality test is the proof that `module.json` carried nothing extra; any
  field it does carry that the descriptor lacks is an escalation, not something to drop.
- **L2** Golden 24 identical on three platforms on MB2. Modules move from one translation unit
  into separate ones, which can change floating-point code generation. Any difference is
  escalated with the differing patch and platform; it is not accepted as a declared sound change
  by the lead.
- **L3** Instruction counts: no row more than 1 % worse on MB2.
- **L4** The S0 catalogue snapshot changes in MB2 only by order (decision 6); the PR shows set
  equality of the entries. Assumption to verify first: nothing in Studio or the sidecar depends on
  catalogue order. If something does, keep the old order through an explicit list and ask.
- **L5** No module source file changes except where the entry-name macro requires it.

Signed: Fable, 2026-11-16
