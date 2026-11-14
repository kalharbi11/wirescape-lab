<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Residue: what is left over from older designs, and whether it is live

Measured on the snapshot (`SNAPSHOT.md`). "Live" = on the shipped `wirescape-engine` or Studio path.

## 1. The first engine (ABI1): the main residue
The product runs on ABI 2 (`native/engine2`, `native/modules2`, `module2.h`). ABI1 is the original
plugin engine. Its 13 modules were all re-written for ABI 2; the ABI1 copies stay for comparisons.

| Item | Where | Live? |
|---|---|---|
| ABI1 engine, built as shared lib target `wirescape_engine` | `native/src/engine.cpp`, `native/CMakeLists.txt:8` | **Yes, linked**: `wirescape_app_engine` links it PUBLIC (`native/engine2/CMakeLists.txt:162`), so the sidecar needs `libwirescape_engine.so`/`.dll` at runtime |
| `AppEngine` creates an ABI1 engine on start, used only as a plugin loader | `native/control/app_engine.cpp:18,36,99` | Created on every start; loader path unused by the app (only `cli/play.cpp:121`) |
| Catalogue metadata kept as ABI1 structs (`ws_module_descriptor`, `ws_port_descriptor`, `ws_parameter_descriptor`) | `app_engine.cpp:13-70` | **Yes** |
| `ws_engine_config` (ABI1 config struct) as the engine config type | `sidecar/session.h:67`, `web/web_engine.cpp`, `document/runtime_patch.h`, `tools/render`, `cli` | **Yes** |
| ABI1 shim inside the realtime scheduler: `Node::legacy`, `add_abi1`, `rebind_abi1_descriptor`, ~15 branches in prepare/process/reset/set-param/reconfigure | `native/engine2/engine2.cpp` (lines ~102-130, 243, 278-311, 555-641, 749-821, 1015-1142) | Branches run; no ABI1 node is ever created by the app |
| ABI1 headers | `native/include/wirescape/{engine.h,module.h,linear_ramp.h}` | via the above |
| 13 ABI1 modules + `TEST_REPORT.json` files | `native/modules/` | No (tests and comparisons only) |
| ABI1 tests | `native/tests/{engine,module,lfo,scale_offset,provider_bridge}_tests.cpp`, `returned_filter_stress.cpp` | No |
| Provider bridge over the ABI1 engine API | `native/control/provider_bridge.*` | No (only its own test) |
| ABI1 fixture module | `native/control/app_legacy_fixture.cpp` | Test only |
| ABI1-vs-ABI2 comparisons | `abi2_benchmark`, `abi2_integration_tests`, `abi2_cost_probe`, `abi2_returned_filter_stress`, `document/qt_free_patch_coverage_tests.cpp`, `tools/capture/{reference,run}.py`, `tools/bench/` | Tests/benchmarks; the old plan was to freeze these as data before deleting ABI1 |
| ABI1 parameter numbers in the formats | `ws2_param.legacy_index` in `module2.h:43` and the SDK helper (`native/sdk/wirescape_sdk.h:23`); v1 patches key parameters by it (`document/runtime_patch.cpp:82`); Studio catalogue `legacy` map checked by `document/ui_patch_conformance.cpp:41-45` | **Yes, in the ABI and patch v1 import**. Removing ABI1 code does not remove this |

The capture harness (`tools/capture/`) also still uses ABI1 offline rendering and native patch v1.

## 2. Qt (retired; code is gone)
The first desktop UI was Qt; the QtCore document library and Qt CI are deleted. Left:
- Wording in ~40 files ("Qt-free", "frozen Qt renderer contract" in `native/tests/golden_render.cpp:23`,
  `tools/golden.py`, many `DESIGN.md`). `qt_free_patch_coverage_tests.cpp` is a real test with a historical name.
- `emit` macro guards in `modules2/chord`, `groove`, `osc_in`, `sdk/examples/step_sequencer` (useful for any host; the comments name Qt).
- `tools/golden.py --compare-renderer` (a Qt-vs-Qt-free comparison mode with nothing to compare against).
- `apps/desktop/tests/app-e2e.spec.cjs:25` passes `-DWIRESCAPE_BUILD_UI=OFF`, an option that no longer exists.
- `tools/dev.py:81` `qt_prefix` key; `tools/pi/demo.env.example` points at the archived `Wirescape-UI` repo.
- Studio tests that assert the retired Qt starter patches stay retired (`tests/starters.spec.ts` and others).
- `.gitignore` entries for the deleted `legacy/` prototype.

## 3. Names that only make sense historically
- `engine2`, `modules2`, `tests2`, "ABI 2": the "2" refers to ABI1, which is meant to go.
- Target `wirescape_engine` is the ABI1 library; `wirescape-engine` is the sidecar executable.
- `AppEngine` (the product engine wrapper) lives in `native/control/`.
- Native patch "v1" (ABI1 numeric parameters) vs Studio `PatchV2` (string IDs).

## 4. Process residue inside product files
- About 114 issue references (`#NNN`, from `kalharbi11/wirescape`) in code/test comments, and 15 agent names or rulings.
- Specs reference the old plan's decision numbers and task files (`ABI2_PLAN.md` 47 times, `ABI2_SPEC.md` 18,
  `ENGINE_PROTOCOL.md` 12, `COMMUNICATION_MODULES_PLAN.md` 12). `docs/context/HISTORY.md` decodes the D-numbers.
- `tools/dev.py accept` and `tools/foundation/acceptance*.py` read task files that are not in the lab.
- `tools/foundation/tests/test_doc_links.py` checks links to files that were left out.
- Studio tests named after reviews (`review-35.spec.ts`, `review-artifacts.spec.ts`).
- Workflows are parked in `ci/from-main/` (inactive). They reference the old repo's Pi runner, guard and merge gate.

## 5. Code shape
Dense one-line code in the core: `engine2.cpp` 25 lines over 200 chars (max 314), `runtime_patch.cpp` max 543,
`cli/play.cpp` max 444, `control/app_engine.cpp` max 397. `sidecar/session.cpp` is formatted (max 139).
