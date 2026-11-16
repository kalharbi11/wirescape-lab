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


## Direct ABI1-shaped uses by runtime layer: sidecar, web, CLI, tools and capture

| Source file:line | Observed v1-shaped type, facade call, direct engine-symbol reference or build/capture path |
| --- | --- |
| `native/sidecar/session.cpp:155` | `for (uint32_t i = 0; i < app_engine_module_count(engine); ++i) {` |
| `native/sidecar/session.cpp:156` | `auto *meta = app_engine_module(engine, i);` |
| `native/sidecar/session.cpp:157` | `auto *d = app_engine_native_descriptor(engine, meta->id);` |
| `native/sidecar/session.cpp:264` | `catalogue_(app_engine_create(&config_), app_engine_destroy), engine_(nullptr, app_engine_destroy) {` |
| `native/sidecar/session.cpp:267` | `token_ = std::to_string(random()) + "-" + std::to_string(app_engine_clock_ns());` |
| `native/sidecar/session.cpp:406` | `const int render = app_engine_render_live(live, rows, 2, options_.block, app_engine_clock_ns());` |
| `native/sidecar/session.cpp:408` | `bench_.observe_faults(app_engine_native(live).meter().faults);` |
| `native/sidecar/session.cpp:447` | `ws_engine_config next_config = config_;` |
| `native/sidecar/session.cpp:454` | `app_engine_destroy);` |
| `native/sidecar/session.cpp:457` | `app_engine_prepare_master_fade_in(prepared.get());` |
| `native/sidecar/session.cpp:614` | `auto *d = app_engine_native_descriptor(catalogue_.get(), m.at("module").get<std::string>().c_str());` |
| `native/sidecar/session.cpp:684` | `app_engine_destroy);` |
| `native/sidecar/session.cpp:744` | `app_engine_begin_master_fade_out(active_);` |
| `native/sidecar/session.cpp:750` | `while (!app_engine_master_fade_silent(active_)) {` |
| `native/sidecar/session.cpp:755` | `app_engine_resume_master_fade(active_);` |
| `native/sidecar/session.cpp:760` | `if (app_engine_master_fade_silent(active_)) {` |
| `native/sidecar/session.cpp:761` | `const auto first_fade_ns = app_engine_master_fade_out_started_ns(active_);` |
| `native/sidecar/session.cpp:763` | `app_engine_resume_master_fade(active_);` |
| `native/sidecar/session.cpp:769` | `app_engine_prepare_master_fade_in(candidate.get());` |
| `native/sidecar/session.cpp:772` | `app_engine_panic(active_);` |
| `native/sidecar/session.cpp:774` | `app_engine_resume_master_fade(active_);` |
| `native/sidecar/session.cpp:784` | `app_engine_resume_master_fade(active_);` |
| `native/sidecar/session.cpp:792` | `while (!app_engine_master_fade_in_started(active_)) {` |
| `native/sidecar/session.cpp:800` | `app_engine_prepare_master_fade_in(previous);` |
| `native/sidecar/session.cpp:822` | `while (!app_engine_master_fade_in_started(active_)) {` |
| `native/sidecar/session.cpp:834` | `app_engine_prepare_master_fade_in(active_);` |
| `native/sidecar/session.cpp:921` | `app_engine_panic(active_); // release held notes before replacing DSP state` |
| `native/sidecar/session.cpp:925` | `ws_engine_config next_config = config_;` |
| `native/sidecar/session.cpp:932` | `app_engine_destroy);` |
| `native/sidecar/session.cpp:934` | `app_engine_prepare_master_fade_in(prepared.get());` |
| `native/sidecar/session.cpp:964` | `app_engine_prepare_master_fade_in(active_);` |
| `native/sidecar/session.cpp:1057` | `app_engine_panic(active_);` |
| `native/sidecar/session.cpp:1073` | `auto result = app_engine_native(active_).enqueue(0, integer(m.at("id")), WS2_DIRECT_PORT, event, 0,` |
| `native/sidecar/session.cpp:1076` | `if (type == "noteOff") app_engine_panic(active_);` |
| `native/sidecar/session.cpp:1086` | `auto *d = app_engine_native_descriptor(catalogue_.get(), m.at("module").get<std::string>().c_str());` |
| `native/sidecar/session.cpp:1099` | `auto result = app_engine_native(active_).enqueue(0, id, WS2_DIRECT_PORT, native, 0, engine2::Timing::Immediate);` |
| `native/sidecar/session.cpp:1251` | `if (active_) app_engine_native(active_).refresh_latency();` |
| `native/sidecar/session.cpp:1303` | `ws_meter meter{};` |
| `native/sidecar/session.cpp:1304` | `app_engine_get_meter(active_, &meter);` |
| `native/sidecar/session.cpp:1314` | `const float level = app_engine_channel_peak(active_, static_cast<uint32_t>(channel));` |
| `native/sidecar/session.h:67` | `ws_engine_config config_;` |
| `native/web/web_engine.cpp:70` | `ws_engine_config config{};` |
| `native/web/web_engine.cpp:71` | `Owner catalogue{nullptr, app_engine_destroy}, live{nullptr, app_engine_destroy}, old{nullptr, app_engine_destroy};` |
| `native/web/web_engine.cpp:83` | `auto *d = app_engine_native_descriptor(catalogue.get(), type.c_str());` |
| `native/web/web_engine.cpp:143` | `app_engine_destroy);` |
| `native/web/web_engine.cpp:164` | `app_engine_panic(live.get());` |
| `native/web/web_engine.cpp:184` | `need(app_engine_native(live.get())` |
| `native/web/web_engine.cpp:195` | `if (live) app_engine_panic(live.get());` |
| `native/web/web_engine.cpp:217` | `need(app_engine_native(live.get())` |
| `native/web/web_engine.cpp:271` | `if (live && app_engine_render_channels(live.get(), rows, 2, frames) != WS_OK) {` |
| `native/web/web_engine.cpp:277` | `if (app_engine_render_channels(old.get(), prior, 2, frames) != WS_OK) {` |
| `native/web/web_engine.cpp:305` | `for (uint32_t i = 0; i < app_engine_module_count(engine); ++i) {` |
| `native/web/web_engine.cpp:306` | `auto *meta = app_engine_module(engine, i);` |
| `native/web/web_engine.cpp:307` | `auto *d = app_engine_native_descriptor(engine, meta->id);` |
| `native/web/web_engine.cpp:357` | `w->config = {sizeof(ws_engine_config), sample_rate, 128, 64, 2048};` |
| `native/web/web_engine.cpp:358` | `w->catalogue.reset(app_engine_create(&w->config));` |
| `native/web/web_engine.cpp:401` | `auto &engine = app_engine_native(web->live.get());` |
| `native/cli/main.cpp:17` | `using Engine = std::unique_ptr<AppEngine, decltype(&app_engine_destroy)>;` |
| `native/cli/main.cpp:19` | `ws_engine_config c{sizeof(c), rate, block, 32, 8192};` |
| `native/cli/main.cpp:20` | `Engine e(app_engine_create(&c), app_engine_destroy);` |
| `native/cli/main.cpp:21` | `if (!e \|\| app_engine_build_essentials(e.get(), dir.c_str()))` |
| `native/cli/main.cpp:22` | `throw std::runtime_error(e ? app_engine_error(e.get()) : "Cannot create engine");` |
| `native/cli/main.cpp:27` | `ws_event ev{sizeof(ev), frame, node, type, parameter, value, 1, note, app_engine_generation(e)};` |
| `native/cli/main.cpp:28` | `if (app_engine_enqueue(e, &ev))` |
| `native/cli/main.cpp:68` | `if (app_engine_render(e.get(), buffer.data(), n))` |
| `native/cli/main.cpp:124` | `app_engine_render(e.get(), buffer.data(), block);` |
| `native/cli/main.cpp:138` | `if (app_engine_render(e.get(), buffer.data(), block))` |
| `native/cli/play.cpp:111` | `ws_engine_config config{sizeof(config),double(rate),block,64,2048};` |
| `native/cli/play.cpp:112` | `wirescape::audio::EngineOwner catalog(app_engine_create(&config),app_engine_destroy);` |
| `native/cli/play.cpp:121` | `if(module&&app_engine_load_module(catalog.get(),entry.path().string().c_str())!=WS_OK)throw std::runtime_error("Cannot load ABI1 module: "+name);` |
| `native/cli/play.cpp:123` | `std::string error;wirescape::audio::EngineOwner engine(wirescape::document::load_runtime_patch(bytes,catalog.get(),config,error),app_engine_destroy);` |
| `native/cli/play.cpp:137` | `if(app_engine_render_channels(engine.get(),rows,2,n)!=WS_OK)throw std::runtime_error("Offline render failed");` |
| `native/tools/render/main.cpp:20` | `using App = std::unique_ptr<AppEngine, decltype(&app_engine_destroy)>;` |
| `native/tools/render/main.cpp:98` | `ws_engine_config cfg{sizeof(cfg), double(rate), uint32_t(block), 64, 2048};` |
| `native/tools/render/main.cpp:99` | `App catalog(app_engine_create(&cfg), app_engine_destroy);` |
| `native/tools/render/main.cpp:103` | `app_engine_destroy);` |
| `native/tools/render/main.cpp:113` | `ws_event event{};` |
| `native/tools/render/main.cpp:118` | `event.generation = app_engine_generation(engine.get());` |
| `native/tools/render/main.cpp:140` | `for (uint32_t i = 0; i < app_engine_module_count(engine.get()); ++i) {` |
| `native/tools/render/main.cpp:141` | `const auto *descriptor = app_engine_module(engine.get(), i);` |
| `native/tools/render/main.cpp:144` | `if (parameter == app_engine_parameter_id(engine.get(), module.c_str(), p)) {` |
| `native/tools/render/main.cpp:156` | `need(app_engine_enqueue(engine.get(), &event) == WS_OK,` |
| `native/tools/render/main.cpp:166` | `ws_event late{};` |
| `native/tools/render/main.cpp:171` | `late.generation = app_engine_generation(engine.get());` |
| `native/tools/render/main.cpp:175` | `need(app_engine_enqueue(engine.get(), &late) == WS_OK, "late fixture enqueue failed");` |
| `native/tools/render/main.cpp:177` | `need(app_engine_render_channels(engine.get(), rows, 2, n) == WS_OK,` |
| `native/tools/render/main.cpp:184` | `const auto meter = app_engine_native(engine.get()).meter();` |
| `tools/capture/reference.py:2` | `"""Offline ABI1 rendering of native patch v1; never creates a device stream."""` |
| `tools/capture/run.py:103` | `engine = args.engine or base / ('wirescape_engine.dll' if is_windows() else 'libwirescape_engine.so')` |
| `tools/dev.py:51` | `names = {"wirescape_cli", "wirescape_engine", "wirescape-engine", "native_engine_tests", "native_module_tests", "audio_device_tests", "controller_failure_tests", "native_scale_offset_tests", "native_provider_bridge_tests", "native_lfo_tests", "returned_filter_` |
| `tools/dev.py:565` | `name = "wirescape-engine" + (".exe" if os.name == "nt" else "")` |
| `bench/offline/repo_facts.py:138` | `rules = {'abi1_symbols': re.compile(r'\b(?:ws_engine\|ws_module\|ws_port\|ws_parameter\|ws_engine_config\|ws_module_descriptor)\w*\b'),` |
| `bench/offline/repo_facts.py:194` | `if (base.name != 'native' or p.name == 'wirescape-engine' or 'wirescape_engine' in p.name` |

The sidecar and web rows above use the app facade; a `ws_engine_config`, `ws_event`, `ws_meter`, or projected v1 descriptor is a **type/layout dependency** and does not by itself show a call to `ws_engine_render` on the legacy engine. Direct `ws_engine_*` calls are explicitly distinguished from `app_engine_*` facade calls in the source cells.


## ABI1 test sources and ABI2 comparative/compatibility fixtures

This table covers the source/call locations of the original native ABI1 engine/module/provider/return-filter CTests, plus existing ABI2-vs-ABI1 comparison and shim-focused tests. Test includes and setup lines are evidence of source dependency, not a claim that any device was run.

| Test file:line | Source symbol, fixture call or ABI1 compatibility reference |
| --- | --- |
| `native/tests/engine_tests.cpp:1` | `#include "wirescape/engine.h"` |
| `native/tests/engine_tests.cpp:18` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vco_entry();` |
| `native/tests/engine_tests.cpp:19` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_adsr_entry();` |
| `native/tests/engine_tests.cpp:20` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vca_entry();` |
| `native/tests/engine_tests.cpp:21` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_output_entry();` |
| `native/tests/engine_tests.cpp:41` | `using Engine = std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)>;` |
| `native/tests/engine_tests.cpp:44` | `ws_engine_config c{sizeof(c), rate, block, 32, events};` |
| `native/tests/engine_tests.cpp:45` | `Engine e(ws_engine_create(&c), ws_engine_destroy);` |
| `native/tests/engine_tests.cpp:48` | `check(ws_engine_build_essentials(e.get(), directory.c_str()) == WS_OK, "load Essentials");` |
| `native/tests/engine_tests.cpp:51` | `ws_event ev(ws_engine *e, uint64_t frame, uint32_t node, uint32_t type, float value = 0,` |
| `native/tests/engine_tests.cpp:53` | `return {sizeof(ws_event),       frame, node, type, param, value, source, note,` |
| `native/tests/engine_tests.cpp:54` | `ws_engine_generation(e)};` |
| `native/tests/engine_tests.cpp:56` | `void send(ws_engine *e, ws_event event) { check(ws_engine_enqueue(e, &event) == WS_OK, "enqueue"); }` |
| `native/tests/engine_tests.cpp:71` | `check(ws_engine_render(e.get(), result.data() + i, n) == WS_OK, "partition render");` |
| `native/tests/engine_tests.cpp:87` | `auto d = ws_engine_module(e.get(), 1);` |
| `native/tests/engine_tests.cpp:90` | `ws_module_config config{sizeof(config), 512, rate, 1};` |
| `native/tests/engine_tests.cpp:92` | `ws_module_event on{WS_NOTE_ON, 0, 60, 1, 7};` |
| `native/tests/engine_tests.cpp:99` | `ws_process_context context{sizeof(context), n, pos, 1};` |
| `native/tests/engine_tests.cpp:109` | `ws_module_event stale{WS_NOTE_OFF, 0, 0, 2, 7};` |
| `native/tests/engine_tests.cpp:116` | `ws_module_event off{WS_NOTE_OFF, 0, 0, 1, 7};` |
| `native/tests/engine_tests.cpp:126` | `auto d = ws_engine_module(e.get(), 0);` |
| `native/tests/engine_tests.cpp:128` | `ws_module_config c{sizeof(c), 512, 48000, 1};` |
| `native/tests/engine_tests.cpp:130` | `ws_module_event freq{WS_PARAMETER, 0, 440, 0, 0};` |
| `native/tests/engine_tests.cpp:136` | `ws_process_context context{sizeof(context), n, pos, 1};` |
| `native/tests/engine_tests.cpp:151` | `ws_engine_config bad{sizeof(bad), std::numeric_limits<double>::quiet_NaN(), 512, 32, 32};` |
| `native/tests/engine_tests.cpp:152` | `check(!ws_engine_create(&bad), "NaN sample rate");` |
| `native/tests/engine_tests.cpp:155` | `check(ws_engine_enqueue(e.get(), &event) == WS_INVALID, "NaN param");` |
| `native/tests/engine_tests.cpp:157` | `check(ws_engine_enqueue(e.get(), &event) == WS_INVALID, "range param");` |
| `native/tests/engine_tests.cpp:160` | `check(ws_engine_enqueue(e.get(), &event) == WS_NOT_FOUND, "unknown parameter");` |
| `native/tests/engine_tests.cpp:163` | `check(ws_engine_enqueue(e.get(), &event) == WS_NOT_FOUND, "unknown node");` |
| `native/tests/engine_tests.cpp:166` | `check(ws_engine_enqueue(e.get(), &event) == WS_INVALID, "unordered events");` |
| `native/tests/engine_tests.cpp:167` | `check(ws_engine_add_node(e.get(), 5, "essentials.vco") == WS_STATE, "prepared graph immutable");` |
| `native/tests/engine_tests.cpp:169` | `check(ws_engine_render(e.get(), output, 513) == WS_INVALID, "oversized block");` |
| `native/tests/engine_tests.cpp:170` | `check(ws_engine_render(e.get(), output, 0) == WS_INVALID, "zero block");` |
| `native/tests/engine_tests.cpp:171` | `check(ws_engine_reset(e.get()) == WS_OK, "reset");` |
| `native/tests/engine_tests.cpp:172` | `check(ws_engine_enqueue(e.get(), &event) == WS_STATE, "stale generation");` |
| `native/tests/engine_tests.cpp:178` | `check(ws_engine_register_module(e.get(), ws_engine_module(donor.get(), i)) == WS_OK,` |
| `native/tests/engine_tests.cpp:180` | `check(ws_engine_add_node(e.get(), 1, "essentials.vca") == WS_OK, "add node");` |
| `native/tests/engine_tests.cpp:181` | `check(ws_engine_add_node(e.get(), 1, "essentials.vca") == WS_INVALID, "duplicate id");` |
| `native/tests/engine_tests.cpp:182` | `check(ws_engine_add_node(e.get(), 2, "essentials.vca") == WS_OK, "add second");` |
| `native/tests/engine_tests.cpp:183` | `check(ws_engine_add_node(e.get(), 3, "essentials.vco") == WS_OK, "add VCO");` |
| `native/tests/engine_tests.cpp:184` | `check(ws_engine_connect(e.get(), 99, 0, 1, 0) == WS_NOT_FOUND, "bad graph id");` |
| `native/tests/engine_tests.cpp:185` | `check(ws_engine_connect(e.get(), 3, 0, 1, 1) == WS_GRAPH, "bad port kind");` |
| `native/tests/engine_tests.cpp:186` | `check(ws_engine_connect(e.get(), 1, 0, 2, 0) == WS_OK, "edge1");` |
| `native/tests/engine_tests.cpp:187` | `check(ws_engine_connect(e.get(), 2, 0, 1, 0) == WS_OK, "edge2");` |
| `native/tests/engine_tests.cpp:188` | `check(ws_engine_prepare(e.get(), 2, 0) == WS_GRAPH, "cycle reject");` |
| `native/tests/engine_tests.cpp:195` | `check(ws_engine_enqueue(e.get(), &event) == WS_CAPACITY, "bounded queue");` |
| `native/tests/engine_tests.cpp:196` | `check(ws_engine_panic(e.get()) == WS_OK, "panic while full");` |
| `native/tests/engine_tests.cpp:198` | `check(ws_engine_render(e.get(), buffer, 512) == WS_OK, "panic render");` |
| `native/tests/engine_tests.cpp:202` | `check(ws_engine_render(e.get(), buffer, 512) == WS_OK, "postpanic render");` |
| `native/tests/engine_tests.cpp:204` | `check(ws_engine_deactivate(e.get()) == WS_OK, "deactivate");` |
| `native/tests/engine_tests.cpp:205` | `check(ws_engine_render(e.get(), buffer, 512) == WS_OK, "inactive render");` |
| `native/tests/engine_tests.cpp:207` | `check(ws_engine_activate(e.get()) == WS_OK, "activate");` |
| `native/tests/engine_tests.cpp:208` | `check(ws_engine_reset(e.get()) == WS_OK, "lifecycle reset");` |
| `native/tests/engine_tests.cpp:209` | `ws_meter meter{};` |
| `native/tests/engine_tests.cpp:211` | `check(ws_engine_get_meter(e.get(), &meter) == WS_OK && meter.frame_position == 0 &&` |
| `native/tests/engine_tests.cpp:217` | `const ws_module_descriptor *descriptors[] = {ws_test_vco_entry(), ws_test_adsr_entry(),` |
| `native/tests/engine_tests.cpp:218` | `ws_test_vca_entry(), ws_test_output_entry()};` |
| `native/tests/engine_tests.cpp:220` | `check(ws_engine_register_module(e.get(), descriptors[i]) == WS_OK, "instrumented registry");` |
| `native/tests/engine_tests.cpp:221` | `check(ws_engine_add_node(e.get(), i + 1, descriptors[i]->id) == WS_OK, "instrumented node");` |
| `native/tests/engine_tests.cpp:223` | `check(ws_engine_connect(e.get(), 1, 0, 3, 0) == WS_OK &&` |
| `native/tests/engine_tests.cpp:224` | `ws_engine_connect(e.get(), 2, 0, 3, 1) == WS_OK &&` |
| `native/tests/engine_tests.cpp:225` | `ws_engine_connect(e.get(), 3, 0, 4, 0) == WS_OK &&` |
| `native/tests/engine_tests.cpp:226` | `ws_engine_prepare(e.get(), 4, 0) == WS_OK,` |
| `native/tests/engine_tests.cpp:239` | `ws_engine_render(e.get(), buffer, 512);` |
| `native/tests/engine_tests.cpp:248` | `auto generation = ws_engine_generation(e.get());` |
| `native/tests/engine_tests.cpp:249` | `check(ws_engine_render(e.get(), buffer, 512) == WS_CAPACITY, "event work budget");` |
| `native/tests/engine_tests.cpp:251` | `ws_meter meter{}; meter.struct_size = sizeof(meter); ws_engine_get_meter(e.get(), &meter);` |
| `native/tests/engine_tests.cpp:254` | `check(ws_engine_render(e.get(), buffer, 512) == WS_OK, "overload recovery");` |
| `native/tests/engine_tests.cpp:258` | `check(ws_engine_render(e.get(), buffer, 512) == WS_CAPACITY, "graph subdivision budget");` |
| `native/tests/engine_tests.cpp:269` | `while ((result = ws_engine_enqueue(e.get(), &event)) == WS_CAPACITY && !stop.load()) {` |
| `native/tests/engine_tests.cpp:282` | `if (ws_engine_render(e.get(), buffer, 32) != WS_OK) { render_ok = false; stop.store(true); }` |
| `native/tests/engine_tests.cpp:291` | `ws_parameter_descriptor parameters[64];` |
| `native/tests/engine_tests.cpp:293` | `auto descriptor = *ws_test_vca_entry(); descriptor.id = "test.many_parameters";` |
| `native/tests/engine_tests.cpp:295` | `ws_engine_config config{sizeof(config), 48000, 512, 64, 128};` |
| `native/tests/engine_tests.cpp:296` | `Engine e(ws_engine_create(&config), ws_engine_destroy);` |
| `native/tests/engine_tests.cpp:297` | `check(ws_engine_register_module(e.get(), &descriptor) == WS_OK, "setup descriptor");` |
| `native/tests/engine_tests.cpp:299` | `check(ws_engine_add_node(e.get(), node, descriptor.id) == WS_OK, "setup node");` |
| `native/tests/engine_tests.cpp:300` | `check(ws_engine_prepare(e.get(), 64, 0) == WS_OK, "setup prepare");` |
| `native/tests/engine_tests.cpp:303` | `check(ws_engine_initialize_parameter(e.get(), node, parameter, .5f) == WS_OK, "4096 initial parameters bypass live queue");` |
| `native/tests/engine_tests.cpp:304` | `check(ws_engine_initialize_parameter(e.get(), 1, 0, 3) == WS_INVALID, "setup range");` |
| `native/tests/engine_tests.cpp:305` | `check(ws_engine_initialize_parameter(e.get(), 1, 999, 1) == WS_NOT_FOUND, "setup unknown parameter");` |
| `native/tests/engine_tests.cpp:306` | `ws_meter meter{}; meter.struct_size = sizeof(meter); ws_engine_get_meter(e.get(), &meter);` |
| `native/tests/engine_tests.cpp:309` | `check(ws_engine_initialize_parameter(e.get(), 1, 0, 1) == WS_STATE, "queued traffic rejects setup");` |
| `native/tests/engine_tests.cpp:310` | `float buffer[512]; check(ws_engine_render(e.get(), buffer, 512) == WS_OK, "large setup renders");` |
| `native/tests/engine_tests.cpp:311` | `check(ws_engine_initialize_parameter(e.get(), 1, 0, 1) == WS_STATE, "rendered graph rejects setup");` |
| `native/tests/engine_tests.cpp:312` | `check(ws_engine_reset(e.get()) == WS_OK && ws_engine_initialize_parameter(e.get(), 1, 0, 1) == WS_OK, "quiescent reset permits setup");` |
| `native/tests/engine_tests.cpp:316` | `check(ws_engine_render(voice.get(), buffer, 512) == (count == 256 ? WS_OK : WS_CAPACITY), "exact dispatch boundary");` |
| `native/tests/engine_tests.cpp:321` | `check(ws_engine_render(voice.get(), buffer, 512) == (count == 64 ? WS_OK : WS_CAPACITY), "exact graph span boundary");` |
| `native/tests/golden_render.cpp:183` | `ws_engine_config cfg{sizeof(cfg), 48000, 128, 128, 2048};` |
| `native/tests/lfo_tests.cpp:1` | `#include "wirescape/engine.h"` |
| `native/tests/lfo_tests.cpp:11` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_lfo_entry();` |
| `native/tests/lfo_tests.cpp:12` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vco_entry();` |
| `native/tests/lfo_tests.cpp:13` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vca_entry();` |
| `native/tests/lfo_tests.cpp:14` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_output_entry();` |
| `native/tests/lfo_tests.cpp:18` | `using Engine = std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)>;` |
| `native/tests/lfo_tests.cpp:20` | `static void send(const ws_module_descriptor *d, void *s, uint32_t id, float value) {` |
| `native/tests/lfo_tests.cpp:21` | `ws_module_event e{WS_PARAMETER, 0, 0, 0, 0};` |
| `native/tests/lfo_tests.cpp:24` | `static std::vector<float> render(const ws_module_descriptor *d, void *s, uint32_t frames,` |
| `native/tests/lfo_tests.cpp:30` | `ws_process_context c{sizeof(c), n, pos, 1};` |
| `native/tests/lfo_tests.cpp:38` | `const auto *d = ws_test_lfo_entry();` |
| `native/tests/lfo_tests.cpp:40` | `d->abi_version == WS_ABI_VERSION && d->input_count == 0 &&` |
| `native/tests/lfo_tests.cpp:50` | `ws_module_config config{sizeof(config), 512, 48000, 1};` |
| `native/tests/lfo_tests.cpp:53` | `float *out[] = {guarded + 1}; ws_process_context c{sizeof(c), 0, 0, 1};` |
| `native/tests/lfo_tests.cpp:76` | `const auto *d = ws_test_lfo_entry(); void *s = d->create(rate);` |
| `native/tests/lfo_tests.cpp:77` | `ws_module_config cfg{sizeof(cfg), 512, rate, 1}; d->prepare(s, &cfg);` |
| `native/tests/lfo_tests.cpp:83` | `const auto *d = ws_test_lfo_entry(); void *s = d->create(rate);` |
| `native/tests/lfo_tests.cpp:84` | `ws_module_config cfg{sizeof(cfg), 512, rate, 1}; d->prepare(s, &cfg);` |
| `native/tests/lfo_tests.cpp:92` | `ws_engine_config cfg{sizeof(cfg), 48000, 128, 8, 64};` |
| `native/tests/lfo_tests.cpp:93` | `Engine engine(ws_engine_create(&cfg), ws_engine_destroy);` |
| `native/tests/lfo_tests.cpp:94` | `for (auto d : {ws_test_vco_entry(), ws_test_vca_entry(), ws_test_output_entry()})` |
| `native/tests/lfo_tests.cpp:95` | `require(ws_engine_register_module(engine.get(), d) == WS_OK, "register graph module");` |
| `native/tests/lfo_tests.cpp:101` | `require(ws_engine_load_module(engine.get(), path.c_str()) == WS_OK, "load LFO DLL");` |
| `native/tests/lfo_tests.cpp:102` | `require(ws_engine_add_node(engine.get(), 1, "essentials.vco") == 0 &&` |
| `native/tests/lfo_tests.cpp:103` | `ws_engine_add_node(engine.get(), 2, "essentials.lfo") == 0 &&` |
| `native/tests/lfo_tests.cpp:104` | `ws_engine_add_node(engine.get(), 3, "essentials.vca") == 0 &&` |
| `native/tests/lfo_tests.cpp:105` | `ws_engine_add_node(engine.get(), 4, "essentials.output") == 0, "LFO graph nodes");` |
| `native/tests/lfo_tests.cpp:106` | `require(ws_engine_connect(engine.get(), 1, 0, 3, 0) == 0 &&` |
| `native/tests/lfo_tests.cpp:107` | `ws_engine_connect(engine.get(), 2, 0, 3, 1) == 0 &&` |
| `native/tests/lfo_tests.cpp:108` | `ws_engine_connect(engine.get(), 3, 0, 4, 0) == 0 &&` |
| `native/tests/lfo_tests.cpp:109` | `ws_engine_prepare(engine.get(), 4, 0) == 0, "LFO to VCA graph routing");` |
| `native/tests/lfo_tests.cpp:113` | `require(ws_engine_render(engine.get(), result.data() + pos, n) == 0, "LFO graph render");` |
| `native/tests/lfo_tests.cpp:137` | `const auto *d = ws_test_lfo_entry(); void *s = d->create(48000);` |
| `native/tests/lfo_tests.cpp:138` | `ws_module_config cfg{sizeof(cfg), 128, 48000, 1}; d->prepare(s, &cfg);` |
| `native/tests/module_tests.cpp:1` | `#include "wirescape/engine.h"` |
| `native/tests/module_tests.cpp:10` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_mixer_entry();` |
| `native/tests/module_tests.cpp:11` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vco_entry();` |
| `native/tests/module_tests.cpp:12` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vca_entry();` |
| `native/tests/module_tests.cpp:13` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_adsr_entry();` |
| `native/tests/module_tests.cpp:15` | `using Engine = std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)>;` |
| `native/tests/module_tests.cpp:17` | `auto d = ws_test_mixer_entry();` |
| `native/tests/module_tests.cpp:18` | `require(!std::strcmp(d->id, "essentials.mixer") && d->abi_version == WS_ABI_VERSION &&` |
| `native/tests/module_tests.cpp:21` | `ws_module_config config{sizeof(config), 16, 48000, 1};` |
| `native/tests/module_tests.cpp:26` | `ws_process_context c{sizeof(c), 5, 0, 1};` |
| `native/tests/module_tests.cpp:32` | `ws_module_event e{WS_PARAMETER, 0, 2, 0, 0}; d->event(s, &e);` |
| `native/tests/module_tests.cpp:45` | `ws_engine_config c{sizeof(c),48000,512,8,64}; Engine e(ws_engine_create(&c),ws_engine_destroy);` |
| `native/tests/module_tests.cpp:46` | `for (auto d : {ws_test_vco_entry()}) require(ws_engine_register_module(e.get(),d)==WS_OK,"register");` |
| `native/tests/module_tests.cpp:55` | `require(ws_engine_load_module(e.get(),path.c_str())==WS_OK,"output DLL");` |
| `native/tests/module_tests.cpp:56` | `require(ws_engine_load_module(e.get(),mixerPath.c_str())==WS_OK,"mixer DLL descriptor");` |
| `native/tests/module_tests.cpp:57` | `require(ws_engine_add_node(e.get(),1,"essentials.vco")==0 && ws_engine_add_node(e.get(),2,"essentials.vco")==0 &&` |
| `native/tests/module_tests.cpp:58` | `ws_engine_add_node(e.get(),3,"essentials.mixer")==0 && ws_engine_add_node(e.get(),4,"essentials.output")==0,"graph nodes");` |
| `native/tests/module_tests.cpp:59` | `require(ws_engine_connect(e.get(),1,0,3,0)==0 && ws_engine_connect(e.get(),2,0,3,1)==0 &&` |
| `native/tests/module_tests.cpp:60` | `ws_engine_connect(e.get(),3,0,4,0)==0 && ws_engine_prepare(e.get(),4,0)==0,"two VCO mixer graph");` |
| `native/tests/module_tests.cpp:61` | `ws_event event{sizeof(event),0,2,WS_PARAMETER,0,330,0,0,ws_engine_generation(e.get())};` |
| `native/tests/module_tests.cpp:62` | `require(ws_engine_enqueue(e.get(),&event)==0,"second pitch");` |
| `native/tests/module_tests.cpp:64` | `require(ws_engine_render(e.get(),output.data()+pos,n)==0,"mixed render");pos+=n;}` |
| `native/tests/module_tests.cpp:69` | `auto d=ws_test_vca_entry(); void *s=d->create(rate);ws_module_config config{sizeof(config),512,rate,1};d->prepare(s,&config);` |
| `native/tests/module_tests.cpp:71` | `ws_process_context c{sizeof(c),1,0,1};d->process(s,in,out,&c);` |
| `native/tests/module_tests.cpp:72` | `ws_module_event event{WS_PARAMETER,0,0,0,0};d->event(s,&event);` |
| `native/tests/module_tests.cpp:76` | `d=ws_test_vco_entry();s=d->create(rate);d->prepare(s,&config);c.frames=1;d->process(s,nullptr,out,&c);` |
| `native/tests/module_tests.cpp:84` | `d=ws_test_mixer_entry();s=d->create(rate);d->prepare(s,&config);` |
| `native/tests/module_tests.cpp:88` | `d=ws_test_adsr_entry();s=d->create(rate);d->prepare(s,&config);` |
| `native/tests/module_tests.cpp:89` | `ws_module_event on{WS_GATE,0,1,1,1};d->event(s,&on);` |
| `native/tests/provider_bridge_tests.cpp:14` | `using Engine = std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)>;` |
| `native/tests/provider_bridge_tests.cpp:18` | `ws_engine_config config{sizeof(config), 48000, 64, 16, events};` |
| `native/tests/provider_bridge_tests.cpp:19` | `Engine engine(ws_engine_create(&config), ws_engine_destroy);` |
| `native/tests/provider_bridge_tests.cpp:21` | `check(ws_engine_build_essentials(engine.get(), modules) == WS_OK, "prepare Essentials");` |
| `native/tests/provider_bridge_tests.cpp:33` | `void direct(ws_engine *e, uint64_t frame, uint32_t node, uint32_t type,` |
| `native/tests/provider_bridge_tests.cpp:35` | `ws_event ev{sizeof(ev), frame, node, type, parameter, value, source, note,` |
| `native/tests/provider_bridge_tests.cpp:36` | `ws_engine_generation(e)};` |
| `native/tests/provider_bridge_tests.cpp:37` | `check(ws_engine_enqueue(e, &ev) == WS_OK, "direct enqueue");` |
| `native/tests/provider_bridge_tests.cpp:39` | `ws_meter meter(ws_engine *e) {` |
| `native/tests/provider_bridge_tests.cpp:40` | `ws_meter m{sizeof(m)};` |
| `native/tests/provider_bridge_tests.cpp:41` | `check(ws_engine_get_meter(e, &m) == WS_OK, "meter");` |
| `native/tests/provider_bridge_tests.cpp:44` | `void render(ws_engine *e) {` |
| `native/tests/provider_bridge_tests.cpp:46` | `check(ws_engine_render(e, samples.data(), 64) == WS_OK, "offline render barrier");` |
| `native/tests/provider_bridge_tests.cpp:74` | `check(ws_engine_render(actual.get(), a.data() + offset, 64) == WS_OK, "bridge render");` |
| `native/tests/provider_bridge_tests.cpp:75` | `check(ws_engine_render(reference.get(), b.data() + offset, 64) == WS_OK, "reference render");` |
| `native/tests/provider_bridge_tests.cpp:108` | `const auto release_gen = ws_engine_generation(release.get());` |
| `native/tests/provider_bridge_tests.cpp:112` | `ws_engine_generation(release.get()) == release_gen + 1,` |
| `native/tests/provider_bridge_tests.cpp:128` | `const auto before = ws_engine_generation(full.get());` |
| `native/tests/provider_bridge_tests.cpp:132` | `check(ws_engine_generation(full.get()) == before + 1 && bounded.counts().loss_panics == 1,` |
| `native/tests/provider_bridge_tests.cpp:135` | `check(ws_engine_generation(full.get()) == before + 1, "no repeated panic");` |
| `native/tests/provider_bridge_tests.cpp:144` | `const auto gen = ws_engine_generation(e.get());` |
| `native/tests/provider_bridge_tests.cpp:148` | `check(ws_engine_generation(e.get()) == gen + 1, "panic increments generation immediately");` |
| `native/tests/provider_bridge_tests.cpp:165` | `check(ws_engine_panic(external.get()) == WS_OK, "external generation change");` |
| `native/tests/provider_bridge_tests.cpp:166` | `const auto changed = ws_engine_generation(external.get());` |
| `native/tests/provider_bridge_tests.cpp:170` | `check(ws_engine_generation(external.get()) == changed, "generation stable after observation");` |
| `native/tests/returned_filter_stress.cpp:3` | `#include "wirescape/engine.h"` |
| `native/tests/returned_filter_stress.cpp:4` | `#include "wirescape/module.h"` |
| `native/tests/returned_filter_stress.cpp:20` | `struct EngineDeleter { void operator()(ws_engine *engine) const { ws_engine_destroy(engine); } };` |
| `native/tests/returned_filter_stress.cpp:22` | `const ws_module_descriptor *descriptor;` |
| `native/tests/returned_filter_stress.cpp:24` | `Processor(const ws_module_descriptor *d, double rate) : descriptor(d) {` |
| `native/tests/returned_filter_stress.cpp:27` | `ws_module_config config{sizeof(config), 512, rate, 1};` |
| `native/tests/returned_filter_stress.cpp:34` | `ws_module_event event{WS_PARAMETER, id, value, 0, 0};` |
| `native/tests/returned_filter_stress.cpp:40` | `ws_process_context context{sizeof(context), frames, position, 1};` |
| `native/tests/returned_filter_stress.cpp:50` | `void impulse_cases(const ws_module_descriptor *d, bool vcf, double rate) {` |
| `native/tests/returned_filter_stress.cpp:98` | `void modulation_case(const ws_module_descriptor *d, bool vcf, double rate) {` |
| `native/tests/returned_filter_stress.cpp:157` | `void run_module(ws_engine *loader, const char *id, bool vcf) {` |
| `native/tests/returned_filter_stress.cpp:158` | `const ws_module_descriptor *d = nullptr;` |
| `native/tests/returned_filter_stress.cpp:159` | `for (uint32_t i = 0; i < ws_engine_module_count(loader); ++i) {` |
| `native/tests/returned_filter_stress.cpp:160` | `const auto *candidate = ws_engine_module(loader, i);` |
| `native/tests/returned_filter_stress.cpp:164` | `require(d->struct_size >= sizeof(ws_module_descriptor) && d->abi_version == WS_ABI_VERSION,` |
| `native/tests/returned_filter_stress.cpp:178` | `ws_engine_config config{sizeof(config), 48000.0, 512, 8, 64};` |
| `native/tests/returned_filter_stress.cpp:179` | `std::unique_ptr<ws_engine, EngineDeleter> engine(ws_engine_create(&config));` |
| `native/tests/returned_filter_stress.cpp:191` | `require(ws_engine_load_module(engine.get(), library.c_str()) == WS_OK,` |
| `native/tests/scale_offset_tests.cpp:1` | `#include "wirescape/engine.h"` |
| `native/tests/scale_offset_tests.cpp:11` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_scale_offset_entry();` |
| `native/tests/scale_offset_tests.cpp:12` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vco_entry();` |
| `native/tests/scale_offset_tests.cpp:13` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_adsr_entry();` |
| `native/tests/scale_offset_tests.cpp:14` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_vca_entry();` |
| `native/tests/scale_offset_tests.cpp:15` | `extern "C" const ws_module_descriptor *WS_CALL ws_test_output_entry();` |
| `native/tests/scale_offset_tests.cpp:20` | `using Engine = std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)>;` |
| `native/tests/scale_offset_tests.cpp:23` | `const auto *d = ws_test_scale_offset_entry();` |
| `native/tests/scale_offset_tests.cpp:25` | `!std::strcmp(d->name, "Scale/Offset") && d->abi_version == WS_ABI_VERSION &&` |
| `native/tests/scale_offset_tests.cpp:37` | `ws_module_config config{sizeof(config), 32, 48000, 1};` |
| `native/tests/scale_offset_tests.cpp:44` | `ws_process_context context{sizeof(context), 6, 0, 1};` |
| `native/tests/scale_offset_tests.cpp:49` | `ws_module_event event{WS_PARAMETER, 0, 0, 0, 0};` |
| `native/tests/scale_offset_tests.cpp:67` | `static std::vector<float> ramped(const ws_module_descriptor *d, double rate, uint32_t block) {` |
| `native/tests/scale_offset_tests.cpp:69` | `ws_module_config config{sizeof(config), 512, rate, 1};` |
| `native/tests/scale_offset_tests.cpp:74` | `ws_process_context context{sizeof(context), 1, 0, 1};` |
| `native/tests/scale_offset_tests.cpp:76` | `ws_module_event event{WS_PARAMETER, 0, 0, 0, 0};` |
| `native/tests/scale_offset_tests.cpp:94` | `ws_engine_config config{sizeof(config), 48000, 512, 8, 64};` |
| `native/tests/scale_offset_tests.cpp:95` | `Engine engine(ws_engine_create(&config), ws_engine_destroy);` |
| `native/tests/scale_offset_tests.cpp:96` | `for (auto d : {ws_test_vco_entry(), ws_test_adsr_entry(), ws_test_vca_entry(), ws_test_output_entry()})` |
| `native/tests/scale_offset_tests.cpp:97` | `require(ws_engine_register_module(engine.get(), d) == WS_OK, "register graph module");` |
| `native/tests/scale_offset_tests.cpp:103` | `require(ws_engine_load_module(engine.get(), path.c_str()) == WS_OK, "load scale/offset DLL");` |
| `native/tests/scale_offset_tests.cpp:105` | `require(ws_engine_add_node(engine.get(), 1, "essentials.vco") == 0 &&` |
| `native/tests/scale_offset_tests.cpp:106` | `ws_engine_add_node(engine.get(), 2, "essentials.adsr") == 0 &&` |
| `native/tests/scale_offset_tests.cpp:107` | `(!directEnvelope ? ws_engine_add_node(engine.get(), 3, "essentials.scale_offset") == 0 : true) &&` |
| `native/tests/scale_offset_tests.cpp:108` | `ws_engine_add_node(engine.get(), 4, "essentials.vca") == 0 &&` |
| `native/tests/scale_offset_tests.cpp:109` | `ws_engine_add_node(engine.get(), 5, "essentials.output") == 0, "graph nodes");` |
| `native/tests/scale_offset_tests.cpp:111` | `? ws_engine_connect(engine.get(), 2, 0, 4, 1) == 0` |
| `native/tests/scale_offset_tests.cpp:112` | `: ws_engine_connect(engine.get(), 2, 0, 3, 0) == 0 &&` |
| `native/tests/scale_offset_tests.cpp:113` | `ws_engine_connect(engine.get(), 3, 0, 4, 1) == 0;` |
| `native/tests/scale_offset_tests.cpp:114` | `require(ws_engine_connect(engine.get(), 1, 0, 4, 0) == 0 && controlRoute &&` |
| `native/tests/scale_offset_tests.cpp:115` | `ws_engine_connect(engine.get(), 4, 0, 5, 0) == 0 &&` |
| `native/tests/scale_offset_tests.cpp:116` | `ws_engine_prepare(engine.get(), 5, 0) == 0, "ADSR scale/offset VCA routing");` |
| `native/tests/scale_offset_tests.cpp:118` | `ws_event e{sizeof(e), 0, node, WS_PARAMETER, parameter, value, 0, 0,` |
| `native/tests/scale_offset_tests.cpp:119` | `ws_engine_generation(engine.get())};` |
| `native/tests/scale_offset_tests.cpp:120` | `require(ws_engine_enqueue(engine.get(), &e) == 0, "enqueue graph parameter");` |
| `native/tests/scale_offset_tests.cpp:124` | `ws_event gate{sizeof(gate), 0, 2, WS_GATE, 0, 1, 0, 1, ws_engine_generation(engine.get())};` |
| `native/tests/scale_offset_tests.cpp:125` | `require(ws_engine_enqueue(engine.get(), &gate) == 0, "enqueue graph gate");` |
| `native/tests/scale_offset_tests.cpp:129` | `require(ws_engine_render(engine.get(), rendered.data() + position, frames) == 0, "graph render");` |
| `native/tests/scale_offset_tests.cpp:138` | `const auto *scaleOffset = ws_test_scale_offset_entry();` |
| `native/modules/clock/tests.cpp:26` | `#include "wirescape/engine.h"` |
| `native/modules/clock/tests.cpp:27` | `#include "wirescape/module.h"` |
| `native/modules/clock/tests.cpp:47` | `struct EngineDeleter { void operator()(ws_engine *e) const { ws_engine_destroy(e); } };` |
| `native/modules/clock/tests.cpp:49` | `const ws_module_descriptor *d=nullptr;` |
| `native/modules/clock/tests.cpp:51` | `explicit Module(const ws_module_descriptor *desc, double rate, uint32_t maxframes=512):d(desc) {` |
| `native/modules/clock/tests.cpp:53` | `ws_module_config c{sizeof(c),maxframes,rate,1}; check(d->prepare(p,&c)==0,"prepare failed");` |
| `native/modules/clock/tests.cpp:57` | `void reprepare(double rate) { ws_module_config c{sizeof(c),512,rate,2};check(d->prepare(p,&c)==0,"reprepare failed"); }` |
| `native/modules/clock/tests.cpp:58` | `void set(uint32_t id, float v) { ws_module_event e{WS_PARAMETER,id,v,0,0}; d->event(p,&e); }` |
| `native/modules/clock/tests.cpp:61` | `void render(const ws_module_descriptor *d, void *p, const float *input, float *first, float *second,` |
| `native/modules/clock/tests.cpp:64` | `ws_process_context ctx{sizeof(ctx),frames,pos,1};` |
| `native/modules/clock/tests.cpp:67` | `void verify_descriptor(const ws_module_descriptor *d) {` |
| `native/modules/clock/tests.cpp:68` | `check(d && d->struct_size>=sizeof(ws_module_descriptor) && d->abi_version==1,"ABI mismatch");` |
| `native/modules/clock/tests.cpp:90` | `void common_guards(const ws_module_descriptor *d) {` |
| `native/modules/clock/tests.cpp:95` | `ws_process_context ctx{sizeof(ctx),0,0,1};` |
| `native/modules/clock/tests.cpp:105` | `ws_module_config bad{0,0,0,0};` |
| `native/modules/clock/tests.cpp:109` | `ws_module_event ev{WS_PARAMETER,0,std::numeric_limits<float>::quiet_NaN(),0,0};` |
| `native/modules/clock/tests.cpp:132` | `std::vector<float> partition_run(const ws_module_descriptor *d, double rate, uint32_t part) {` |
| `native/modules/clock/tests.cpp:158` | `void partition_tests(const ws_module_descriptor *d) {` |
| `native/modules/clock/tests.cpp:169` | `void reset_instances_and_missing(const ws_module_descriptor *d) {` |
| `native/modules/clock/tests.cpp:191` | `ws_module_event bad{WS_PARAMETER,0,std::numeric_limits<float>::infinity(),0,0};` |
| `native/modules/clock/tests.cpp:199` | `void specific(const ws_module_descriptor *d) {` |
| `native/modules/clock/tests.cpp:271` | `ws_engine_config cfg{sizeof(cfg),48000,512,8,64};` |
| `native/modules/clock/tests.cpp:272` | `std::unique_ptr<ws_engine,EngineDeleter> engine(ws_engine_create(&cfg));` |
| `native/modules/clock/tests.cpp:274` | `check(ws_engine_load_module(engine.get(),argv[1])==WS_OK,"actual offline engine DLL/.so discovery failed");` |
| `native/modules/clock/tests.cpp:275` | `check(ws_engine_module_count(engine.get())==1,"discovery count mismatch");` |
| `native/modules/clock/tests.cpp:276` | `const auto *d=ws_engine_module(engine.get(),0);` |
| `native/modules/function_envelope/tests.cpp:26` | `#include "wirescape/engine.h"` |
| `native/modules/function_envelope/tests.cpp:27` | `#include "wirescape/module.h"` |
| `native/modules/function_envelope/tests.cpp:47` | `struct EngineDeleter { void operator()(ws_engine *e) const { ws_engine_destroy(e); } };` |
| `native/modules/function_envelope/tests.cpp:49` | `const ws_module_descriptor *d=nullptr;` |
| `native/modules/function_envelope/tests.cpp:51` | `explicit Module(const ws_module_descriptor *desc, double rate, uint32_t maxframes=512):d(desc) {` |
| `native/modules/function_envelope/tests.cpp:53` | `ws_module_config c{sizeof(c),maxframes,rate,1}; check(d->prepare(p,&c)==0,"prepare failed");` |
| `native/modules/function_envelope/tests.cpp:57` | `void reprepare(double rate) { ws_module_config c{sizeof(c),512,rate,2};check(d->prepare(p,&c)==0,"reprepare failed"); }` |
| `native/modules/function_envelope/tests.cpp:58` | `void set(uint32_t id, float v) { ws_module_event e{WS_PARAMETER,id,v,0,0}; d->event(p,&e); }` |
| `native/modules/function_envelope/tests.cpp:61` | `void render(const ws_module_descriptor *d, void *p, const float *input, float *first, float *second,` |
| `native/modules/function_envelope/tests.cpp:64` | `ws_process_context ctx{sizeof(ctx),frames,pos,1};` |
| `native/modules/function_envelope/tests.cpp:67` | `void verify_descriptor(const ws_module_descriptor *d) {` |
| `native/modules/function_envelope/tests.cpp:68` | `check(d && d->struct_size>=sizeof(ws_module_descriptor) && d->abi_version==1,"ABI mismatch");` |
| `native/modules/function_envelope/tests.cpp:90` | `void common_guards(const ws_module_descriptor *d) {` |
| `native/modules/function_envelope/tests.cpp:95` | `ws_process_context ctx{sizeof(ctx),0,0,1};` |
| `native/modules/function_envelope/tests.cpp:105` | `ws_module_config bad{0,0,0,0};` |
| `native/modules/function_envelope/tests.cpp:109` | `ws_module_event ev{WS_PARAMETER,0,std::numeric_limits<float>::quiet_NaN(),0,0};` |
| `native/modules/function_envelope/tests.cpp:132` | `std::vector<float> partition_run(const ws_module_descriptor *d, double rate, uint32_t part) {` |
| `native/modules/function_envelope/tests.cpp:158` | `void partition_tests(const ws_module_descriptor *d) {` |
| `native/modules/function_envelope/tests.cpp:169` | `void reset_instances_and_missing(const ws_module_descriptor *d) {` |
| `native/modules/function_envelope/tests.cpp:191` | `ws_module_event bad{WS_PARAMETER,0,std::numeric_limits<float>::infinity(),0,0};` |
| `native/modules/function_envelope/tests.cpp:202` | `void specific(const ws_module_descriptor *d) {` |
| `native/modules/function_envelope/tests.cpp:251` | `ws_engine_config cfg{sizeof(cfg),48000,512,8,64};` |
| `native/modules/function_envelope/tests.cpp:252` | `std::unique_ptr<ws_engine,EngineDeleter> engine(ws_engine_create(&cfg));` |
| `native/modules/function_envelope/tests.cpp:254` | `check(ws_engine_load_module(engine.get(),argv[1])==WS_OK,"actual offline engine DLL/.so discovery failed");` |
| `native/modules/function_envelope/tests.cpp:255` | `check(ws_engine_module_count(engine.get())==1,"discovery count mismatch");` |
| `native/modules/function_envelope/tests.cpp:256` | `const auto *d=ws_engine_module(engine.get(),0);` |
| `native/modules/ladder/tests.cpp:26` | `#include "wirescape/engine.h"` |
| `native/modules/ladder/tests.cpp:27` | `#include "wirescape/module.h"` |
| `native/modules/ladder/tests.cpp:47` | `struct EngineDeleter { void operator()(ws_engine *e) const { ws_engine_destroy(e); } };` |
| `native/modules/ladder/tests.cpp:49` | `const ws_module_descriptor *d=nullptr;` |
| `native/modules/ladder/tests.cpp:51` | `explicit Module(const ws_module_descriptor *desc, double rate, uint32_t maxframes=512):d(desc) {` |
| `native/modules/ladder/tests.cpp:53` | `ws_module_config c{sizeof(c),maxframes,rate,1}; check(d->prepare(p,&c)==0,"prepare failed");` |
| `native/modules/ladder/tests.cpp:57` | `void reprepare(double rate) { ws_module_config c{sizeof(c),512,rate,2};check(d->prepare(p,&c)==0,"reprepare failed"); }` |
| `native/modules/ladder/tests.cpp:58` | `void set(uint32_t id, float v) { ws_module_event e{WS_PARAMETER,id,v,0,0}; d->event(p,&e); }` |
| `native/modules/ladder/tests.cpp:61` | `void render(const ws_module_descriptor *d, void *p, const float *input, float *first, float *second,` |
| `native/modules/ladder/tests.cpp:64` | `ws_process_context ctx{sizeof(ctx),frames,pos,1};` |
| `native/modules/ladder/tests.cpp:67` | `void verify_descriptor(const ws_module_descriptor *d) {` |
| `native/modules/ladder/tests.cpp:68` | `check(d && d->struct_size>=sizeof(ws_module_descriptor) && d->abi_version==1,"ABI mismatch");` |
| `native/modules/ladder/tests.cpp:90` | `void common_guards(const ws_module_descriptor *d) {` |
| `native/modules/ladder/tests.cpp:95` | `ws_process_context ctx{sizeof(ctx),0,0,1};` |
| `native/modules/ladder/tests.cpp:105` | `ws_module_config bad{0,0,0,0};` |
| `native/modules/ladder/tests.cpp:109` | `ws_module_event ev{WS_PARAMETER,0,std::numeric_limits<float>::quiet_NaN(),0,0};` |
| `native/modules/ladder/tests.cpp:132` | `std::vector<float> partition_run(const ws_module_descriptor *d, double rate, uint32_t part) {` |
| `native/modules/ladder/tests.cpp:158` | `void partition_tests(const ws_module_descriptor *d) {` |
| `native/modules/ladder/tests.cpp:169` | `void reset_instances_and_missing(const ws_module_descriptor *d) {` |
| `native/modules/ladder/tests.cpp:191` | `ws_module_event bad{WS_PARAMETER,0,std::numeric_limits<float>::infinity(),0,0};` |
| `native/modules/ladder/tests.cpp:199` | `double response(const ws_module_descriptor *d, double rate, double hz) {` |
| `native/modules/ladder/tests.cpp:211` | `void specific(const ws_module_descriptor *d) {` |
| `native/modules/ladder/tests.cpp:254` | `ws_engine_config cfg{sizeof(cfg),48000,512,8,64};` |
| `native/modules/ladder/tests.cpp:255` | `std::unique_ptr<ws_engine,EngineDeleter> engine(ws_engine_create(&cfg));` |
| `native/modules/ladder/tests.cpp:257` | `check(ws_engine_load_module(engine.get(),argv[1])==WS_OK,"actual offline engine DLL/.so discovery failed");` |
| `native/modules/ladder/tests.cpp:258` | `check(ws_engine_module_count(engine.get())==1,"discovery count mismatch");` |
| `native/modules/ladder/tests.cpp:259` | `const auto *d=ws_engine_module(engine.get(),0);` |
| `native/modules/noise/tests.cpp:26` | `#include "wirescape/engine.h"` |
| `native/modules/noise/tests.cpp:27` | `#include "wirescape/module.h"` |
| `native/modules/noise/tests.cpp:47` | `struct EngineDeleter { void operator()(ws_engine *e) const { ws_engine_destroy(e); } };` |
| `native/modules/noise/tests.cpp:49` | `const ws_module_descriptor *d=nullptr;` |
| `native/modules/noise/tests.cpp:51` | `explicit Module(const ws_module_descriptor *desc, double rate, uint32_t maxframes=512):d(desc) {` |
| `native/modules/noise/tests.cpp:53` | `ws_module_config c{sizeof(c),maxframes,rate,1}; check(d->prepare(p,&c)==0,"prepare failed");` |
| `native/modules/noise/tests.cpp:57` | `void reprepare(double rate) { ws_module_config c{sizeof(c),512,rate,2};check(d->prepare(p,&c)==0,"reprepare failed"); }` |
| `native/modules/noise/tests.cpp:58` | `void set(uint32_t id, float v) { ws_module_event e{WS_PARAMETER,id,v,0,0}; d->event(p,&e); }` |
| `native/modules/noise/tests.cpp:61` | `void render(const ws_module_descriptor *d, void *p, const float *input, float *first, float *second,` |
| `native/modules/noise/tests.cpp:64` | `ws_process_context ctx{sizeof(ctx),frames,pos,1};` |
| `native/modules/noise/tests.cpp:67` | `void verify_descriptor(const ws_module_descriptor *d) {` |
| `native/modules/noise/tests.cpp:68` | `check(d && d->struct_size>=sizeof(ws_module_descriptor) && d->abi_version==1,"ABI mismatch");` |
| `native/modules/noise/tests.cpp:90` | `void common_guards(const ws_module_descriptor *d) {` |
| `native/modules/noise/tests.cpp:95` | `ws_process_context ctx{sizeof(ctx),0,0,1};` |
| `native/modules/noise/tests.cpp:105` | `ws_module_config bad{0,0,0,0};` |
| `native/modules/noise/tests.cpp:109` | `ws_module_event ev{WS_PARAMETER,0,std::numeric_limits<float>::quiet_NaN(),0,0};` |
| `native/modules/noise/tests.cpp:132` | `std::vector<float> partition_run(const ws_module_descriptor *d, double rate, uint32_t part) {` |
| `native/modules/noise/tests.cpp:158` | `void partition_tests(const ws_module_descriptor *d) {` |
| `native/modules/noise/tests.cpp:169` | `void reset_instances_and_missing(const ws_module_descriptor *d) {` |
| `native/modules/noise/tests.cpp:191` | `ws_module_event bad{WS_PARAMETER,0,std::numeric_limits<float>::infinity(),0,0};` |
| `native/modules/noise/tests.cpp:199` | `void specific(const ws_module_descriptor *d) {` |
| `native/modules/noise/tests.cpp:235` | `ws_engine_config cfg{sizeof(cfg),48000,512,8,64};` |
| `native/modules/noise/tests.cpp:236` | `std::unique_ptr<ws_engine,EngineDeleter> engine(ws_engine_create(&cfg));` |
| `native/modules/noise/tests.cpp:238` | `check(ws_engine_load_module(engine.get(),argv[1])==WS_OK,"actual offline engine DLL/.so discovery failed");` |
| `native/modules/noise/tests.cpp:239` | `check(ws_engine_module_count(engine.get())==1,"discovery count mismatch");` |
| `native/modules/noise/tests.cpp:240` | `const auto *d=ws_engine_module(engine.get(),0);` |
| `native/modules/slew/tests.cpp:26` | `#include "wirescape/engine.h"` |
| `native/modules/slew/tests.cpp:27` | `#include "wirescape/module.h"` |
| `native/modules/slew/tests.cpp:47` | `struct EngineDeleter { void operator()(ws_engine *e) const { ws_engine_destroy(e); } };` |
| `native/modules/slew/tests.cpp:49` | `const ws_module_descriptor *d=nullptr;` |
| `native/modules/slew/tests.cpp:51` | `explicit Module(const ws_module_descriptor *desc, double rate, uint32_t maxframes=512):d(desc) {` |
| `native/modules/slew/tests.cpp:53` | `ws_module_config c{sizeof(c),maxframes,rate,1}; check(d->prepare(p,&c)==0,"prepare failed");` |
| `native/modules/slew/tests.cpp:57` | `void reprepare(double rate) { ws_module_config c{sizeof(c),512,rate,2};check(d->prepare(p,&c)==0,"reprepare failed"); }` |
| `native/modules/slew/tests.cpp:58` | `void set(uint32_t id, float v) { ws_module_event e{WS_PARAMETER,id,v,0,0}; d->event(p,&e); }` |
| `native/modules/slew/tests.cpp:61` | `void render(const ws_module_descriptor *d, void *p, const float *input, float *first, float *second,` |
| `native/modules/slew/tests.cpp:64` | `ws_process_context ctx{sizeof(ctx),frames,pos,1};` |
| `native/modules/slew/tests.cpp:67` | `void verify_descriptor(const ws_module_descriptor *d) {` |
| `native/modules/slew/tests.cpp:68` | `check(d && d->struct_size>=sizeof(ws_module_descriptor) && d->abi_version==1,"ABI mismatch");` |
| `native/modules/slew/tests.cpp:90` | `void common_guards(const ws_module_descriptor *d) {` |
| `native/modules/slew/tests.cpp:95` | `ws_process_context ctx{sizeof(ctx),0,0,1};` |
| `native/modules/slew/tests.cpp:105` | `ws_module_config bad{0,0,0,0};` |
| `native/modules/slew/tests.cpp:109` | `ws_module_event ev{WS_PARAMETER,0,std::numeric_limits<float>::quiet_NaN(),0,0};` |
| `native/modules/slew/tests.cpp:132` | `std::vector<float> partition_run(const ws_module_descriptor *d, double rate, uint32_t part) {` |
| `native/modules/slew/tests.cpp:158` | `void partition_tests(const ws_module_descriptor *d) {` |
| `native/modules/slew/tests.cpp:169` | `void reset_instances_and_missing(const ws_module_descriptor *d) {` |
| `native/modules/slew/tests.cpp:191` | `ws_module_event bad{WS_PARAMETER,0,std::numeric_limits<float>::infinity(),0,0};` |
| `native/modules/slew/tests.cpp:199` | `void specific(const ws_module_descriptor *d) {` |
| `native/modules/slew/tests.cpp:240` | `ws_engine_config cfg{sizeof(cfg),48000,512,8,64};` |
| `native/modules/slew/tests.cpp:241` | `std::unique_ptr<ws_engine,EngineDeleter> engine(ws_engine_create(&cfg));` |
| `native/modules/slew/tests.cpp:243` | `check(ws_engine_load_module(engine.get(),argv[1])==WS_OK,"actual offline engine DLL/.so discovery failed");` |
| `native/modules/slew/tests.cpp:244` | `check(ws_engine_module_count(engine.get())==1,"discovery count mismatch");` |
| `native/modules/slew/tests.cpp:245` | `const auto *d=ws_engine_module(engine.get(),0);` |
| `native/modules/vcf/tests.cpp:26` | `#include "wirescape/engine.h"` |
| `native/modules/vcf/tests.cpp:27` | `#include "wirescape/module.h"` |
| `native/modules/vcf/tests.cpp:47` | `struct EngineDeleter { void operator()(ws_engine *e) const { ws_engine_destroy(e); } };` |
| `native/modules/vcf/tests.cpp:49` | `const ws_module_descriptor *d=nullptr;` |
| `native/modules/vcf/tests.cpp:51` | `explicit Module(const ws_module_descriptor *desc, double rate, uint32_t maxframes=512):d(desc) {` |
| `native/modules/vcf/tests.cpp:53` | `ws_module_config c{sizeof(c),maxframes,rate,1}; check(d->prepare(p,&c)==0,"prepare failed");` |
| `native/modules/vcf/tests.cpp:57` | `void reprepare(double rate) { ws_module_config c{sizeof(c),512,rate,2};check(d->prepare(p,&c)==0,"reprepare failed"); }` |
| `native/modules/vcf/tests.cpp:58` | `void set(uint32_t id, float v) { ws_module_event e{WS_PARAMETER,id,v,0,0}; d->event(p,&e); }` |
| `native/modules/vcf/tests.cpp:61` | `void render(const ws_module_descriptor *d, void *p, const float *input, float *first, float *second,` |
| `native/modules/vcf/tests.cpp:64` | `ws_process_context ctx{sizeof(ctx),frames,pos,1};` |
| `native/modules/vcf/tests.cpp:67` | `void verify_descriptor(const ws_module_descriptor *d) {` |
| `native/modules/vcf/tests.cpp:68` | `check(d && d->struct_size>=sizeof(ws_module_descriptor) && d->abi_version==1,"ABI mismatch");` |
| `native/modules/vcf/tests.cpp:90` | `void common_guards(const ws_module_descriptor *d) {` |
| `native/modules/vcf/tests.cpp:95` | `ws_process_context ctx{sizeof(ctx),0,0,1};` |
| `native/modules/vcf/tests.cpp:105` | `ws_module_config bad{0,0,0,0};` |
| `native/modules/vcf/tests.cpp:109` | `ws_module_event ev{WS_PARAMETER,0,std::numeric_limits<float>::quiet_NaN(),0,0};` |
| `native/modules/vcf/tests.cpp:132` | `std::vector<float> partition_run(const ws_module_descriptor *d, double rate, uint32_t part) {` |
| `native/modules/vcf/tests.cpp:158` | `void partition_tests(const ws_module_descriptor *d) {` |
| `native/modules/vcf/tests.cpp:169` | `void reset_instances_and_missing(const ws_module_descriptor *d) {` |
| `native/modules/vcf/tests.cpp:191` | `ws_module_event bad{WS_PARAMETER,0,std::numeric_limits<float>::infinity(),0,0};` |
| `native/modules/vcf/tests.cpp:201` | `double response(const ws_module_descriptor *d, int output_index, double rate, double cutoff, double hz) {` |
| `native/modules/vcf/tests.cpp:216` | `void specific(const ws_module_descriptor *d) {` |
| `native/modules/vcf/tests.cpp:257` | `ws_engine_config cfg{sizeof(cfg),48000,512,8,64};` |
| `native/modules/vcf/tests.cpp:258` | `std::unique_ptr<ws_engine,EngineDeleter> engine(ws_engine_create(&cfg));` |
| `native/modules/vcf/tests.cpp:260` | `check(ws_engine_load_module(engine.get(),argv[1])==WS_OK,"actual offline engine DLL/.so discovery failed");` |
| `native/modules/vcf/tests.cpp:261` | `check(ws_engine_module_count(engine.get())==1,"discovery count mismatch");` |
| `native/modules/vcf/tests.cpp:262` | `const auto *d=ws_engine_module(engine.get(),0);` |
| `native/tests2/abi2_returned_filter_stress.cpp:16` | `static int WS_CALL prepare(void*p,const ws_module_config*){auto&s=*static_cast<Adapter*>(p);auto h=s.host();s.instance=stress_descriptor->create(&h);ws2_config cfg{sizeof(cfg),s.rate,512,1,1,nullptr,0};return s.instance&&stress_descriptor->prepare(s.instance` |
| `native/tests2/abi2_returned_filter_stress.cpp:18` | `static void WS_CALL event(void*p,const ws_module_event*e){if(e->type==WS_PARAMETER&&e->parameter_id<3)static_cast<Adapter*>(p)->values[e->parameter_id]=e->value;}` |
| `native/tests2/abi2_returned_filter_stress.cpp:19` | `static void WS_CALL process(void*p,const float*const*in,float*const*out,const ws_process_context*c){` |
| `native/tests2/integration_tests.cpp:7` | `#include "wirescape/engine.h"` |
| `native/tests2/integration_tests.cpp:40` | `ModuleLoader loader(directory);const char*names[]={"noise","clock","function_envelope","slew","vcf","ladder","vca","output"};const ws_module_descriptor*d[8];for(int i=0;i<8;++i)d[i]=loader.abi1(names[i]);` |
| `native/tests2/integration_tests.cpp:42` | `ws_engine_config oldcfg{sizeof(oldcfg),48000,256,32,1024};std::unique_ptr<ws_engine,decltype(&ws_engine_destroy)>old(ws_engine_create(&oldcfg),ws_engine_destroy);VERIFY(old);Config c;c.max_block=256;Engine e(c);` |
| `native/tests2/integration_tests.cpp:43` | `for(uint32_t i=0;i<8;++i){VERIFY(ws_engine_register_module(old.get(),d[i])==WS_OK);VERIFY(ws_engine_add_node(old.get(),i+1,d[i]->id)==WS_OK);VERIFY(e.add_abi1(i+1,d[i]));}` |
| `native/tests2/integration_tests.cpp:45` | `for(auto&v:cables){VERIFY(ws_engine_connect(old.get(),v[0],v[1],v[2],v[3])==WS_OK);VERIFY(e.connect(v[0],v[1],v[2],v[3]));}` |
| `native/tests2/integration_tests.cpp:46` | `VERIFY(e.output(8,0,0));VERIFY(e.register_producer()==0);VERIFY(ws_engine_prepare(old.get(),8,0)==WS_OK);VERIFY(e.prepare());` |
| `native/tests2/integration_tests.cpp:48` | `for(auto&v:initial){VERIFY(ws_engine_initialize_parameter(old.get(),v.node,v.param,v.value)==WS_OK);VERIFY(e.set_parameter(v.node,v.param,v.value));}` |
| `native/tests2/integration_tests.cpp:49` | `if(scripted){const Init changes[]={{5,0,3000},{7,0,.4f},{2,0,91},{6,0,1500}};uint64_t frame=777;for(auto&v:changes){ws_event o{sizeof(o),frame,v.node,WS_PARAMETER,v.param,v.value,1,1,ws_engine_generation(old.get())};VERIFY(ws_engine_enqueue(old.get(),&o)==WS` |
| `native/tests2/integration_tests.cpp:50` | `std::vector<float>baseline(16384),actual(16384);for(uint32_t pos=0;pos<16384;pos+=256){VERIFY(ws_engine_render(old.get(),baseline.data()+pos,256)==WS_OK);float*out[]={actual.data()+pos};VERIFY(e.render(out,1,256)==WS2_OK);}` |
| `native/tests2/module_tests.cpp:45` | `VERIFY(d->params[i].legacy_index == i);` |
| `native/tests2/module_tests.cpp:197` | `auto f=std::make_unique<DspFixture>(descriptors[m],rate,1);void*state=old->create(rate);VERIFY(state);ws_module_config cfg{sizeof(cfg),256,rate,1};VERIFY(old->prepare(state,&cfg)==0);` |
| `native/tests2/module_tests.cpp:202` | `if(m==3){f->ins[0].flags=WS2_CONSTANT;f->input[0][0][0]=0;f->process.events={sizeof(ws2_event_list),1,&on};ws_module_event e{WS_NOTE_ON,0,60,1,1};old->event(state,&e);}` |
| `native/tests2/module_tests.cpp:204` | `for(uint32_t pos=0;pos<2048;){uint32_t n=std::min(block,2048-pos);ws_process_context context{sizeof(context),n,pos,1};old->process(state,ip,op,&context);f->run(n);` |
| `native/tests2/utility_port_tests.h:14` | `for(uint32_t p=0;p<d->param_count;++p){VERIFY(d->params[p].legacy_index==old->parameters[p].id);VERIFY(d->params[p].initial==old->parameters[p].initial);VERIFY(d->params[p].minimum==old->parameters[p].minimum&&d->params[p].maximum==old->parameters[p].maximum` |
| `native/tests2/utility_port_tests.h:16` | `auto f=std::make_unique<DspFixture>(d,rate,channels);std::vector<void*>states(channels);ws_module_config cfg{sizeof(cfg),256,rate,1};for(auto&state:states){state=old->create(rate);VERIFY(state&&old->prepare(state,&cfg)==0);}` |
| `native/tests2/utility_port_tests.h:22` | `for(uint32_t c=0;c<channels;++c){float result[6][256]{};float*op[6];const float*ip[6];for(int p=0;p<6;++p){op[p]=result[p];ip[p]=pattern==3?nullptr:f->input[p][c];}ws_process_context context{sizeof(context),n,pos,1};old->process(states[c],ip,op,&context);` |

Test-to-target CMake wiring is enumerated in the build section above, including the six `essentials_${module}_tests` instances (`native/CMakeLists.txt:82-88`), direct v1 tests and ABI2 equivalence/benchmark/cost targets linked to `wirescape_engine` (`native/engine2/CMakeLists.txt:60-70,113-114,156-159`).


## Remaining compatibility test, facade-simulator and comparison call sites

These are native tests and integration test sources retaining ABI1 engine configuration/event/metadata compatibility even where the executed engine is ABI2.

| Test file:line | ABI1-shaped type, call or metadata field |
| --- | --- |
| `native/control/app_engine_tests.cpp:19` | `static App make(){ws_engine_config c{sizeof(c),48000,128,32,2048};App e(app_engine_create(&c),app_engine_destroy);check(bool(e),"create app engine");return e;}` |
| `native/control/app_engine_tests.cpp:25` | `check(ids.insert(app_engine_module(source.get(), i)->id).second, "duplicate catalogue module ID");` |
| `native/control/app_engine_tests.cpp:38` | `const ws_module_descriptor *metadata = nullptr;` |
| `native/control/app_engine_tests.cpp:40` | `auto *d = app_engine_module(source.get(), i);` |
| `native/control/app_engine_tests.cpp:61` | `check(app_engine_load_module(source.get(), library) == WS_OK, "load third-party ABI1 shared library");` |
| `native/control/app_engine_tests.cpp:75` | `result = app_engine_render(e.get(), out, 128);` |
| `native/control/app_engine_tests.cpp:80` | `ws_event input{sizeof(input),128,9,WS_PARAMETER,7,.75f,1,0,app_engine_generation(e.get())};` |
| `native/control/app_engine_tests.cpp:81` | `check(app_engine_enqueue(e.get(),&input)==WS_OK,"enqueue ABI1 parameter ID, not array index");` |
| `native/control/app_engine_tests.cpp:82` | `{allocation_watch::Scope watch;result=app_engine_render(e.get(),out,128);allocations+=watch.allocations();}` |
| `native/control/app_engine_tests.cpp:85` | `input.parameter_id=99;check(app_engine_enqueue(e.get(),&input)==WS_INVALID,"unknown parameter refused");` |
| `native/control/app_engine_tests.cpp:104` | `status = app_engine_render(e.get(), samples, 128);` |
| `native/control/app_engine_tests.cpp:127` | `const auto generation = app_engine_generation(e.get());` |
| `native/control/app_engine_tests.cpp:133` | `check(app_engine_generation(e.get()) == generation && live_allocations.load() == 0,` |
| `native/control/app_engine_tests.cpp:140` | `auto e=make();check(app_engine_build_essentials(e.get(),"")==WS_OK,"build app graph");` |
| `native/control/app_engine_tests.cpp:143` | `for(auto node:{1u,2u}){ws_event on{sizeof(on),0,node,WS_NOTE_ON,0,69,1,71,app_engine_generation(e.get())};check(app_engine_enqueue(e.get(),&on)==WS_OK,"host note on");}` |
| `native/control/app_engine_tests.cpp:144` | `for(auto node:{1u,2u}){ws_event off{sizeof(off),4800,node,WS_NOTE_OFF,0,69,1,71,app_engine_generation(e.get())};check(app_engine_enqueue(e.get(),&off)==WS_OK,"host note off");}` |
| `native/control/app_engine_tests.cpp:147` | `{allocation_watch::Scope watch;result=app_engine_render(e.get(),out,count);allocations+=watch.allocations();}` |
| `native/control/app_engine_tests.cpp:157` | `int main(int argc,char**argv){try{check(argc==2,"ABI1 fixture library argument");check(app_engine_create(nullptr)==nullptr,"null configuration refused");shim(argv[1]);host_notes();std::cout<<"PASS app native catalogue, host notes, ABI1 IDs/library lifetime and allo` |
| `native/control/midi_host_tests.cpp:59` | `ws_engine_config config{sizeof(config), 48000, 128, 16, 2048};` |
| `native/control/midi_host_tests.cpp:60` | `std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> engine(app_engine_create(&config), app_engine_destroy);` |
| `native/control/midi_host_tests.cpp:131` | `CHECK(app_engine_render(engine.get(), samples, 128) == WS_OK);` |
| `native/control/midi_host_tests.cpp:143` | `ws_engine_config config{sizeof(config), 48000, 256, 16, 2048};` |
| `native/control/midi_host_tests.cpp:144` | `App e(app_engine_create(&config), app_engine_destroy);` |
| `native/control/midi_host_tests.cpp:204` | `const auto generation = app_engine_generation(engine.get());` |
| `native/control/midi_host_tests.cpp:234` | `CHECK(app_engine_generation(engine.get()) == generation);` |
| `native/control/midi_host_tests.cpp:251` | `CHECK(app_engine_generation(engine.get()) == generation);` |
| `native/document/builtin_source_tests.cpp:40` | `ws_engine_config config{sizeof(config), 48000, 256, 64, 2048};` |
| `native/document/builtin_source_tests.cpp:51` | `result = app_engine_render(engine, out, frames);` |
| `native/document/builtin_source_tests.cpp:123` | `ws_engine_config config{sizeof(config), 48000, 256, 64, 2048};` |
| `native/document/builtin_source_tests.cpp:124` | `Owner catalogue(app_engine_create(&config), app_engine_destroy);` |
| `native/document/class_demo_cc_depth_tests.cpp:145` | `ws_engine_config config{sizeof(config), 48000, 256, 64, 2048};` |
| `native/document/class_demo_cc_depth_tests.cpp:146` | `std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> catalog(app_engine_create(&config),` |
| `native/document/groove_runtime_tests.cpp:63` | `ws_engine_config cfg{sizeof(cfg), rate, 256, 64, 2048};` |
| `native/document/groove_runtime_tests.cpp:79` | `const auto *m = app_engine_module(engine, i);` |
| `native/document/groove_runtime_tests.cpp:89` | `ws_event event{};` |
| `native/document/groove_runtime_tests.cpp:96` | `check(app_engine_enqueue(e, &event) == WS_OK, "existing ingress accepts run command");` |
| `native/document/groove_runtime_tests.cpp:109` | `result = app_engine_render(e, audio.data(), n);` |
| `native/document/groove_runtime_tests.cpp:250` | `status = app_engine_render(e, audio.data(), n);` |
| `native/document/groove_runtime_tests.cpp:1040` | `ws_engine_config cfg{sizeof(cfg), 48000, 256, 64, 2048};` |
| `native/document/groove_runtime_tests.cpp:1041` | `Owner cat(app_engine_create(&cfg), app_engine_destroy);` |
| `native/document/qt_free_patch_coverage_tests.cpp:24` | `Owner load(const std::string &bytes, AppEngine *catalogue, const ws_engine_config &config) {` |
| `native/document/qt_free_patch_coverage_tests.cpp:45` | `status = app_engine_render(graph, samples, 128);` |
| `native/document/qt_free_patch_coverage_tests.cpp:62` | `void serialized_demo_equivalence(AppEngine *catalogue, const ws_engine_config &config,` |
| `native/document/qt_free_patch_coverage_tests.cpp:120` | `using Legacy = std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)>;` |
| `native/document/qt_free_patch_coverage_tests.cpp:121` | `Legacy old(ws_engine_create(&config), ws_engine_destroy);` |
| `native/document/qt_free_patch_coverage_tests.cpp:129` | `require(ws_engine_load_module(old.get(), filename.string().c_str()) == WS_OK, "load ABI1 reference module");` |
| `native/document/qt_free_patch_coverage_tests.cpp:131` | `const auto descriptor = [&](const std::string &type) -> const ws_module_descriptor * {` |
| `native/document/qt_free_patch_coverage_tests.cpp:132` | `for (uint32_t i = 0; i < ws_engine_module_count(old.get()); ++i) {` |
| `native/document/qt_free_patch_coverage_tests.cpp:133` | `const auto *item = ws_engine_module(old.get(), i);` |
| `native/document/qt_free_patch_coverage_tests.cpp:138` | `const auto node = [&](int id) -> const ws_module_descriptor * {` |
| `native/document/qt_free_patch_coverage_tests.cpp:143` | `const auto port = [](const ws_port_descriptor *ports, uint32_t count, const std::string &id) -> uint32_t {` |
| `native/document/qt_free_patch_coverage_tests.cpp:149` | `require(ws_engine_add_node(old.get(), module.at("id").get<uint32_t>(),` |
| `native/document/qt_free_patch_coverage_tests.cpp:157` | `require(ws_engine_connect(old.get(), from,` |
| `native/document/qt_free_patch_coverage_tests.cpp:162` | `require(ws_engine_prepare(old.get(), source.at("outputNode").get<uint32_t>(), 0) == WS_OK,` |
| `native/document/qt_free_patch_coverage_tests.cpp:166` | `require(ws_engine_initialize_parameter(old.get(), module.at("id").get<uint32_t>(),` |
| `native/document/qt_free_patch_coverage_tests.cpp:173` | `require(ws_engine_render(old.get(), baseline, 128) == WS_OK, "ABI1 render");` |
| `native/document/qt_free_patch_coverage_tests.cpp:177` | `a = app_engine_render(from_v1.get(), loaded, 128);` |
| `native/document/qt_free_patch_coverage_tests.cpp:178` | `b = app_engine_render(from_saved_v2.get(), reloaded, 128);` |
| `native/document/qt_free_patch_coverage_tests.cpp:197` | `void keyboard_macro(AppEngine *catalogue, const ws_engine_config &config) {` |
| `native/document/qt_free_patch_coverage_tests.cpp:214` | `const ws_event on{` |
| `native/document/qt_free_patch_coverage_tests.cpp:215` | `sizeof(ws_event), 0, 1, WS_NOTE_ON, 0, static_cast<float>(key), 1, key, app_engine_generation(graph.get())};` |
| `native/document/qt_free_patch_coverage_tests.cpp:216` | `require(app_engine_enqueue(graph.get(), &on) == WS_OK,` |
| `native/document/qt_free_patch_coverage_tests.cpp:235` | `status = app_engine_render(graph.get(), previous, 128);` |
| `native/document/qt_free_patch_coverage_tests.cpp:242` | `void dual_chaos(AppEngine *catalogue, const ws_engine_config &config, const std::filesystem::path &examples) {` |
| `native/document/qt_free_patch_coverage_tests.cpp:249` | `void fake_midi_dual_chaos(AppEngine *catalogue, const ws_engine_config &config, const std::filesystem::path &examples) {` |
| `native/document/qt_free_patch_coverage_tests.cpp:272` | `const ws_engine_config config{sizeof(ws_engine_config), 48000, 128, 64, 2048};` |
| `native/document/qt_free_patch_coverage_tests.cpp:273` | `Owner catalogue(app_engine_create(&config), app_engine_destroy);` |
| `native/document/runtime_patch_tests.cpp:16` | `static void saved_lfo_patch(const char *demo, AppEngine *catalog, const ws_engine_config &cfg) {` |
| `native/document/runtime_patch_tests.cpp:42` | `check(app_engine_render(engine.get(), audio, 128) == WS_OK, "render saved LFO patch");` |
| `native/document/runtime_patch_tests.cpp:59` | `ws_engine_config cfg{sizeof(cfg),48000,128,64,2048};Owner catalog(app_engine_create(&cfg),app_engine_destroy);std::string error;` |
| `native/document/runtime_patch_tests.cpp:81` | `for(int block=0;block<100;++block){int ra,rb;size_t count;{allocation_watch::Scope watch;ra=app_engine_render(v1.get(),a,128);rb=app_engine_render(v2.get(),b,128);count=watch.allocations();}check(ra==WS_OK&&rb==WS_OK&&count==0,"loader callback allocation-free");for` |
| `native/document/runtime_patch_tests.cpp:124` | `check(app_engine_render(ccfirst.get(), stable, 128) == WS_OK &&` |
| `native/document/runtime_patch_tests.cpp:125` | `app_engine_render(ccsecond.get(), stable, 128) == WS_OK && scope.allocations() == 0,` |
| `native/document/ui_patch_conformance.cpp:24` | `ws_engine_config config{sizeof(config), 48000, 256, 64, 2048};` |
| `native/document/ui_patch_conformance.cpp:25` | `Owner catalogue(app_engine_create(&config), app_engine_destroy);` |
| `native/document/ui_patch_conformance.cpp:28` | `auto *descriptor = app_engine_module(catalogue.get(), i);` |
| `native/document/ui_patch_conformance.cpp:41` | `const bool unique_slot = used_legacy_indices.insert(param.legacy_index).second;` |
| `native/document/ui_patch_conformance.cpp:42` | `require(unique_slot, id + ": duplicate legacy_index");` |
| `native/document/ui_patch_conformance.cpp:43` | `require(param.legacy_index == legacy.at(param.id).get<uint32_t>(),` |
| `native/document/ui_patch_conformance.cpp:44` | `id + ": legacy_index differs from UI catalogue");` |
| `native/document/ui_patch_conformance.cpp:45` | `require(descriptor->parameters[p].id == param.legacy_index,` |
| `native/engine2/tests/benchmark.cpp:5` | `#include "wirescape/engine.h"` |
| `native/engine2/tests/benchmark.cpp:27` | `ModuleLoader loader(argv[1]);ws_engine_config c{sizeof(c),48000,block,32,1024};std::unique_ptr<ws_engine,decltype(&ws_engine_destroy)>old(ws_engine_create(&c),ws_engine_destroy);VERIFY(old);` |
| `native/engine2/tests/benchmark.cpp:28` | `const char*names[]={"vco","vcf","vca"};for(uint32_t i=0;i<3;++i){auto*d=loader.abi1(names[i]);VERIFY(ws_engine_register_module(old.get(),d)==0);VERIFY(ws_engine_add_node(old.get(),i+1,d->id)==0);}VERIFY(ws_engine_connect(old.get(),1,0,2,0)==0);VERIFY(ws_engine_conn` |
| `native/engine2/tests/benchmark.cpp:33` | `case 0:return ws_engine_render(old.get(),buffer,block);` |
| `native/engine2/tests/cost_probe.cpp:5` | `#include "wirescape/engine.h"` |
| `native/engine2/tests/cost_probe.cpp:22` | `ws_engine_config c{sizeof(c), 48000, 256, 32, 1024};` |
| `native/engine2/tests/cost_probe.cpp:23` | `std::unique_ptr<ws_engine, decltype(&ws_engine_destroy)> old(ws_engine_create(&c), ws_engine_destroy);` |
| `native/engine2/tests/cost_probe.cpp:28` | `VERIFY(ws_engine_register_module(old.get(), d) == 0);` |
| `native/engine2/tests/cost_probe.cpp:29` | `VERIFY(ws_engine_add_node(old.get(), i + 1, d->id) == 0);` |
| `native/engine2/tests/cost_probe.cpp:31` | `VERIFY(ws_engine_connect(old.get(), 1, 0, 2, 0) == 0);` |
| `native/engine2/tests/cost_probe.cpp:32` | `VERIFY(ws_engine_connect(old.get(), 2, 1, 3, 0) == 0);` |
| `native/engine2/tests/cost_probe.cpp:33` | `VERIFY(ws_engine_prepare(old.get(), 3, 0) == 0);` |
| `native/engine2/tests/cost_probe.cpp:34` | `for (unsigned long i = 0; i < blocks; ++i) VERIFY(ws_engine_render(old.get(), buffer, 256) == 0);` |
| `native/engine2/tests/soak.cpp:92` | `ws_engine_config config{sizeof(config),o.rate,o.block,64,8192};` |
| `native/engine2/tests/soak.cpp:93` | `std::unique_ptr<AppEngine,decltype(&app_engine_destroy)>catalog(app_engine_create(&config),app_engine_destroy);require(bool(catalog));` |
| `native/engine2/tests/soak.cpp:111` | `result = app ? app_engine_render(app.get(), buffer.data(), o.block) : e->render(out, 1, o.block);` |
| `native/io/audio/callback_live_midi_tests.cpp:25` | `ws_engine_config cfg{sizeof(cfg), rate, block, bench ? 64u : 8u, 2048};` |
| `native/io/audio/callback_live_midi_tests.cpp:26` | `App app(app_engine_create(&cfg), app_engine_destroy);` |
| `native/io/audio/stream_lifecycle_tests.cpp:40` | `const ws_engine_config config{sizeof(ws_engine_config), 48000, 128, 16, 2048};` |
| `native/io/audio/stream_lifecycle_tests.cpp:41` | `wirescape::audio::EngineOwner catalogue(app_engine_create(&config), app_engine_destroy);` |
| `native/io/net/graph_tests.cpp:26` | `wirescape::engine2::Timing::Timestamped, app_engine_generation(self.engine));` |
| `native/io/net/graph_tests.cpp:35` | `ws_engine_config config{sizeof(config), 48000, 128, 64, 2048};` |
| `native/io/net/graph_tests.cpp:36` | `std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> catalog(app_engine_create(&config), app_engine_destroy);` |
| `native/sidecar/protocol_unit_tests.cpp:355` | `ws_engine_config config{sizeof(config), 48000, 128, 64, 2048};` |
| `native/sidecar/protocol_unit_tests.cpp:356` | `wirescape::audio::EngineOwner catalogue(app_engine_create(&config), app_engine_destroy);` |
| `native/sidecar/protocol_unit_tests.cpp:367` | `ws_event parameter{};` |
| `native/sidecar/protocol_unit_tests.cpp:371` | `// The native descriptor's stable legacy_index, independent of catalogue order.` |
| `native/sidecar/protocol_unit_tests.cpp:372` | `parameter.parameter_id = app_engine_native_descriptor(engine.get(), "essentials.vco")->params[0].legacy_index;` |
| `native/sidecar/protocol_unit_tests.cpp:373` | `parameter.generation = app_engine_generation(engine.get());` |
| `native/sidecar/protocol_unit_tests.cpp:379` | `okay = okay && app_engine_enqueue(engine.get(), &parameter) == WS_OK;` |
| `native/modules2/quad_vca/tests.cpp:88` | `for (uint32_t p = 0; p < params.size(); ++p) REQUIRE(params[p].legacy_index == p);` |
| `native/modules2/reverb/tests.cpp:156` | `for (uint32_t p = 0; p < reverb::COUNT; ++p) REQUIRE(Reverb::params[p].legacy_index == p);` |
| `native/modules2/midi_to_cv/tests.cpp:296` | `REQUIRE(MidiToCv::params[5].legacy_index == 6);` |
| `native/modules2/midi_to_cv/tests.cpp:297` | `REQUIRE(MidiToCv::params[8].legacy_index == 9);` |


## Legacy document and ABI1-reference fixtures

| Source file:line | Fixture or test reference at pinned commit |
| --- | --- |
| `native/tests/fixtures/legacy_documents/future_patch_v99.json:2` | `"format": "wirescape.patch",` |
| `native/tests/fixtures/legacy_documents/future_patch_v99.json:3` | `"version": 99,` |
| `native/tests/fixtures/legacy_documents/malformed_patch.json:2` | `"format": "wirescape.patch",` |
| `native/tests/fixtures/legacy_documents/malformed_patch.json:3` | `"version": 3,` |
| `native/tests/fixtures/legacy_documents/patch_v1.json:2` | `"format": "wirescape.patch",` |
| `native/tests/fixtures/legacy_documents/patch_v1.json:3` | `"version": 1,` |
| `native/tests/fixtures/legacy_documents/patch_v2.json:2` | `"format": "wirescape.patch",` |
| `native/tests/fixtures/legacy_documents/patch_v2.json:3` | `"version": 2,` |
| `native/tests/fixtures/legacy_documents/patch_v3_unknown.json:2` | `"format": "wirescape.patch",` |
| `native/tests/fixtures/legacy_documents/patch_v3_unknown.json:3` | `"version": 3,` |
| `native/tests/fixtures/legacy_documents/visual_study_v4.json:2` | `"format": "wirescape.visual.study",` |
| `native/tests/fixtures/legacy_documents/visual_study_v4.json:3` | `"version": 4,` |
| `native/tests/fixtures/abi2/manifest.json:3` | `"format": "IEEE float32 WAV, raw engine output before app gain",` |
| `native/tests/fixtures/abi2/manifest.json:6` | `"description": "Six_Essentials_Demo equivalent; one steady and one scripted parameter sequence. Generated by unchanged ABI1 engine and compared bit-for-bit with engine2 ABI1 shim. See native/tests2/integration_tests.cpp.",` |
| `native/examples/Six_Essentials_Demo.json:2` | `"format": "wirescape.native.patch",` |
| `native/examples/Six_Essentials_Demo.json:3` | `"version": 1,` |
| `tools/foundation/tests/test_legacy_fixtures.py:1` | `"""Keep synthetic migration inputs usable without importing the legacy runtime."""` |
| `tools/foundation/tests/test_legacy_fixtures.py:9` | `folder = Path(__file__).resolve().parents[3] / "native/tests/fixtures/legacy_documents"` |
| `tools/foundation/tests/test_legacy_fixtures.py:17` | `self.assertEqual((document["format"], document["version"]), identity)` |
| `tools/foundation/tests/test_reporting.py:168` | `(build/'libwirescape_engine.so').write_bytes(b"engine")` |
| `tools/foundation/tests/test_reporting.py:169` | `(build/'libws_mixer.so').write_bytes(b"module")` |
| `tools/foundation/tests/test_reporting.py:179` | `self.assertIn('libwirescape_engine.so', metadata['binaries'])` |
| `tools/foundation/tests/test_reporting.py:180` | `self.assertIn('libws_mixer.so', metadata['binaries'])` |
| `tools/capture/test_capture.py:123` | `run.main(['--confirm-audio', '--seconds', '20'])` |
| `tools/capture/test_capture.py:139` | `self.assertEqual(run.main(['--confirm-audio']), 1)` |
| `tools/capture/test_capture.py:165` | `result = run.main(['--confirm-audio', '--stimulus', 'tone', '--seconds', '.1', '--native', str(helper)])` |
| `tools/capture/test_capture.py:254` | `module = root / 'module.so'` |
| `tools/capture/test_capture.py:259` | `run.main(['--confirm-audio', '--seconds', '.1', '--engine', str(engine), '--modules', str(root)])` |
| `tools/capture/test_capture.py:262` | `self.assertEqual(set(json.loads(report)['binary_sha256']), {'engine.so', 'module.so'})` |
| `tools/capture/test_capture.py:268` | `external = root.parent / 'private-user-home' / 'module.so'` |
| `tools/capture/test_capture.py:271` | `self.assertEqual(run.report_path(external), 'module.so')` |
| `tools/capture/test_capture.py:272` | `self.assertEqual(run.report_error(OSError(str(external)), [external]), 'module.so')` |
| `tools/capture/test_capture.py:292` | `parser.add_argument('--engine', required=True)` |

## Evidence grouped by runtime layer

The detailed occurrence tables above are the line-by-line source index. The following map identifies the declared interface boundary and representative call lines, without reclassifying ABI2-only clients as an ABI1 dynamic engine call.

| Layer | Exact source-site evidence | Observed reference |
| --- | --- | --- |
| Facade | `native/control/app_engine.h:3`, `native/control/app_engine.cpp:15-19`, `native/control/app_engine.cpp:36`, `native/control/app_engine.cpp:90-101`, `native/control/app_engine.cpp:108-109` | Includes ABI1 header, stores v1 metadata and shared legacy engine library owners, converts or chooses ABI2 descriptor vs ABI1 `add_abi1` |
| Loader/patch | `native/src/engine.cpp:166-178`, `native/tests2/module_loader.h:30-48`, `native/document/runtime_patch.cpp:29`, `native/document/runtime_patch.cpp:48-63`, `native/control/app_legacy_fixture.cpp:10-13` | ABI1 shared-library entry lookup, v1 document config/descriptor bridge, v1 fixture entry |
| Scheduler shim | `native/engine2/engine2.cpp:102-145`, `native/engine2/engine2.cpp:275-283`, `native/engine2/engine2.cpp:627-646`, `native/engine2/engine2.cpp:749-755`, `native/engine2/engine2.cpp:1107-1115` | ABI1 node ownership, create/prepare/callback translation, process/event bridge, descriptor rebind |
| Sidecar | `native/sidecar/session.h:67`, `native/sidecar/session.cpp:447-454`, `native/sidecar/session.cpp:925-934`, `native/sidecar/session.cpp:1303-1304` | ABI1-shaped config and meter around ABI2 facade/session |
| Web | `native/web/CMakeLists.txt:40-45`, `native/web/web_engine.cpp:70-71`, `native/web/web_engine.cpp:357-358` | Static ABI1 `src/engine.cpp` in web_core, `ws_engine_config` for web app facade |
| Tools and CLI | `native/cli/main.cpp:19-28`, `native/tools/render/main.cpp:98-118`, `native/tools/capture/CMakeLists.txt:3-6`, `tools/capture/reference.py:7-25,40-58`, `tools/capture/run.py:94,103` | v1 config/event structs used by facade CLI/render; capture offline test points to ABI1 shared engine file; Python capture/reference source paths indexed above |

### ABI1 offline capture's dynamic C-API bindings

The Python offline reference loader looks up `ws_engine_` + each short function name at runtime, so literal code-token searches for names such as `ws_engine_render` do not list its call sites. The following lines identify its ctypes layout, exported-symbol lookup, function pointer binding, module shared-library discovery and source/reference execution.

| Exact source | Python ABI1 field, bound symbol, module loader or callback call |
| --- | --- |
| `tools/capture/reference.py:2` | `"""Offline ABI1 rendering of native patch v1; never creates a device stream."""` |
| `tools/capture/reference.py:7` | `class Config(C.Structure):` |
| `tools/capture/reference.py:8` | `_fields_ = [('size', C.c_uint32), ('rate', C.c_double), ('block', C.c_uint32),` |
| `tools/capture/reference.py:9` | `('nodes', C.c_uint32), ('events', C.c_uint32)]` |
| `tools/capture/reference.py:12` | `class Event(C.Structure):` |
| `tools/capture/reference.py:13` | `_fields_ = [('size', C.c_uint32), ('frame', C.c_uint64), ('node', C.c_uint32),` |
| `tools/capture/reference.py:14` | `('type', C.c_uint32), ('parameter', C.c_uint32), ('value', C.c_float),` |
| `tools/capture/reference.py:15` | `('source', C.c_uint32), ('note', C.c_uint32), ('generation', C.c_uint64)]` |
| `tools/capture/reference.py:18` | `class Port(C.Structure):` |
| `tools/capture/reference.py:19` | `_fields_ = [('id', C.c_char_p), ('name', C.c_char_p), ('kind', C.c_uint32)]` |
| `tools/capture/reference.py:22` | `class Descriptor(C.Structure):` |
| `tools/capture/reference.py:23` | `_fields_ = [('size', C.c_uint32), ('abi', C.c_uint32), ('id', C.c_char_p), ('name', C.c_char_p),` |
| `tools/capture/reference.py:24` | `('inputs', C.c_uint32), ('outputs', C.c_uint32), ('parameters', C.c_uint32),` |
| `tools/capture/reference.py:25` | `('in_ports', C.POINTER(Port)), ('out_ports', C.POINTER(Port))]` |
| `tools/capture/reference.py:28` | `def tone_patch():` |
| `tools/capture/reference.py:29` | `return dict(format='wirescape.native.patch', version=1, outputNode=2,` |
| `tools/capture/reference.py:35` | `def render(engine, modules, patch, events=(), seconds=2):` |
| `tools/capture/reference.py:36` | `if patch.get('format') != 'wirescape.native.patch' or patch.get('version') != 1:` |
| `tools/capture/reference.py:40` | `lib = C.CDLL(str(Path(engine).resolve()))` |
| `tools/capture/reference.py:41` | `def bind(name, result, *args):` |
| `tools/capture/reference.py:42` | `f = getattr(lib, 'ws_engine_' + name)` |
| `tools/capture/reference.py:45` | `ptr, u32 = C.c_void_p, C.c_uint32` |
| `tools/capture/reference.py:46` | `create = bind('create', ptr, C.POINTER(Config))` |
| `tools/capture/reference.py:47` | `destroy = bind('destroy', None, ptr)` |
| `tools/capture/reference.py:48` | `load = bind('load_module', C.c_int, ptr, C.c_char_p)` |
| `tools/capture/reference.py:49` | `count = bind('module_count', u32, ptr)` |
| `tools/capture/reference.py:50` | `descriptor = bind('module', C.POINTER(Descriptor), ptr, u32)` |
| `tools/capture/reference.py:51` | `add = bind('add_node', C.c_int, ptr, u32, C.c_char_p)` |
| `tools/capture/reference.py:52` | `connect = bind('connect', C.c_int, ptr, u32, u32, u32, u32)` |
| `tools/capture/reference.py:53` | `prepare = bind('prepare', C.c_int, ptr, u32, u32)` |
| `tools/capture/reference.py:54` | `parameter = bind('initialize_parameter', C.c_int, ptr, u32, u32, C.c_float)` |
| `tools/capture/reference.py:55` | `enqueue = bind('enqueue', C.c_int, ptr, C.POINTER(Event))` |
| `tools/capture/reference.py:56` | `generation = bind('generation', C.c_uint64, ptr)` |
| `tools/capture/reference.py:57` | `process = bind('render', C.c_int, ptr, C.POINTER(C.c_float), u32)` |
| `tools/capture/reference.py:58` | `error = bind('error', C.c_char_p, ptr)` |
| `tools/capture/reference.py:59` | `e = create(C.byref(Config(C.sizeof(Config), 48000, 512, 32, 2048)))` |
| `tools/capture/reference.py:69` | `for node in nodes.values():` |
| `tools/capture/reference.py:75` | `candidates = [Path(modules) / name for name in` |
| `tools/capture/reference.py:76` | `(f'ws_{suffix}.dll', f'libws_{suffix}.so', f'libws_{suffix}.dylib')]` |
| `tools/capture/reference.py:80` | `check(load(e, str(file.resolve()).encode('utf-8')))` |
| `tools/capture/reference.py:81` | `d = descriptor(e, count(e) - 1).contents` |
| `tools/capture/reference.py:86` | `check(add(e, node['id'], identity.encode()))` |
| `tools/capture/reference.py:87` | `def port(node, name, output):` |
| `tools/capture/reference.py:88` | `d = loaded[nodes[node]['type']]` |
| `tools/capture/reference.py:89` | `ports, size = (d.out_ports, d.outputs) if output else (d.in_ports, d.inputs)` |
| `tools/capture/reference.py:90` | `return next(i for i in range(size) if ports[i].id.decode() == name)` |
| `tools/capture/reference.py:93` | `check(connect(e, a, port(a, wire['fromPort'], True), b, port(b, wire['toPort'], False)))` |
| `tools/capture/reference.py:94` | `check(prepare(e, patch['outputNode'], 0))` |
| `tools/capture/reference.py:95` | `for node in nodes.values():` |
| `tools/capture/reference.py:96` | `for key, value in node.get('values', {}).items():` |
| `tools/capture/reference.py:97` | `check(parameter(e, node['id'], int(key), float(value)))` |
| `tools/capture/reference.py:99` | `for ev in events:` |
| `tools/capture/reference.py:104` | `value = Event(C.sizeof(Event), frame, ev['node'], ev['type'], ev.get('parameter', 0),` |
| `tools/capture/reference.py:105` | `ev.get('value', 0), ev.get('source', 1), ev.get('note', 1), generation(e))` |
| `tools/capture/reference.py:106` | `check(enqueue(e, C.byref(value)))` |
| `tools/capture/reference.py:107` | `samples, buffer = [], (C.c_float * 512)()` |
| `tools/capture/reference.py:108` | `while len(samples) < round(seconds * 48000):` |
| `tools/capture/reference.py:110` | `check(process(e, buffer, n))` |
| `tools/capture/reference.py:113` | `finally:` |
| `tools/capture/reference.py:114` | `destroy(e)` |

The manual capture runner selects `libwirescape_engine.so` or `wirescape_engine.dll` by default (`tools/capture/run.py:103`); the test target supplies `$<TARGET_FILE:wirescape_engine>` to offline self-tests (`native/tools/capture/CMakeLists.txt:3-6`). No device test was executed during this inventory.


## Literal token search / absence scope

The pinned Git tree is complete (1,184 tracked files, recursive `truncated=false`). File search via GitHub `search/code` scoped to `repo:kalharbi11/wirescape-lab` was performed for `ws_engine_config`, `ws_event`, `ws_meter`, `ws_module_descriptor`, `ws_parameter_descriptor`, `ws_port_descriptor`, `ws_module_config`, `ws_module_event`, `ws_process_context`, `legacy_index`, `WS_ABI_VERSION`, `ws_module_entry_fn`, `wirescape/engine.h`, `wirescape/module.h`, `ws_engine_`, `add_abi1`, `rebind_abi1`, and `wirescape_engine`; matched source files were opened at the pinned SHA and literal matching lines indexed above. Search results are index candidates; file contents, not index snippets, supply the cited line numbers.

Zero-result exact code searches: `ws_param_descriptor` and `ws_legacy` (`repo:kalharbi11/wirescape-lab`), distinct from actual `ws_parameter_descriptor` and `legacy_index`. The source-only scope `apps/**` yielded no direct declarations of the searched ABI1 C structs or `wirescape/engine.h`; `native/web` and the facade own the native ABI1-shaped web boundaries instead (`native/web/CMakeLists.txt:40-45`, `native/web/web_engine.cpp:70`). Test-fixture file paths shown here are literal source documents, not verified ABI1 runtime linkage.

Static inspection does not establish whether a target is built in a given CI configuration, nor runtime execution of devices. Direct target links in CMake are separate from transitive links through `wirescape_app_engine`, `wirescape_runtime_document` and the web static core.

