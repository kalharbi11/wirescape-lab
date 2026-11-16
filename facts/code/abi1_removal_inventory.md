<!-- SPDX-License-Identifier: GPL-3.0-only -->
# ABI1 removal inventory — M0 r2 P1

- **Pinned examined lab commit:** `389ed265de5fc81cf72fb165ae361d3c7eec64ac` (live `main` at initial inspection); New York date **2026-11-16**.
- **Environment:** read-only source inspection through connected GitHub; no local build or device execution, no LAN socket. Paths are repository-relative. `file:line` uses 1-based line numbers at the pinned commit.
- **Scope/method:** recursive Git tree listing (1,184 tracked files, `truncated=false`), code-token searches and direct source inspection. This is inventory evidence, not removal guidance or measured runtime behavior.
- **ABI1 declarations:** `native/include/wirescape/module.h` defines the v1 module/descriptor contract; `native/include/wirescape/engine.h` exposes its v1 engine API. `module2.h` is distinct and retains some numeric compatibility identifiers.

## Build/link target and ABI1 module catalogue

| Evidence site | Observed target/source/link expression |
| --- | --- |
| `native/CMakeLists.txt:8` | `add_library(wirescape_engine SHARED src/engine.cpp)` |
| `native/CMakeLists.txt:9` | `target_compile_definitions(wirescape_engine PRIVATE WS_ENGINE_BUILD)` |
| `native/CMakeLists.txt:10` | `target_include_directories(wirescape_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)` |
| `native/CMakeLists.txt:11` | `target_link_libraries(wirescape_engine PRIVATE ${CMAKE_DL_LIBS})` |
| `native/CMakeLists.txt:17` | `function(wirescape_add_module target)` |
| `native/CMakeLists.txt:18` | `add_library(${target} SHARED module.cpp)` |
| `native/CMakeLists.txt:24` | `file(GLOB module_directories CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/modules/*")` |
| `native/CMakeLists.txt:27` | `add_subdirectory("${module_directory}")` |
| `native/CMakeLists.txt:30` | `add_executable(wirescape_cli cli/main.cpp)` |
| `native/CMakeLists.txt:31` | `target_link_libraries(wirescape_cli PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:37` | `add_executable(native_engine_tests tests/engine_tests.cpp src/engine.cpp)` |
| `native/CMakeLists.txt:38` | `target_compile_definitions(native_engine_tests PRIVATE WS_ENGINE_BUILD)` |
| `native/CMakeLists.txt:40` | `target_link_libraries(native_engine_tests PRIVATE ${CMAKE_DL_LIBS} Threads::Threads)` |
| `native/CMakeLists.txt:41` | `foreach(module vco adsr vca output)` |
| `native/CMakeLists.txt:42` | `add_library(ws_test_${module} OBJECT modules/${module}/module.cpp)` |
| `native/CMakeLists.txt:44` | `target_compile_definitions(ws_test_${module} PRIVATE WS_MODULE_ENTRY_NAME=ws_test_${module}_entry)` |
| `native/CMakeLists.txt:45` | `target_sources(native_engine_tests PRIVATE $<TARGET_OBJECTS:ws_test_${module}>)` |
| `native/CMakeLists.txt:49` | `add_library(ws_test_mixer OBJECT modules/mixer/module.cpp)` |
| `native/CMakeLists.txt:51` | `target_compile_definitions(ws_test_mixer PRIVATE WS_MODULE_ENTRY_NAME=ws_test_mixer_entry)` |
| `native/CMakeLists.txt:52` | `add_executable(native_module_tests tests/module_tests.cpp $<TARGET_OBJECTS:ws_test_mixer>` |
| `native/CMakeLists.txt:54` | `target_link_libraries(native_module_tests PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:57` | `add_library(ws_test_scale_offset OBJECT modules/scale_offset/module.cpp)` |
| `native/CMakeLists.txt:59` | `target_compile_definitions(ws_test_scale_offset PRIVATE WS_MODULE_ENTRY_NAME=ws_test_scale_offset_entry)` |
| `native/CMakeLists.txt:60` | `add_executable(native_scale_offset_tests tests/scale_offset_tests.cpp` |
| `native/CMakeLists.txt:63` | `target_link_libraries(native_scale_offset_tests PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:67` | `add_executable(native_provider_bridge_tests tests/provider_bridge_tests.cpp control/provider_bridge.cpp)` |
| `native/CMakeLists.txt:69` | `target_link_libraries(native_provider_bridge_tests PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:70` | `add_dependencies(native_provider_bridge_tests ws_vco ws_adsr ws_vca ws_output)` |
| `native/CMakeLists.txt:73` | `add_library(ws_test_lfo OBJECT modules/lfo/module.cpp)` |
| `native/CMakeLists.txt:75` | `target_compile_definitions(ws_test_lfo PRIVATE WS_MODULE_ENTRY_NAME=ws_test_lfo_entry)` |
| `native/CMakeLists.txt:76` | `add_executable(native_lfo_tests tests/lfo_tests.cpp $<TARGET_OBJECTS:ws_test_lfo>` |
| `native/CMakeLists.txt:78` | `target_link_libraries(native_lfo_tests PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:82` | `foreach(module noise slew function_envelope clock vcf ladder)` |
| `native/CMakeLists.txt:83` | `add_executable(essentials_${module}_tests modules/${module}/tests.cpp)` |
| `native/CMakeLists.txt:84` | `target_link_libraries(essentials_${module}_tests PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:85` | `add_dependencies(essentials_${module}_tests ws_${module})` |
| `native/CMakeLists.txt:89` | `add_executable(returned_filter_stress tests/returned_filter_stress.cpp)` |
| `native/CMakeLists.txt:90` | `target_link_libraries(returned_filter_stress PRIVATE wirescape_engine)` |
| `native/CMakeLists.txt:91` | `add_dependencies(returned_filter_stress ws_vcf ws_ladder)` |
| `native/CMakeLists.txt:95` | `# Isolated experimental ABI2 foundation; ABI1 app/engine/module sources stay unchanged.` |
| `native/CMakeLists.txt:96` | `add_subdirectory(engine2)` |
| `native/CMakeLists.txt:98` | `add_subdirectory(tools/render)` |
| `native/CMakeLists.txt:101` | `add_subdirectory(tools/capture)` |
| `native/engine2/CMakeLists.txt:34` | `add_library(wirescape_engine2 STATIC engine2.cpp)` |
| `native/engine2/CMakeLists.txt:35` | `target_include_directories(wirescape_engine2 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})` |
| `native/engine2/CMakeLists.txt:36` | `target_link_libraries(wirescape_engine2 PUBLIC wirescape_sdk2)` |
| `native/engine2/CMakeLists.txt:41` | `add_executable(abi2_module_tests ../tests2/module_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/engine2/CMakeLists.txt:42` | `target_link_libraries(abi2_module_tests PRIVATE wirescape_sdk2 ${CMAKE_DL_LIBS})` |
| `native/engine2/CMakeLists.txt:43` | `add_test(NAME abi2_module_tests COMMAND abi2_module_tests $<TARGET_FILE_DIR:ws_vco> ${CMAKE_BINARY_DIR}/abi2_equivalence.json)` |
| `native/engine2/CMakeLists.txt:60` | `add_executable(abi2_benchmark tests/benchmark.cpp)` |
| `native/engine2/CMakeLists.txt:61` | `target_link_libraries(abi2_benchmark PRIVATE wirescape_engine2 wirescape_engine ${CMAKE_DL_LIBS})` |
| `native/engine2/CMakeLists.txt:68` | `add_executable(abi2_integration_tests ../tests2/integration_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/engine2/CMakeLists.txt:69` | `target_link_libraries(abi2_integration_tests PRIVATE wirescape_engine2 wirescape_voice2 wirescape_engine ${CMAKE_DL_LIBS})` |
| `native/engine2/CMakeLists.txt:70` | `add_test(NAME abi2_integration_tests COMMAND abi2_integration_tests $<TARGET_FILE_DIR:ws_vco> ${CMAKE_CURRENT_SOURCE_DIR}/../../build_reports/abi2)` |
| `native/engine2/CMakeLists.txt:113` | `add_executable(abi2_cost_probe tests/cost_probe.cpp)` |
| `native/engine2/CMakeLists.txt:114` | `target_link_libraries(abi2_cost_probe PRIVATE wirescape_engine2 wirescape_engine ${CMAKE_DL_LIBS})` |
| `native/engine2/CMakeLists.txt:156` | `add_executable(abi2_returned_filter_stress ../tests2/abi2_returned_filter_stress.cpp)` |
| `native/engine2/CMakeLists.txt:157` | `target_link_libraries(abi2_returned_filter_stress PRIVATE wirescape_sdk2 wirescape_engine ${CMAKE_DL_LIBS})` |
| `native/engine2/CMakeLists.txt:159` | `add_test(NAME abi2_returned_filter_stress COMMAND abi2_returned_filter_stress $<TARGET_FILE_DIR:ws_ladder>)` |
| `native/engine2/CMakeLists.txt:164` | `add_library(wirescape_app_engine STATIC ../control/app_engine.cpp)` |
| `native/engine2/CMakeLists.txt:165` | `target_include_directories(wirescape_app_engine PUBLIC ../control)` |
| `native/engine2/CMakeLists.txt:166` | `target_link_libraries(wirescape_app_engine PUBLIC wirescape_engine2 wirescape_engine wirescape_catalog_dependencies)` |
| `native/engine2/CMakeLists.txt:167` | `target_link_libraries(wirescape_cli PRIVATE wirescape_app_engine)` |
| `native/engine2/CMakeLists.txt:194` | `add_library(wirescape_audio_service STATIC ../io/audio/portaudio_service.cpp ../io/audio/device_identity.cpp)` |
| `native/engine2/CMakeLists.txt:195` | `target_link_libraries(wirescape_audio_service PUBLIC wirescape_app_engine PRIVATE ${CMAKE_DL_LIBS} Threads::Threads)` |
| `native/engine2/CMakeLists.txt:222` | `target_link_libraries(wirescape_cli PRIVATE wirescape_runtime_document wirescape_audio_service)` |
| `native/engine2/CMakeLists.txt:223` | `add_executable(audio_callback_live_midi_tests ../io/audio/callback_live_midi_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/engine2/CMakeLists.txt:224` | `target_link_libraries(audio_callback_live_midi_tests PRIVATE wirescape_app_engine)` |
| `native/engine2/CMakeLists.txt:228` | `target_sources(wirescape_cli PRIVATE ../cli/play.cpp)` |
| `native/engine2/CMakeLists.txt:233` | `add_library(wirescape_midi_host STATIC ../control/midi_host.cpp)` |
| `native/engine2/CMakeLists.txt:235` | `target_link_libraries(wirescape_midi_host PUBLIC wirescape_app_engine wirescape_midi_service wirescape_midi_backend PRIVATE nlohmann_json::nlohmann_json)` |
| `native/engine2/CMakeLists.txt:236` | `target_link_libraries(wirescape_cli PRIVATE wirescape_midi_host)` |
| `native/engine2/CMakeLists.txt:237` | `add_executable(midi_host_tests ../control/midi_host_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/engine2/CMakeLists.txt:238` | `target_link_libraries(midi_host_tests PRIVATE wirescape_midi_host)` |
| `native/engine2/CMakeLists.txt:241` | `add_executable(app_engine_tests ../control/app_engine_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/engine2/CMakeLists.txt:242` | `target_link_libraries(app_engine_tests PRIVATE wirescape_app_engine)` |
| `native/engine2/CMakeLists.txt:245` | `add_library(app_legacy_fixture SHARED ../control/app_legacy_fixture.cpp)` |
| `native/engine2/CMakeLists.txt:247` | `add_dependencies(app_engine_tests app_legacy_fixture)` |
| `native/engine2/CMakeLists.txt:248` | `add_test(NAME app_engine_tests COMMAND app_engine_tests $<TARGET_FILE:app_legacy_fixture>)` |
| `native/document/CMakeLists.txt:8` | `add_library(wirescape_runtime_document STATIC runtime_patch.cpp)` |
| `native/document/CMakeLists.txt:10` | `target_link_libraries(wirescape_runtime_document PUBLIC wirescape_app_engine PRIVATE nlohmann_json::nlohmann_json)` |
| `native/document/CMakeLists.txt:20` | `add_executable(runtime_patch_tests runtime_patch_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/document/CMakeLists.txt:21` | `target_link_libraries(runtime_patch_tests PRIVATE wirescape_runtime_document nlohmann_json::nlohmann_json)` |
| `native/document/CMakeLists.txt:25` | `add_executable(qt_free_patch_coverage_tests qt_free_patch_coverage_tests.cpp ../tests2/allocation_watch.cpp)` |
| `native/document/CMakeLists.txt:26` | `target_link_libraries(qt_free_patch_coverage_tests PRIVATE wirescape_runtime_document wirescape_engine nlohmann_json::nlohmann_json ${CMAKE_DL_LIBS})` |
| `native/document/CMakeLists.txt:27` | `add_dependencies(qt_free_patch_coverage_tests ws_noise ws_clock ws_function_envelope ws_slew ws_vcf ws_ladder ws_vca ws_output)` |
| `native/document/CMakeLists.txt:43` | `add_test(NAME abi2_offline_play COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/cli/play_tests.py $<TARGET_FILE:wirescape_cli> "${PROJECT_SOURCE_DIR}/examples/Six_Essentials_Demo.json")` |
| `native/document/CMakeLists.txt:46` | `${PROJECT_SOURCE_DIR}/../tools/foundation/tests/test_class_demo_patches.py $<TARGET_FILE:wirescape_cli>)` |
| `native/document/CMakeLists.txt:60` | `add_executable(golden_render ../tests/golden_render.cpp)` |
| `native/document/CMakeLists.txt:61` | `target_link_libraries(golden_render PRIVATE wirescape_runtime_document nlohmann_json::nlohmann_json)` |
| `native/document/CMakeLists.txt:62` | `add_test(NAME golden_render_hashes COMMAND "${Python3_EXECUTABLE}"` |
| `native/document/CMakeLists.txt:64` | `add_test(NAME golden_event_stream COMMAND "${Python3_EXECUTABLE}"` |
| `native/document/CMakeLists.txt:66` | `add_test(NAME golden_serialization COMMAND "${Python3_EXECUTABLE}"` |
| `native/tools/capture/CMakeLists.txt:3` | `add_test(NAME capture_offline_selftests COMMAND ${Python3_EXECUTABLE}` |
| `native/tools/capture/CMakeLists.txt:4` | `${PROJECT_SOURCE_DIR}/../tools/capture/test_capture.py` |
| `native/tools/capture/CMakeLists.txt:5` | `--engine $<TARGET_FILE:wirescape_engine> --modules $<TARGET_FILE_DIR:ws_vco>)` |
| `native/tools/capture/CMakeLists.txt:9` | `add_executable(wirescape_capture capture.cpp)` |
| `native/tools/capture/CMakeLists.txt:10` | `target_compile_definitions(wirescape_capture PRIVATE _WIN32_WINNT=0x0A00)` |
| `native/tools/capture/CMakeLists.txt:11` | `target_link_libraries(wirescape_capture PRIVATE ole32 uuid mmdevapi)` |
| `native/web/CMakeLists.txt:40` | `add_library(web_core STATIC ${native}/engine2/engine2.cpp ${native}/control/app_engine.cpp` |
| `native/web/CMakeLists.txt:41` | `${native}/document/runtime_patch.cpp ${native}/src/engine.cpp ${native}/voice/allocator.cpp)` |
| `native/web/CMakeLists.txt:42` | `target_include_directories(web_core PUBLIC ${native}/include ${native}/sdk ${native}/engine2 ${native}/control` |
| `native/web/CMakeLists.txt:44` | `target_compile_definitions(web_core PUBLIC WS_ENGINE_BUILD)` |
| `native/web/CMakeLists.txt:45` | `target_link_libraries(web_core PUBLIC web_macro nlohmann_json::nlohmann_json ${CMAKE_DL_LIBS})` |
| `native/web/CMakeLists.txt:49` | `add_executable(wirescape_web web_engine.cpp)` |
| `native/web/CMakeLists.txt:50` | `target_link_libraries(wirescape_web PRIVATE web_core)` |
| `native/web/CMakeLists.txt:61` | `add_executable(web_engine_tests web_engine_tests.cpp web_engine.cpp)` |
| `native/web/CMakeLists.txt:62` | `target_link_libraries(web_engine_tests PRIVATE web_core)` |
| `native/web/CMakeLists.txt:63` | `add_test(NAME web_engine_tests COMMAND web_engine_tests ${native}/examples)` |

### ABI1 `native/modules` shared libraries

Each target below invokes the root `wirescape_add_module` function, which builds `module.cpp` and copies `module.json` (`native/CMakeLists.txt:17-22`); the directory glob is `native/CMakeLists.txt:24-29`.

| Build target site | Target | Source and module metadata |
| --- | --- | --- |
| `native/modules/adsr/CMakeLists.txt:2` | `ws_adsr` | `native/modules/adsr/module.cpp`, `native/modules/adsr/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/clock/CMakeLists.txt:1` | `ws_clock` | `native/modules/clock/module.cpp`, `native/modules/clock/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/function_envelope/CMakeLists.txt:1` | `ws_function_envelope` | `native/modules/function_envelope/module.cpp`, `native/modules/function_envelope/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/ladder/CMakeLists.txt:1` | `ws_ladder` | `native/modules/ladder/module.cpp`, `native/modules/ladder/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/lfo/CMakeLists.txt:2` | `ws_lfo` | `native/modules/lfo/module.cpp`, `native/modules/lfo/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/mixer/CMakeLists.txt:2` | `ws_mixer` | `native/modules/mixer/module.cpp`, `native/modules/mixer/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/noise/CMakeLists.txt:1` | `ws_noise` | `native/modules/noise/module.cpp`, `native/modules/noise/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/output/CMakeLists.txt:2` | `ws_output` | `native/modules/output/module.cpp`, `native/modules/output/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/scale_offset/CMakeLists.txt:2` | `ws_scale_offset` | `native/modules/scale_offset/module.cpp`, `native/modules/scale_offset/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/slew/CMakeLists.txt:1` | `ws_slew` | `native/modules/slew/module.cpp`, `native/modules/slew/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/vca/CMakeLists.txt:2` | `ws_vca` | `native/modules/vca/module.cpp`, `native/modules/vca/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/vcf/CMakeLists.txt:1` | `ws_vcf` | `native/modules/vcf/module.cpp`, `native/modules/vcf/module.json` (`native/CMakeLists.txt:18-21`) |
| `native/modules/vco/CMakeLists.txt:2` | `ws_vco` | `native/modules/vco/module.cpp`, `native/modules/vco/module.json` (`native/CMakeLists.txt:18-21`) |

## ABI1 header structs, symbols and API exports

| Source declaration | Literal declaration |
| --- | --- |
| `native/include/wirescape/module.h:14` | `#define WS_ABI_VERSION 1u` |
| `native/include/wirescape/module.h:15` | `enum ws_port_kind { WS_AUDIO = 1, WS_CONTROL = 2 };` |
| `native/include/wirescape/module.h:16` | `enum ws_event_type { WS_PARAMETER = 1, WS_NOTE_ON = 2, WS_NOTE_OFF = 3, WS_GATE = 4 };` |
| `native/include/wirescape/module.h:17` | `typedef struct ws_parameter_descriptor {` |
| `native/include/wirescape/module.h:22` | `} ws_parameter_descriptor;` |
| `native/include/wirescape/module.h:23` | `typedef struct ws_port_descriptor {` |
| `native/include/wirescape/module.h:27` | `} ws_port_descriptor;` |
| `native/include/wirescape/module.h:28` | `typedef struct ws_module_event {` |
| `native/include/wirescape/module.h:32` | `} ws_module_event;` |
| `native/include/wirescape/module.h:33` | `typedef struct ws_module_config {` |
| `native/include/wirescape/module.h:37` | `} ws_module_config;` |
| `native/include/wirescape/module.h:38` | `typedef struct ws_process_context {` |
| `native/include/wirescape/module.h:41` | `} ws_process_context;` |
| `native/include/wirescape/module.h:46` | `typedef struct ws_module_descriptor {` |
| `native/include/wirescape/module.h:51` | `const ws_port_descriptor *inputs;` |
| `native/include/wirescape/module.h:53` | `const ws_parameter_descriptor *parameters;` |
| `native/include/wirescape/module.h:54` | `void *(WS_CALL *create)(double sample_rate);` |
| `native/include/wirescape/module.h:56` | `int(WS_CALL *prepare)(void *, const ws_module_config *);` |
| `native/include/wirescape/module.h:58` | `void(WS_CALL *event)(void *, const ws_module_event *);` |
| `native/include/wirescape/module.h:59` | `void(WS_CALL *process)(void *, const float *const *, float *const *,` |
| `native/include/wirescape/module.h:61` | `} ws_module_descriptor;` |
| `native/include/wirescape/module.h:62` | `typedef const ws_module_descriptor *(WS_CALL *ws_module_entry_fn)(void);` |
| `native/include/wirescape/module.h:64` | `WS_EXPORT const ws_module_descriptor *WS_CALL ws_module_entry(void);` |
| `native/include/wirescape/engine.h:3` | `#include "module.h"` |
| `native/include/wirescape/engine.h:12` | `typedef struct ws_engine ws_engine;` |
| `native/include/wirescape/engine.h:13` | `enum ws_result {` |
| `native/include/wirescape/engine.h:23` | `typedef struct ws_engine_config {` |
| `native/include/wirescape/engine.h:27` | `} ws_engine_config;` |
| `native/include/wirescape/engine.h:28` | `typedef struct ws_event {` |
| `native/include/wirescape/engine.h:35` | `} ws_event;` |
| `native/include/wirescape/engine.h:36` | `typedef struct ws_meter {` |
| `native/include/wirescape/engine.h:43` | `} ws_meter;` |
| `native/include/wirescape/engine.h:44` | `WS_API uint32_t WS_CALL ws_engine_abi_version(void);` |
| `native/include/wirescape/engine.h:45` | `WS_API ws_engine *WS_CALL ws_engine_create(const ws_engine_config *);` |
| `native/include/wirescape/engine.h:46` | `WS_API void WS_CALL ws_engine_destroy(ws_engine *);` |
| `native/include/wirescape/engine.h:47` | `WS_API const char *WS_CALL ws_engine_error(const ws_engine *);` |
| `native/include/wirescape/engine.h:48` | `WS_API int WS_CALL ws_engine_load_module(ws_engine *, const char *library_path);` |
| `native/include/wirescape/engine.h:49` | `WS_API int WS_CALL ws_engine_register_module(ws_engine *, const ws_module_descriptor *);` |
| `native/include/wirescape/engine.h:50` | `WS_API uint32_t WS_CALL ws_engine_module_count(const ws_engine *);` |
| `native/include/wirescape/engine.h:51` | `WS_API const ws_module_descriptor *WS_CALL ws_engine_module(const ws_engine *, uint32_t index);` |
| `native/include/wirescape/engine.h:52` | `WS_API int WS_CALL ws_engine_add_node(ws_engine *, uint32_t id, const char *module_id);` |
| `native/include/wirescape/engine.h:53` | `WS_API int WS_CALL ws_engine_connect(ws_engine *, uint32_t source, uint32_t source_port,` |
| `native/include/wirescape/engine.h:55` | `WS_API int WS_CALL ws_engine_prepare(ws_engine *, uint32_t output_node, uint32_t output_port);` |
| `native/include/wirescape/engine.h:56` | `WS_API int WS_CALL ws_engine_enqueue(ws_engine *, const ws_event *);` |
| `native/include/wirescape/engine.h:60` | `WS_API int WS_CALL ws_engine_initialize_parameter(ws_engine *, uint32_t node,` |
| `native/include/wirescape/engine.h:62` | `WS_API int WS_CALL ws_engine_render(ws_engine *, float *output, uint32_t frames);` |
| `native/include/wirescape/engine.h:66` | `WS_API int WS_CALL ws_engine_reset(ws_engine *);` |
| `native/include/wirescape/engine.h:67` | `WS_API int WS_CALL ws_engine_activate(ws_engine *);` |
| `native/include/wirescape/engine.h:68` | `WS_API int WS_CALL ws_engine_deactivate(ws_engine *);` |
| `native/include/wirescape/engine.h:71` | `WS_API int WS_CALL ws_engine_panic(ws_engine *);` |
| `native/include/wirescape/engine.h:72` | `WS_API uint64_t WS_CALL ws_engine_generation(const ws_engine *);` |
| `native/include/wirescape/engine.h:73` | `WS_API int WS_CALL ws_engine_get_meter(const ws_engine *, ws_meter *);` |
| `native/include/wirescape/engine.h:76` | `WS_API int WS_CALL ws_engine_build_essentials(ws_engine *, const char *module_directory);` |

## ABI1 engine implementation, dynamic loader and module source exports

The legacy implementation and its C export/function definitions remain in the pinned tree. `ws_module_entry` and `WS_MODULE_ENTRY_NAME` are the shared-library discovery surface; `ws_module_descriptor` is the returned ABI1 structure.

| Source file:line | Literal ABI1 source evidence |
| --- | --- |
| `native/src/engine.cpp:1` | `#include "wirescape/engine.h"` |
| `native/src/engine.cpp:18` | `return LoadLibraryW(std::filesystem::u8path(p).c_str());` |
| `native/src/engine.cpp:21` | `static ws_module_entry_fn entry(Library p) {` |
| `native/src/engine.cpp:22` | `return reinterpret_cast<ws_module_entry_fn>(GetProcAddress(p, "ws_module_entry"));` |
| `native/src/engine.cpp:27` | `static Library open_library(const char *p) { return dlopen(p, RTLD_NOW \| RTLD_LOCAL); }` |
| `native/src/engine.cpp:29` | `static ws_module_entry_fn entry(Library p) {` |
| `native/src/engine.cpp:30` | `return reinterpret_cast<ws_module_entry_fn>(dlsym(p, "ws_module_entry"));` |
| `native/src/engine.cpp:47` | `const ws_module_descriptor *descriptor;` |
| `native/src/engine.cpp:54` | `bool valid_descriptor(const ws_module_descriptor *d) {` |
| `native/src/engine.cpp:55` | `if (!d \|\| d->struct_size != sizeof(*d) \|\| d->abi_version != WS_ABI_VERSION \|\| !d->id \|\|` |
| `native/src/engine.cpp:93` | `struct ws_engine {` |
| `native/src/engine.cpp:94` | `ws_engine_config config;` |
| `native/src/engine.cpp:96` | `std::vector<const ws_module_descriptor *> modules;` |
| `native/src/engine.cpp:109` | `explicit ws_engine(ws_engine_config c) : config(c), events(c.max_events) {` |
| `native/src/engine.cpp:114` | `~ws_engine() {` |
| `native/src/engine.cpp:132` | `uint32_t WS_CALL ws_engine_abi_version() { return WS_ABI_VERSION; }` |
| `native/src/engine.cpp:133` | `ws_engine *WS_CALL ws_engine_create(const ws_engine_config *c) {` |
| `native/src/engine.cpp:140` | `return new ws_engine(*c);` |
| `native/src/engine.cpp:145` | `void WS_CALL ws_engine_destroy(ws_engine *e) { delete e; }` |
| `native/src/engine.cpp:146` | `const char *WS_CALL ws_engine_error(const ws_engine *e) { return e ? e->error : "Invalid engine"; }` |
| `native/src/engine.cpp:147` | `int WS_CALL ws_engine_register_module(ws_engine *e, const ws_module_descriptor *d) {` |
| `native/src/engine.cpp:166` | `int WS_CALL ws_engine_load_module(ws_engine *e, const char *path) {` |
| `native/src/engine.cpp:178` | `auto result = ws_engine_register_module(e, f());` |
| `native/src/engine.cpp:193` | `uint32_t WS_CALL ws_engine_module_count(const ws_engine *e) {` |
| `native/src/engine.cpp:196` | `const ws_module_descriptor *WS_CALL ws_engine_module(const ws_engine *e, uint32_t i) {` |
| `native/src/engine.cpp:199` | `int WS_CALL ws_engine_add_node(ws_engine *e, uint32_t id, const char *module) {` |
| `native/src/engine.cpp:208` | `const ws_module_descriptor *d = nullptr;` |
| `native/src/engine.cpp:238` | `int WS_CALL ws_engine_connect(ws_engine *e, uint32_t src, uint32_t sp, uint32_t dst, uint32_t dp) {` |
| `native/src/engine.cpp:258` | `int WS_CALL ws_engine_prepare(ws_engine *e, uint32_t output, uint32_t port) {` |
| `native/src/engine.cpp:286` | `ws_module_config config{sizeof(ws_module_config), e->config.max_block_frames,` |
| `native/src/engine.cpp:301` | `uint64_t WS_CALL ws_engine_generation(const ws_engine *e) {` |
| `native/src/engine.cpp:304` | `int WS_CALL ws_engine_enqueue(ws_engine *e, const ws_event *event) {` |
| `native/src/engine.cpp:352` | `int WS_CALL ws_engine_initialize_parameter(ws_engine *e, uint32_t node, uint32_t parameter, float value) {` |
| `native/src/engine.cpp:366` | `ws_module_event event{WS_PARAMETER, parameter, value, 0, 0};` |
| `native/src/engine.cpp:376` | `int WS_CALL ws_engine_render(ws_engine *e, float *output, uint32_t frames) {` |
| `native/src/engine.cpp:426` | `ws_module_event me{ev.type, ev.parameter_id, ev.value, ev.source_id, ev.note_id};` |
| `native/src/engine.cpp:446` | `ws_process_context context{sizeof(ws_process_context), count, now, gen};` |
| `native/src/engine.cpp:465` | `int WS_CALL ws_engine_reset(ws_engine *e) {` |
| `native/src/engine.cpp:484` | `int WS_CALL ws_engine_activate(ws_engine *e) {` |
| `native/src/engine.cpp:490` | `int WS_CALL ws_engine_deactivate(ws_engine *e) {` |
| `native/src/engine.cpp:496` | `int WS_CALL ws_engine_panic(ws_engine *e) {` |
| `native/src/engine.cpp:502` | `int WS_CALL ws_engine_get_meter(const ws_engine *e, ws_meter *m) {` |
| `native/src/engine.cpp:518` | `int WS_CALL ws_engine_build_essentials(ws_engine *e, const char *directory) {` |
| `native/src/engine.cpp:534` | `int r = ws_engine_load_module(e, path.c_str());` |
| `native/src/engine.cpp:537` | `r = ws_engine_add_node(e, i + 1, ids[i]);` |
| `native/src/engine.cpp:541` | `int r = ws_engine_connect(e, 1, 0, 3, 0);` |
| `native/src/engine.cpp:544` | `r = ws_engine_connect(e, 2, 0, 3, 1);` |
| `native/src/engine.cpp:547` | `r = ws_engine_connect(e, 3, 0, 4, 0);` |
| `native/src/engine.cpp:550` | `return ws_engine_prepare(e, 4, 0);` |
| `native/modules/adsr/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/adsr/module.cpp:27` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/adsr/module.cpp:39` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/adsr/module.cpp:64` | `const ws_process_context *c) {` |
| `native/modules/adsr/module.cpp:95` | `const ws_port_descriptor outputs[] = {{"envelope", "Envelope", WS_CONTROL}};` |
| `native/modules/adsr/module.cpp:96` | `const ws_parameter_descriptor parameters[] = {{0, "Attack", .0001f, 30, .01f, "s"},` |
| `native/modules/adsr/module.cpp:100` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor),` |
| `native/modules/adsr/module.cpp:101` | `WS_ABI_VERSION,` |
| `native/modules/adsr/module.cpp:117` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/adsr/module.cpp:118` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/adsr/module.cpp:120` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |
| `native/modules/clock/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/clock/module.cpp:12` | `bool valid_config(const ws_module_config *c) noexcept {` |
| `native/modules/clock/module.cpp:13` | `return c && c->struct_size >= sizeof(ws_module_config) && std::isfinite(c->sample_rate) &&` |
| `native/modules/clock/module.cpp:16` | `bool valid_process(const void *p, float *const *out, const ws_process_context *c, uint32_t count, uint32_t max_frames) noexcept {` |
| `native/modules/clock/module.cpp:17` | `if (!p \|\| !out \|\| !c \|\| c->struct_size < sizeof(ws_process_context) \|\| c->frames > max_frames) return false;` |
| `native/modules/clock/module.cpp:30` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/clock/module.cpp:40` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/clock/module.cpp:51` | `void WS_CALL process(void *p, const float *const *in, float *const *out, const ws_process_context *c) {` |
| `native/modules/clock/module.cpp:67` | `const ws_port_descriptor inputs[] = {{"reset", "Reset", WS_CONTROL}};` |
| `native/modules/clock/module.cpp:68` | `const ws_port_descriptor outputs[] = {{"clock", "Clock", WS_CONTROL}};` |
| `native/modules/clock/module.cpp:69` | `const ws_parameter_descriptor parameters[] = {{0, "BPM", 20.0f, 300.0f, 120.0f, "BPM"}, {1, "Ticks per beat", 1.0f, 24.0f, 1.0f, ""}, {2, "Duty", 0.01f, 0.99f, 0.5f, ""}, {3, "Run", 0.0f, 1.0f, 1.0f, ""}};` |
| `native/modules/clock/module.cpp:70` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/clock/module.cpp:74` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/clock/module.cpp:75` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/clock/module.cpp:77` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() { return &descriptor; }` |
| `native/modules/function_envelope/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/function_envelope/module.cpp:12` | `bool valid_config(const ws_module_config *c) noexcept {` |
| `native/modules/function_envelope/module.cpp:13` | `return c && c->struct_size >= sizeof(ws_module_config) && std::isfinite(c->sample_rate) &&` |
| `native/modules/function_envelope/module.cpp:16` | `bool valid_process(const void *p, float *const *out, const ws_process_context *c, uint32_t count, uint32_t max_frames) noexcept {` |
| `native/modules/function_envelope/module.cpp:17` | `if (!p \|\| !out \|\| !c \|\| c->struct_size < sizeof(ws_process_context) \|\| c->frames > max_frames) return false;` |
| `native/modules/function_envelope/module.cpp:31` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/function_envelope/module.cpp:37` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/function_envelope/module.cpp:54` | `void WS_CALL process(void *p, const float *const *in, float *const *out, const ws_process_context *c) {` |
| `native/modules/function_envelope/module.cpp:74` | `const ws_port_descriptor inputs[] = {{"gate", "Gate", WS_CONTROL}};` |
| `native/modules/function_envelope/module.cpp:75` | `const ws_port_descriptor outputs[] = {{"envelope", "Envelope", WS_CONTROL}};` |
| `native/modules/function_envelope/module.cpp:76` | `const ws_parameter_descriptor parameters[] = {{0, "Rise", 0.0001f, 30.0f, 0.01f, "s"}, {1, "Fall", 0.0001f, 30.0f, 0.1f, "s"}, {2, "Curve", -1.0f, 1.0f, 0.0f, ""}};` |
| `native/modules/function_envelope/module.cpp:77` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/function_envelope/module.cpp:81` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/function_envelope/module.cpp:82` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/function_envelope/module.cpp:84` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() { return &descriptor; }` |
| `native/modules/ladder/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/ladder/module.cpp:12` | `bool valid_config(const ws_module_config *c) noexcept {` |
| `native/modules/ladder/module.cpp:13` | `return c && c->struct_size >= sizeof(ws_module_config) && std::isfinite(c->sample_rate) &&` |
| `native/modules/ladder/module.cpp:16` | `bool valid_process(const void *p, float *const *out, const ws_process_context *c, uint32_t count, uint32_t max_frames) noexcept {` |
| `native/modules/ladder/module.cpp:17` | `if (!p \|\| !out \|\| !c \|\| c->struct_size < sizeof(ws_process_context) \|\| c->frames > max_frames) return false;` |
| `native/modules/ladder/module.cpp:48` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/ladder/module.cpp:59` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/ladder/module.cpp:66` | `void WS_CALL process(void *p, const float *const *in, float *const *out, const ws_process_context *c) {` |
| `native/modules/ladder/module.cpp:85` | `const ws_port_descriptor inputs[] = {{"audio", "Audio", WS_AUDIO}};` |
| `native/modules/ladder/module.cpp:86` | `const ws_port_descriptor outputs[] = {{"audio", "Audio", WS_AUDIO}};` |
| `native/modules/ladder/module.cpp:87` | `const ws_parameter_descriptor parameters[] = {{0, "Cutoff", 20.0f, 20000.0f, 1000.0f, "Hz"}, {1, "Resonance", 0.0f, 1.0f, 0.0f, ""}, {2, "Drive", 0.0f, 2.0f, 0.0f, ""}};` |
| `native/modules/ladder/module.cpp:88` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/ladder/module.cpp:92` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/ladder/module.cpp:93` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/ladder/module.cpp:95` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() { return &descriptor; }` |
| `native/modules/lfo/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/lfo/module.cpp:27` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/lfo/module.cpp:36` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/lfo/module.cpp:44` | `const ws_process_context *c) {` |
| `native/modules/lfo/module.cpp:54` | `const ws_port_descriptor outputs[] = {{"control", "Control", WS_CONTROL}};` |
| `native/modules/lfo/module.cpp:55` | `const ws_parameter_descriptor parameters[] = {{0, "Rate", .01f, 20, 1, "Hz"},` |
| `native/modules/lfo/module.cpp:58` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/lfo/module.cpp:63` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/lfo/module.cpp:64` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/lfo/module.cpp:66` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |
| `native/modules/mixer/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/mixer/module.cpp:23` | `int WS_CALL prepare(void *p, const ws_module_config *config) {` |
| `native/modules/mixer/module.cpp:24` | `if (!p \|\| !config \|\| config->struct_size < sizeof(ws_module_config) \|\|` |
| `native/modules/mixer/module.cpp:38` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/mixer/module.cpp:50` | `const ws_process_context *c) {` |
| `native/modules/mixer/module.cpp:63` | `const ws_port_descriptor inputs[] = {` |
| `native/modules/mixer/module.cpp:67` | `const ws_port_descriptor outputs[] = {` |
| `native/modules/mixer/module.cpp:70` | `const ws_parameter_descriptor parameters[] = {` |
| `native/modules/mixer/module.cpp:74` | `const ws_module_descriptor descriptor = {` |
| `native/modules/mixer/module.cpp:75` | `sizeof(ws_module_descriptor),` |
| `native/modules/mixer/module.cpp:76` | `WS_ABI_VERSION,` |
| `native/modules/mixer/module.cpp:95` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/mixer/module.cpp:96` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/mixer/module.cpp:98` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |
| `native/modules/noise/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/noise/module.cpp:12` | `bool valid_config(const ws_module_config *c) noexcept {` |
| `native/modules/noise/module.cpp:13` | `return c && c->struct_size >= sizeof(ws_module_config) && std::isfinite(c->sample_rate) &&` |
| `native/modules/noise/module.cpp:16` | `bool valid_process(const void *p, float *const *out, const ws_process_context *c, uint32_t count, uint32_t max_frames) noexcept {` |
| `native/modules/noise/module.cpp:17` | `if (!p \|\| !out \|\| !c \|\| c->struct_size < sizeof(ws_process_context) \|\| c->frames > max_frames) return false;` |
| `native/modules/noise/module.cpp:26` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/noise/module.cpp:34` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/noise/module.cpp:39` | `void WS_CALL process(void *p, const float *const *, float *const *out, const ws_process_context *c) {` |
| `native/modules/noise/module.cpp:49` | `const ws_port_descriptor *inputs = nullptr;` |
| `native/modules/noise/module.cpp:50` | `const ws_port_descriptor outputs[] = {{"audio", "Audio", WS_AUDIO}};` |
| `native/modules/noise/module.cpp:51` | `const ws_parameter_descriptor parameters[] = {{0, "Level", 0.0f, 1.0f, 0.2f, ""}};` |
| `native/modules/noise/module.cpp:52` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/noise/module.cpp:56` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/noise/module.cpp:57` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/noise/module.cpp:59` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() { return &descriptor; }` |
| `native/modules/output/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/output/module.cpp:9` | `int WS_CALL prepare(void *, const ws_module_config *) { return 0; }` |
| `native/modules/output/module.cpp:10` | `void WS_CALL event(void *, const ws_module_event *) {}` |
| `native/modules/output/module.cpp:12` | `const ws_process_context *c) {` |
| `native/modules/output/module.cpp:16` | `const ws_port_descriptor inputs[] = {{"audio", "Audio", WS_AUDIO}},` |
| `native/modules/output/module.cpp:18` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor),` |
| `native/modules/output/module.cpp:19` | `WS_ABI_VERSION,` |
| `native/modules/output/module.cpp:35` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/output/module.cpp:36` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/output/module.cpp:38` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |
| `native/modules/scale_offset/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/scale_offset/module.cpp:19` | `int WS_CALL prepare(void *state, const ws_module_config *config) {` |
| `native/modules/scale_offset/module.cpp:25` | `void WS_CALL event(void *state, const ws_module_event *event) {` |
| `native/modules/scale_offset/module.cpp:32` | `const ws_process_context *context) {` |
| `native/modules/scale_offset/module.cpp:39` | `const ws_port_descriptor inputs[] = {{"control", "Control", WS_CONTROL}};` |
| `native/modules/scale_offset/module.cpp:40` | `const ws_port_descriptor outputs[] = {{"control", "Control", WS_CONTROL}};` |
| `native/modules/scale_offset/module.cpp:41` | `const ws_parameter_descriptor parameters[] = {{0, "Scale", -2, 2, 1, ""},` |
| `native/modules/scale_offset/module.cpp:43` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/scale_offset/module.cpp:48` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/scale_offset/module.cpp:49` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/scale_offset/module.cpp:51` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |
| `native/modules/slew/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/slew/module.cpp:12` | `bool valid_config(const ws_module_config *c) noexcept {` |
| `native/modules/slew/module.cpp:13` | `return c && c->struct_size >= sizeof(ws_module_config) && std::isfinite(c->sample_rate) &&` |
| `native/modules/slew/module.cpp:16` | `bool valid_process(const void *p, float *const *out, const ws_process_context *c, uint32_t count, uint32_t max_frames) noexcept {` |
| `native/modules/slew/module.cpp:17` | `if (!p \|\| !out \|\| !c \|\| c->struct_size < sizeof(ws_process_context) \|\| c->frames > max_frames) return false;` |
| `native/modules/slew/module.cpp:24` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/slew/module.cpp:30` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/slew/module.cpp:37` | `void WS_CALL process(void *p, const float *const *in, float *const *out, const ws_process_context *c) {` |
| `native/modules/slew/module.cpp:56` | `const ws_port_descriptor inputs[] = {{"control", "Control", WS_CONTROL}};` |
| `native/modules/slew/module.cpp:57` | `const ws_port_descriptor outputs[] = {{"control", "Control", WS_CONTROL}};` |
| `native/modules/slew/module.cpp:58` | `const ws_parameter_descriptor parameters[] = {{0, "Rise", 0.0f, 10.0f, 0.1f, "s/unit"}, {1, "Fall", 0.0f, 10.0f, 0.1f, "s/unit"}};` |
| `native/modules/slew/module.cpp:59` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/slew/module.cpp:63` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/slew/module.cpp:64` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/slew/module.cpp:66` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() { return &descriptor; }` |
| `native/modules/vca/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/vca/module.cpp:16` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/vca/module.cpp:19` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/vca/module.cpp:26` | `const ws_process_context *c) {` |
| `native/modules/vca/module.cpp:32` | `const ws_port_descriptor inputs[] = {{"audio", "Audio", WS_AUDIO},` |
| `native/modules/vca/module.cpp:35` | `const ws_parameter_descriptor parameters[] = {{0, "Gain", 0, 2, 1, ""}};` |
| `native/modules/vca/module.cpp:36` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor),` |
| `native/modules/vca/module.cpp:37` | `WS_ABI_VERSION,` |
| `native/modules/vca/module.cpp:53` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/vca/module.cpp:54` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/vca/module.cpp:56` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |
| `native/modules/vcf/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/vcf/module.cpp:12` | `bool valid_config(const ws_module_config *c) noexcept {` |
| `native/modules/vcf/module.cpp:13` | `return c && c->struct_size >= sizeof(ws_module_config) && std::isfinite(c->sample_rate) &&` |
| `native/modules/vcf/module.cpp:16` | `bool valid_process(const void *p, float *const *out, const ws_process_context *c, uint32_t count, uint32_t max_frames) noexcept {` |
| `native/modules/vcf/module.cpp:17` | `if (!p \|\| !out \|\| !c \|\| c->struct_size < sizeof(ws_process_context) \|\| c->frames > max_frames) return false;` |
| `native/modules/vcf/module.cpp:47` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/vcf/module.cpp:57` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/vcf/module.cpp:63` | `void WS_CALL process(void *p, const float *const *in, float *const *out, const ws_process_context *c) {` |
| `native/modules/vcf/module.cpp:85` | `const ws_port_descriptor inputs[] = {{"audio", "Audio", WS_AUDIO}};` |
| `native/modules/vcf/module.cpp:86` | `const ws_port_descriptor outputs[] = {{"low12", "Low12", WS_AUDIO}, {"low24", "Low24", WS_AUDIO}};` |
| `native/modules/vcf/module.cpp:87` | `const ws_parameter_descriptor parameters[] = {{0, "Cutoff", 20.0f, 20000.0f, 1000.0f, "Hz"}, {1, "Resonance", 0.0f, 0.95f, 0.0f, ""}};` |
| `native/modules/vcf/module.cpp:88` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor), WS_ABI_VERSION,` |
| `native/modules/vcf/module.cpp:92` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/vcf/module.cpp:93` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/vcf/module.cpp:95` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() { return &descriptor; }` |
| `native/modules/vco/module.cpp:2` | `#include "wirescape/module.h"` |
| `native/modules/vco/module.cpp:19` | `int WS_CALL prepare(void *p, const ws_module_config *c) {` |
| `native/modules/vco/module.cpp:25` | `void WS_CALL event(void *p, const ws_module_event *e) {` |
| `native/modules/vco/module.cpp:35` | `const ws_process_context *c) {` |
| `native/modules/vco/module.cpp:44` | `const ws_port_descriptor outputs[] = {{"audio", "Audio", WS_AUDIO}};` |
| `native/modules/vco/module.cpp:45` | `const ws_parameter_descriptor parameters[] = {{0, "Frequency", .01f, 20000, 220, "Hz"}};` |
| `native/modules/vco/module.cpp:46` | `const ws_module_descriptor descriptor = {sizeof(ws_module_descriptor),` |
| `native/modules/vco/module.cpp:47` | `WS_ABI_VERSION,` |
| `native/modules/vco/module.cpp:63` | `#ifndef WS_MODULE_ENTRY_NAME` |
| `native/modules/vco/module.cpp:64` | `#define WS_MODULE_ENTRY_NAME ws_module_entry` |
| `native/modules/vco/module.cpp:66` | `extern "C" WS_EXPORT const ws_module_descriptor *WS_CALL WS_MODULE_ENTRY_NAME() {` |

Each module's `module.json` is copied to its shared-library output location by `native/CMakeLists.txt:20-21`; it is metadata, not a separate source or ABI function. Exact module source and target binding is enumerated in the preceding build catalogue.


## Facade, provider bridge, document loader and ABI2 scheduler compatibility

| Source file:line | ABI1 field, branch, loader call or bridging usage |
| --- | --- |
| `native/control/app_engine.cpp:15` | `const ws2_descriptor* native=nullptr;ws_module_descriptor metadata{};` |
| `native/control/app_engine.cpp:16` | `std::vector<ws_port_descriptor> inputs,outputs;std::vector<ws_parameter_descriptor> params;` |
| `native/control/app_engine.cpp:18` | `std::shared_ptr<ws_engine> legacy{nullptr,ws_engine_destroy};` |
| `native/control/app_engine.cpp:19` | `std::vector<std::shared_ptr<ws_engine>> library_owners;` |
| `native/control/app_engine.cpp:36` | `explicit AppEngine(const ws_engine_config& c,const wirescape::engine2::Config* override=nullptr):legacy(ws_engine_create(&c),ws_engine_destroy),engine(override?*override:config(c)){` |
| `native/control/app_engine.cpp:48` | `static_cast<uint32_t>(d->inputs[i].hint == WS2_AUDIO ? WS_AUDIO : WS_CONTROL)});` |
| `native/control/app_engine.cpp:51` | `static_cast<uint32_t>(d->outputs[i].hint == WS2_AUDIO ? WS_AUDIO : WS_CONTROL)});` |
| `native/control/app_engine.cpp:54` | `e.params.push_back({p.legacy_index, p.name, p.minimum, p.maximum, p.initial, p.unit});` |
| `native/control/app_engine.cpp:56` | `e.metadata = {sizeof(ws_module_descriptor),` |
| `native/control/app_engine.cpp:57` | `WS_ABI_VERSION,` |
| `native/control/app_engine.cpp:74` | `static wirescape::engine2::Config config(const ws_engine_config& c){wirescape::engine2::Config r;r.sample_rate=c.sample_rate;r.max_block=c.max_block_frames;r.max_nodes=c.max_nodes;r.event_budget=c.max_events;return r;}` |
| `native/control/app_engine.cpp:77` | `AppEngine* app_engine_create(const ws_engine_config*c){` |
| `native/control/app_engine.cpp:81` | `wirescape::engine2::Config AppEngineConfig(const ws_engine_config&c){return AppEngine::config(c);}` |
| `native/control/app_engine.cpp:82` | `AppEngine* app_engine_create_config(const ws_engine_config*c,const wirescape::engine2::Config*n){` |
| `native/control/app_engine.cpp:90` | `int app_engine_register_module(AppEngine*e,const ws_module_descriptor*d){if(!d)return WS_INVALID;if(e->find(d->id))return WS_OK;e->entries.emplace_back();e->entries.back().metadata=*d;return WS_OK;}` |
| `native/control/app_engine.cpp:96` | `e->library_owners.push_back(source->legacy);` |
| `native/control/app_engine.cpp:99` | `int app_engine_load_module(AppEngine*e,const char*path){int r=ws_engine_load_module(e->legacy.get(),path);if(r!=WS_OK)return r;for(uint32_t i=0;i<ws_engine_module_count(e->legacy.get());++i)app_engine_register_module(e,ws_engine_module(e->legacy.get(),i));return WS_OK;}` |
| `native/control/app_engine.cpp:101` | `const ws_module_descriptor* app_engine_module(const AppEngine*e,uint32_t i){return i<e->entries.size()?&e->entries[i].metadata:nullptr;}` |
| `native/control/app_engine.cpp:108` | `int app_engine_add_node_config(AppEngine*e,uint32_t id,const char*type,const std::vector<uint8_t>&config){auto*d=e->find(type);if(!d)return WS_NOT_FOUND;bool ok=d->native?e->engine.add_node(id,d->native,config):(config.empty()&&e->engine.add_abi1(id,&d->metadata));if(ok)e->nodes[` |
| `native/control/app_engine.cpp:123` | `if (!entry->native && !candidate->engine.rebind_abi1_descriptor(item.first, &entry->metadata)) {` |
| `native/control/app_engine.cpp:139` | `int app_engine_enqueue(AppEngine*e,const ws_event*v){` |
| `native/control/app_engine.cpp:142` | `if(v->type==WS_PARAMETER){` |
| `native/control/app_engine.cpp:147` | `else if(v->type==WS_GATE){` |
| `native/control/app_engine.cpp:154` | `}else x.type=v->type==WS_NOTE_ON?WS2_NOTE_ON:WS2_NOTE_OFF;` |
| `native/control/app_engine.cpp:254` | `int app_engine_get_meter(const AppEngine*e,ws_meter*m){auto x=e->engine.meter();*m={sizeof(*m),x.frame,e->blocks.load(),x.late,e->peak.load(),0,x.generation,x.dropped,0,0};return WS_OK;}` |
| `native/control/app_engine.h:3` | `#include "wirescape/engine.h"` |
| `native/control/app_engine.h:7` | `AppEngine* app_engine_create(const ws_engine_config*);` |
| `native/control/app_engine.h:8` | `wirescape::engine2::Config AppEngineConfig(const ws_engine_config&);` |
| `native/control/app_engine.h:9` | `AppEngine* app_engine_create_config(const ws_engine_config*,const wirescape::engine2::Config*);` |
| `native/control/app_engine.h:14` | `int app_engine_register_module(AppEngine*,const ws_module_descriptor*);` |
| `native/control/app_engine.h:17` | `const ws_module_descriptor* app_engine_module(const AppEngine*,uint32_t);` |
| `native/control/app_engine.h:27` | `int app_engine_enqueue(AppEngine*,const ws_event*);` |
| `native/control/app_engine.h:49` | `int app_engine_get_meter(const AppEngine*,ws_meter*);` |
| `native/control/provider_bridge.cpp:15` | `ProviderBridge::ProviderBridge(ws_engine *engine, Config config) noexcept` |
| `native/control/provider_bridge.cpp:18` | `generation_ = ws_engine_generation(engine_);` |
| `native/control/provider_bridge.cpp:30` | `ws_meter meter{sizeof(ws_meter)};` |
| `native/control/provider_bridge.cpp:31` | `return ws_engine_get_meter(engine_, &meter) == WS_OK &&` |
| `native/control/provider_bridge.cpp:73` | `ws_engine_panic(engine_);` |
| `native/control/provider_bridge.cpp:78` | `if (ws_engine_generation(engine_) == generation_) return true;` |
| `native/control/provider_bridge.cpp:85` | `if ((input.type != WS_PARAMETER && input.type != WS_NOTE_ON &&` |
| `native/control/provider_bridge.cpp:86` | `input.type != WS_NOTE_OFF && input.type != WS_GATE) \|\|` |
| `native/control/provider_bridge.cpp:88` | `if (input.type == WS_NOTE_OFF \|\| input.type == WS_GATE) stop_with_panic();` |
| `native/control/provider_bridge.cpp:93` | `if (input.type == WS_NOTE_OFF \|\| input.type == WS_GATE) stop_with_panic();` |
| `native/control/provider_bridge.cpp:96` | `ws_meter meter{sizeof(ws_meter)};` |
| `native/control/provider_bridge.cpp:97` | `if (ws_engine_get_meter(engine_, &meter) != WS_OK) { stop_generation(); return false; }` |
| `native/control/provider_bridge.cpp:106` | `if (input.type == WS_NOTE_OFF \|\| input.type == WS_GATE) stop_with_panic();` |
| `native/control/provider_bridge.cpp:109` | `ws_event event{sizeof(ws_event), frame, input.node_id, input.type,` |
| `native/control/provider_bridge.cpp:112` | `if (input.type == WS_PARAMETER) {` |
| `native/control/provider_bridge.cpp:115` | `if (old.type == WS_PARAMETER && old.node_id == event.node_id &&` |
| `native/control/provider_bridge.cpp:137` | `ws_meter meter{sizeof(ws_meter)};` |
| `native/control/provider_bridge.cpp:138` | `if (ws_engine_get_meter(engine_, &meter) != WS_OK) { stop_generation(); break; }` |
| `native/control/provider_bridge.cpp:150` | `if (event.type == WS_PARAMETER) {` |
| `native/control/provider_bridge.cpp:153` | `} else if (event.type == WS_NOTE_ON) {` |
| `native/control/provider_bridge.cpp:162` | `const int result = ws_engine_enqueue(engine_, &event);` |
| `native/control/provider_bridge.cpp:163` | `if (result == WS_STATE \|\| ws_engine_generation(engine_) != generation_) {` |
| `native/control/provider_bridge.cpp:178` | `generation_ = ws_engine_generation(engine_);` |
| `native/control/provider_bridge.h:4` | `#include "wirescape/engine.h"` |
| `native/control/provider_bridge.h:38` | `ProviderBridge(ws_engine *engine, Config config) noexcept;` |
| `native/control/provider_bridge.h:50` | `struct Pending { ws_event event; uint64_t serial; };` |
| `native/control/provider_bridge.h:58` | `ws_engine *engine_;` |
| `native/control/app_legacy_fixture.cpp:2` | `#include "wirescape/module.h"` |
| `native/control/app_legacy_fixture.cpp:6` | `static int WS_CALL prepare(void*,const ws_module_config*){return 0;}` |
| `native/control/app_legacy_fixture.cpp:8` | `static void WS_CALL event(void*p,const ws_module_event*e){if(e->type==WS_PARAMETER&&e->parameter_id==7)*static_cast<float*>(p)=e->value;}` |
| `native/control/app_legacy_fixture.cpp:9` | `static void WS_CALL process(void*p,const float*const*,float*const*out,const ws_process_context*c){std::fill_n(out[0],c->frames,*static_cast<float*>(p));}` |
| `native/control/app_legacy_fixture.cpp:10` | `static const ws_port_descriptor output{"out","Out",WS_AUDIO};` |
| `native/control/app_legacy_fixture.cpp:11` | `static const ws_parameter_descriptor parameter{7,"Level",0,1,.25f,""};` |
| `native/control/app_legacy_fixture.cpp:12` | `static const ws_module_descriptor descriptor{sizeof(descriptor),WS_ABI_VERSION,"test.app_legacy","Legacy",0,1,1,nullptr,&output,&parameter,create,destroy,prepare,reset,event,process};` |
| `native/control/app_legacy_fixture.cpp:13` | `WS_EXPORT const ws_module_descriptor* WS_CALL ws_module_entry(void){return &descriptor;}` |
| `native/document/runtime_patch.cpp:29` | `AppEngine* load_runtime_patch(const std::string&bytes,AppEngine*catalog,const ws_engine_config&config,std::string&error,const std::vector<engine2::Tap>*telemetry_taps){` |
| `native/document/runtime_patch.cpp:50` | `std::map<uint32_t,const ws_module_descriptor*> nodes;` |
| `native/document/runtime_patch.cpp:54` | `const ws_module_descriptor *descriptor = nullptr;` |
| `native/document/runtime_patch.h:10` | `const ws_engine_config& config,std::string& error,` |
| `native/engine2/engine2.cpp:4` | `#include "wirescape/module.h"` |
| `native/engine2/engine2.cpp:102` | `const ws_module_descriptor*legacy=nullptr;void*instance=nullptr;` |
| `native/engine2/engine2.cpp:130` | `if(instance){if(legacy)legacy->destroy(instance);else if(d)d->destroy(instance);instance=nullptr;}` |
| `native/engine2/engine2.cpp:145` | `if (!node \|\| node->legacy) return false;` |
| `native/engine2/engine2.cpp:168` | `if (tap.kind == Tap::Param) return !node->legacy && tap.index < node->parameters.size();` |
| `native/engine2/engine2.cpp:243` | `if(n->legacy)n->legacy->reset(n->instance);else n->d->reset(n->instance);` |
| `native/engine2/engine2.cpp:278` | `if(n.legacy){` |
| `native/engine2/engine2.cpp:279` | `n.instance=n.legacy->create(cfg.sample_rate);` |
| `native/engine2/engine2.cpp:280` | `ws_module_config old{sizeof(old),cfg.max_block,cfg.sample_rate,generation.load()};` |
| `native/engine2/engine2.cpp:281` | `if(!n.instance\|\|n.legacy->prepare(n.instance,&old))return fail("ABI1 shim prepare failed");` |
| `native/engine2/engine2.cpp:282` | `for(auto&p:n.state)if(p.requested){ws_module_event e{WS_PARAMETER,p.info.legacy_index,static_cast<float>(ws::to_plain(p.info,p.base.value())),0,0};n.legacy->event(n.instance,&e);}` |
| `native/engine2/engine2.cpp:555` | `const bool direct=!n.loop&&!n.legacy;` |
| `native/engine2/engine2.cpp:572` | `if(!n.legacy)for(const auto*edge:n.signal_edges){const auto&e=*edge;if(e.kind==2?(n.parameters[e.input].flags&WS2_PER_VOICE)!=0:n.inputs[e.input].poly==WS2_POLY)channels=std::max(channels,raw_channels(e));}` |
| `native/engine2/engine2.cpp:595` | `if(!n.legacy)for(uint32_t j=0;j<n.parameters.size();++j){` |
| `native/engine2/engine2.cpp:627` | `else if(n.legacy){` |
| `native/engine2/engine2.cpp:632` | `ws_process_context c{sizeof(c),end-cursor,block_start+start+cursor,generation.load()};` |
| `native/engine2/engine2.cpp:633` | `n.legacy->process(n.instance,n.legacy_in.data(),n.legacy_out.data(),&c);cursor=end;` |
| `native/engine2/engine2.cpp:636` | `ws_module_event old{};old.source_id=e.source_id;old.note_id=static_cast<uint32_t>(e.note_id);old.parameter_id=e.index;old.value=e.value;` |
| `native/engine2/engine2.cpp:637` | `if(e.type==WS2_PARAM){old.type=WS_PARAMETER;if(e.index<n.state.size()){auto&v=n.state[e.index];old.parameter_id=v.info.legacy_index;v.base.jump(ws::to_normal(v.info,e.value));v.requested=true;}}` |
| `native/engine2/engine2.cpp:638` | `else if(e.type==WS2_NOTE_ON){old.type=WS_NOTE_ON;old.value=static_cast<float>(e.key);}` |
| `native/engine2/engine2.cpp:639` | `else if(e.type==WS2_NOTE_OFF\|\|e.type==WS2_NOTE_CHOKE)old.type=WS_NOTE_OFF;` |
| `native/engine2/engine2.cpp:641` | `n.legacy->event(n.instance,&old);` |
| `native/engine2/engine2.cpp:749` | `bool Engine::add_abi1(uint32_t id,const ws_module_descriptor*d){` |
| `native/engine2/engine2.cpp:750` | `auto&p=*p_;if(p.prepared\|\|!id\|\|p.find(id)\|\|p.nodes.size()>=p.cfg.max_nodes\|\|!d\|\|d->struct_size<sizeof(ws_module_descriptor)\|\|d->abi_version!=WS_ABI_VERSION\|\|!d->create\|\|!d->prepare\|\|!d->process\|\|!d->reset\|\|!d->destroy\|\|!d->event)return p.fail("Invalid ABI1` |
| `native/engine2/engine2.cpp:751` | `auto n=std::make_unique<Node>();n->id=id;n->legacy=d;n->legacy_ids.resize(d->parameter_count);` |
| `native/engine2/engine2.cpp:752` | `for(uint32_t i=0;i<d->input_count;++i){auto&v=d->inputs[i];n->inputs.push_back(ws::port(v.id,v.name,v.kind==WS_AUDIO?WS2_AUDIO:WS2_ANY,WS2_FIRST,!std::strcmp(v.id,"gain_cv")?1.f:0.f));}` |
| `native/engine2/engine2.cpp:753` | `for(uint32_t i=0;i<d->output_count;++i){auto&v=d->outputs[i];n->outputs.push_back(ws::port(v.id,v.name,v.kind==WS_AUDIO?WS2_AUDIO:WS2_ANY));}` |
| `native/engine2/engine2.cpp:821` | `if(n->legacy&&n->instance){ws_module_event e{WS_PARAMETER,v.info.legacy_index,plain,0,0};n->legacy->event(n->instance,&e);}return true;` |
| `native/engine2/engine2.cpp:823` | `bool Engine::set_channels(uint32_t node,uint32_t channels){auto*n=p_->find(node);if(!n\|\|channels>p_->cfg.max_channels\|\|(n->legacy&&channels!=1))return false;n->forced_channels=static_cast<int>(channels);return true;}` |
| `native/engine2/engine2.cpp:1015` | `auto*n=p_->find(node);if(!n\|\|n->legacy)return {};` |
| `native/engine2/engine2.cpp:1021` | `auto*n=p_->find(node);if(!n\|\|n->legacy\|\|bytes.size()>1024*1024)return WS2_INVALID;` |
| `native/engine2/engine2.cpp:1036` | `if(!(n->legacy?next.add_abi1(n->id,n->legacy):next.add_node(n->id,n->d,config)))return old.fail("Cannot stage reconfiguration");` |
| `native/engine2/engine2.cpp:1040` | `if(n->legacy&&!fresh.setup(*target))return old.fail("Staged shim prepare failed");` |
| `native/engine2/engine2.cpp:1042` | `auto target=std::make_unique<Node>();target->id=n->id;target->d=n->d;target->legacy=n->legacy;` |
| `native/engine2/engine2.cpp:1076` | `if(!changed->legacy){auto bytes=save_state(node);if(!bytes.empty()){int r=next.load_state(node,bytes);if(r!=WS2_OK&&r!=WS2_UNSUPPORTED)return old.fail("Staged state restore failed");}}` |
| `native/engine2/engine2.cpp:1107` | `bool Engine::rebind_abi1_descriptor(uint32_t node, const ws_module_descriptor *d) {` |
| `native/engine2/engine2.cpp:1109` | `if (!n \|\| !n->legacy \|\| !d \|\| !d->id \|\| std::string_view(n->legacy->id) != d->id \|\|` |
| `native/engine2/engine2.cpp:1110` | `n->legacy->create != d->create \|\| n->legacy->destroy != d->destroy \|\| n->legacy->prepare != d->prepare \|\|` |
| `native/engine2/engine2.cpp:1111` | `n->legacy->process != d->process \|\| n->legacy->event != d->event \|\| n->legacy->input_count != d->input_count \|\|` |
| `native/engine2/engine2.cpp:1112` | `n->legacy->output_count != d->output_count \|\| n->legacy->parameter_count != d->parameter_count)` |
| `native/engine2/engine2.cpp:1114` | `n->legacy = d;` |
| `native/engine2/engine2.cpp:1142` | `if (prior && prior->d == n.d && prior->legacy == n.legacy && prior->config == n.config) {` |
| `native/engine2/engine2.h:8` | `struct ws_module_descriptor;` |
| `native/engine2/engine2.h:56` | `bool add_abi1(uint32_t id,const ws_module_descriptor*);` |
| `native/engine2/engine2.h:100` | `bool rebind_abi1_descriptor(uint32_t node, const ws_module_descriptor *);` |
| `native/include/wirescape/module2.h:43` | `float minimum,maximum,initial; uint32_t legacy_index,taper; float curve,step;` |
| `native/tests2/module_loader.h:3` | `#include "wirescape/module.h"` |
| `native/tests2/module_loader.h:47` | `const ws_module_descriptor*abi1(const std::string&name){auto h=library("ws_"+name);auto entry=reinterpret_cast<ws_module_entry_fn>(symbol(h,"ws_module_entry"));if(!entry)throw std::runtime_error("Missing ABI1 entry");return entry();}` |

### Scheduler shim branch inventory (`native/engine2/engine2.cpp`)

Each row is an actual condition, event translation, ABI1 descriptor callback, or legacy-node ownership branch in the ABI2 scheduler. `legacy_index` stores numeric ABI1 parameter identity in ABI2 `ws2_param` metadata (`native/include/wirescape/module2.h:43`).

| Branch site | Observed ABI1-specific condition/callback |
| --- | --- |
| `native/engine2/engine2.cpp:102` | `const ws_module_descriptor*legacy=nullptr;void*instance=nullptr;` |
| `native/engine2/engine2.cpp:130` | `if(instance){if(legacy)legacy->destroy(instance);else if(d)d->destroy(instance);instance=nullptr;}` |
| `native/engine2/engine2.cpp:145` | `if (!node \|\| node->legacy) return false;` |
| `native/engine2/engine2.cpp:168` | `if (tap.kind == Tap::Param) return !node->legacy && tap.index < node->parameters.size();` |
| `native/engine2/engine2.cpp:243` | `if(n->legacy)n->legacy->reset(n->instance);else n->d->reset(n->instance);` |
| `native/engine2/engine2.cpp:278` | `if(n.legacy){` |
| `native/engine2/engine2.cpp:279` | `n.instance=n.legacy->create(cfg.sample_rate);` |
| `native/engine2/engine2.cpp:281` | `if(!n.instance\|\|n.legacy->prepare(n.instance,&old))return fail("ABI1 shim prepare failed");` |
| `native/engine2/engine2.cpp:282` | `for(auto&p:n.state)if(p.requested){ws_module_event e{WS_PARAMETER,p.info.legacy_index,static_cast<float>(ws::to_plain(p.info,p.base.value())),0,0};n.legacy->event(n.instance,&e);}` |
| `native/engine2/engine2.cpp:555` | `const bool direct=!n.loop&&!n.legacy;` |
| `native/engine2/engine2.cpp:572` | `if(!n.legacy)for(const auto*edge:n.signal_edges){const auto&e=*edge;if(e.kind==2?(n.parameters[e.input].flags&WS2_PER_VOICE)!=0:n.inputs[e.input].poly==WS2_POLY)channels=std::max(channels,raw_channels(e));}` |
| `native/engine2/engine2.cpp:595` | `if(!n.legacy)for(uint32_t j=0;j<n.parameters.size();++j){` |
| `native/engine2/engine2.cpp:627` | `else if(n.legacy){` |
| `native/engine2/engine2.cpp:633` | `n.legacy->process(n.instance,n.legacy_in.data(),n.legacy_out.data(),&c);cursor=end;` |
| `native/engine2/engine2.cpp:637` | `if(e.type==WS2_PARAM){old.type=WS_PARAMETER;if(e.index<n.state.size()){auto&v=n.state[e.index];old.parameter_id=v.info.legacy_index;v.base.jump(ws::to_normal(v.info,e.value));v.requested=true;}}` |
| `native/engine2/engine2.cpp:641` | `n.legacy->event(n.instance,&old);` |
| `native/engine2/engine2.cpp:749` | `bool Engine::add_abi1(uint32_t id,const ws_module_descriptor*d){` |
| `native/engine2/engine2.cpp:751` | `auto n=std::make_unique<Node>();n->id=id;n->legacy=d;n->legacy_ids.resize(d->parameter_count);` |
| `native/engine2/engine2.cpp:821` | `if(n->legacy&&n->instance){ws_module_event e{WS_PARAMETER,v.info.legacy_index,plain,0,0};n->legacy->event(n->instance,&e);}return true;` |
| `native/engine2/engine2.cpp:823` | `bool Engine::set_channels(uint32_t node,uint32_t channels){auto*n=p_->find(node);if(!n\|\|channels>p_->cfg.max_channels\|\|(n->legacy&&channels!=1))return false;n->forced_channels=static_cast<int>(channels);return true;}` |
| `native/engine2/engine2.cpp:1015` | `auto*n=p_->find(node);if(!n\|\|n->legacy)return {};` |
| `native/engine2/engine2.cpp:1021` | `auto*n=p_->find(node);if(!n\|\|n->legacy\|\|bytes.size()>1024*1024)return WS2_INVALID;` |
| `native/engine2/engine2.cpp:1036` | `if(!(n->legacy?next.add_abi1(n->id,n->legacy):next.add_node(n->id,n->d,config)))return old.fail("Cannot stage reconfiguration");` |
| `native/engine2/engine2.cpp:1040` | `if(n->legacy&&!fresh.setup(*target))return old.fail("Staged shim prepare failed");` |
| `native/engine2/engine2.cpp:1042` | `auto target=std::make_unique<Node>();target->id=n->id;target->d=n->d;target->legacy=n->legacy;` |
| `native/engine2/engine2.cpp:1076` | `if(!changed->legacy){auto bytes=save_state(node);if(!bytes.empty()){int r=next.load_state(node,bytes);if(r!=WS2_OK&&r!=WS2_UNSUPPORTED)return old.fail("Staged state restore failed");}}` |
| `native/engine2/engine2.cpp:1107` | `bool Engine::rebind_abi1_descriptor(uint32_t node, const ws_module_descriptor *d) {` |
| `native/engine2/engine2.cpp:1109` | `if (!n \|\| !n->legacy \|\| !d \|\| !d->id \|\| std::string_view(n->legacy->id) != d->id \|\|` |
| `native/engine2/engine2.cpp:1110` | `n->legacy->create != d->create \|\| n->legacy->destroy != d->destroy \|\| n->legacy->prepare != d->prepare \|\|` |
| `native/engine2/engine2.cpp:1111` | `n->legacy->process != d->process \|\| n->legacy->event != d->event \|\| n->legacy->input_count != d->input_count \|\|` |
| `native/engine2/engine2.cpp:1112` | `n->legacy->output_count != d->output_count \|\| n->legacy->parameter_count != d->parameter_count)` |
| `native/engine2/engine2.cpp:1114` | `n->legacy = d;` |
| `native/engine2/engine2.cpp:1142` | `if (prior && prior->d == n.d && prior->legacy == n.legacy && prior->config == n.config) {` |

**Facade/loader identity distinction:** ABI1 v1 libraries live behind a `ws_engine` owner (`native/control/app_engine.cpp:18-19,36,96-99`); metadata for built-in ABI2 modules is projected into ABI1 descriptor structs (`native/control/app_engine.cpp:42-71`) without implying that built-ins are linked ABI1 shared modules. Staged graph replans rebind borrowed ABI1 descriptors (`native/control/app_engine.cpp:111-129`).


<!-- Further source/loader/facade/scheduler/layer/test and full-token use indexes follow. -->
