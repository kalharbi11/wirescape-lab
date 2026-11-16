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

<!-- Further source/loader/facade/scheduler/layer/test and full-token use indexes follow. -->
