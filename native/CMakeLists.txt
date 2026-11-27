cmake_minimum_required(VERSION 3.20)
project(WirescapeNative VERSION 1.0.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
# S4: ABI2/AppEngine is the sole engine; old ABI1 modules retired.
add_executable(wirescape_cli ../host/cli/main.cpp)
enable_testing()
add_subdirectory(../host/document document)
find_package(Threads REQUIRED)
# ABI2-only targets and frozen references remain.
add_subdirectory(../engine engine2)
# OB-g5: compile and execute the ADSR Trigger/Hold bit-oracle in hosted CTest.
# Keep this registration outside shared engine/CMakeLists.txt module-writer lanes.
add_subdirectory(../modules/adsr adsr_ob_g5)
# Production ABI2 device-free renderer and behavioral CTests.
add_subdirectory(../tools/render tools/render)

# Offline analysis tests only; real endpoint capture is always a manual command.
add_subdirectory(../tools/capture tools/capture)

# Independent localhost UDP worker; production Session integration follows in OSC B.
add_library(wirescape_osc_service STATIC ../host/net/osc_service.cpp)
target_include_directories(wirescape_osc_service PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../sdk/include ${CMAKE_CURRENT_SOURCE_DIR}/../engine/include ${CMAKE_CURRENT_SOURCE_DIR}/../host/include)
target_link_libraries(wirescape_osc_service PUBLIC Threads::Threads)
if(WIN32)
  target_link_libraries(wirescape_osc_service PUBLIC ws2_32)
endif()
add_executable(abi2_osc_host_service_tests ../host/net/tests.cpp)
target_include_directories(abi2_osc_host_service_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../sdk)
target_link_libraries(abi2_osc_host_service_tests PRIVATE wirescape_osc_service)
add_test(NAME abi2_osc_host_service_tests COMMAND abi2_osc_host_service_tests)
set_tests_properties(abi2_osc_host_service_tests PROPERTIES TIMEOUT 30)

# Offline real engine route: measured worker timestamp, one-block lead and
# no audio-thread allocation. Only binds a loopback ephemeral UDP socket.
add_executable(abi2_osc_graph_ingress_tests ../host/net/graph_tests.cpp ../tests/native/abi2/allocation_watch.cpp)
target_include_directories(abi2_osc_graph_ingress_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../sdk)
target_link_libraries(abi2_osc_graph_ingress_tests PRIVATE
  wirescape_runtime_document wirescape_osc_service nlohmann_json::nlohmann_json)
add_test(NAME abi2_osc_graph_ingress_tests COMMAND abi2_osc_graph_ingress_tests)
set_tests_properties(abi2_osc_graph_ingress_tests PROPERTIES TIMEOUT 30)


# Always compile the two harness translation units for Static ownership coverage.
# This OBJECT library never links or runs libFuzzer in the standard build.
add_library(abi2_osc_fuzz_compile OBJECT ../host/osc/fuzz.cpp)
# Opt-in device-free OSC libFuzzer executables; disabled in normal builds.
option(WIRESCAPE_OSC_FUZZ "Build Clang libFuzzer OSC packet/pattern targets" OFF)
if(WIRESCAPE_OSC_FUZZ)
  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(FATAL_ERROR "WIRESCAPE_OSC_FUZZ requires Clang with libFuzzer")
  endif()
  foreach(kind codec pattern)
    add_executable(abi2_osc_${kind}_fuzz ../host/osc/fuzz.cpp)
    if(kind STREQUAL "pattern")
      target_compile_definitions(abi2_osc_${kind}_fuzz PRIVATE WIRESCAPE_OSC_PATTERN=1)
    endif()
    target_compile_options(abi2_osc_${kind}_fuzz PRIVATE
      -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer)
    target_link_options(abi2_osc_${kind}_fuzz PRIVATE -fsanitize=fuzzer,address,undefined)
  endforeach()
endif()

# Qt-free stdio engine process; no devices without explicit confirmation.
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
# OB-a3 pin 7: real executable load-only paths against disposable v1/v2 files.
# All output is temporary, no native source or fixture write is permitted.
add_test(NAME abi2_ob_a3_soak_no_write COMMAND ${Python3_EXECUTABLE}
  "${PROJECT_SOURCE_DIR}/../tests/native/ob_a3_execution_paths.py" soak
  $<TARGET_FILE:wirescape_soak>
  "${PROJECT_SOURCE_DIR}/../host/examples/Six_Essentials_Demo.json"
  "${PROJECT_SOURCE_DIR}/../host/examples/chaos_two.json")
add_test(NAME abi2_ob_a3_golden_no_write COMMAND ${Python3_EXECUTABLE}
  "${PROJECT_SOURCE_DIR}/../tests/native/ob_a3_execution_paths.py" golden
  $<TARGET_FILE:golden_render>
  "${PROJECT_SOURCE_DIR}/../host/examples/Six_Essentials_Demo.json"
  "${PROJECT_SOURCE_DIR}/../host/examples/chaos_two.json")
set_tests_properties(abi2_ob_a3_soak_no_write abi2_ob_a3_golden_no_write
  PROPERTIES TIMEOUT 180)
execute_process(COMMAND git rev-parse --short=12 HEAD WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
  OUTPUT_VARIABLE engine_sha OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
add_library(wirescape_osc_host STATIC ../engine/control/osc_host.cpp ../engine/control/osc_out_host.cpp)
target_include_directories(wirescape_osc_host PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../engine/control)
target_link_libraries(wirescape_osc_host PUBLIC wirescape_osc_service wirescape_runtime_document
  nlohmann_json::nlohmann_json)
# OB-g8: device-off, bounded 64 x 200 Hz OSC ingress and panic recovery regressions.
# Keep this below bench/io and use the actual Host, service and engine queue.
add_executable(abi2_osc_heavy_ingress_tests ../host/net/heavy_ingress_tests.cpp)
target_include_directories(abi2_osc_heavy_ingress_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../sdk)
target_link_libraries(abi2_osc_heavy_ingress_tests PRIVATE
  wirescape_osc_host wirescape_runtime_document nlohmann_json::nlohmann_json)
add_test(NAME abi2_osc_heavy_ingress_tests COMMAND abi2_osc_heavy_ingress_tests)
add_test(NAME abi2_osc_panic_recovery_tests COMMAND abi2_osc_heavy_ingress_tests panic)
set_tests_properties(abi2_osc_heavy_ingress_tests abi2_osc_panic_recovery_tests PROPERTIES TIMEOUT 30)

add_executable(wirescape_engine_sidecar ../host/sidecar/main.cpp ../host/sidecar/protocol.cpp ../host/sidecar/session.cpp ../host/sidecar/devices.cpp)
set_target_properties(wirescape_engine_sidecar PROPERTIES OUTPUT_NAME wirescape-engine)
# Compile native catalogue categories from the same presentation source as
# tools/gen_ui_catalogue.py. No source-tree lookup is needed at runtime.
set(_sidecar_presentation "${CMAKE_CURRENT_SOURCE_DIR}/../apps/studio/public/catalogue-presentation.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${_sidecar_presentation}")
file(READ "${_sidecar_presentation}" _sidecar_presentation_json)
string(JSON _sidecar_count LENGTH "${_sidecar_presentation_json}" modules)
math(EXPR _sidecar_last "${_sidecar_count} - 1")
set(_sidecar_category_header "// SPDX-License-Identifier: GPL-3.0-only\n#pragma once\n#include <string>\ninline const char *wirescape_sidecar_category(const std::string &id) {\n")
foreach(_i RANGE 0 ${_sidecar_last})
  string(JSON _id GET "${_sidecar_presentation_json}" modules ${_i} id)
  string(JSON _category GET "${_sidecar_presentation_json}" modules ${_i} category)
  string(APPEND _sidecar_category_header "  if (id == \"${_id}\") return \"${_category}\";\n")
endforeach()
string(APPEND _sidecar_category_header "  return \"Native\";\n}\n")
file(GENERATE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/wirescape_sidecar_categories.h"
  CONTENT "${_sidecar_category_header}")
target_include_directories(wirescape_engine_sidecar PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
target_compile_definitions(wirescape_engine_sidecar PRIVATE WIRESCAPE_ENGINE_SHA="${engine_sha}")
target_link_libraries(wirescape_engine_sidecar PRIVATE wirescape_runtime_document wirescape_audio_service
  wirescape_midi_host wirescape_osc_host nlohmann_json::nlohmann_json Threads::Threads)
add_test(NAME abi2_sidecar_protocol_tests COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/protocol_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar> ${PROJECT_SOURCE_DIR}/../host/examples)
set_tests_properties(abi2_sidecar_protocol_tests PROPERTIES TIMEOUT 90)
add_test(NAME abi2_sidecar_apply_graph_tests COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/apply_graph_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar>)
set_tests_properties(abi2_sidecar_apply_graph_tests PROPERTIES TIMEOUT 120)
# OB-a3 pin 7: actual null-audio sidecar v1 loadGraph/applyGraph refusal,
# followed by a valid v2 control, without any source-file write.
add_test(NAME abi2_ob_a3_sidecar_no_write COMMAND ${Python3_EXECUTABLE}
  "${PROJECT_SOURCE_DIR}/../host/sidecar/ob_a3_no_write.py"
  $<TARGET_FILE:wirescape_engine_sidecar>
  "${PROJECT_SOURCE_DIR}/../host/examples/Six_Essentials_Demo.json"
  "${PROJECT_SOURCE_DIR}/../host/examples/chaos_two.json")
set_tests_properties(abi2_ob_a3_sidecar_no_write PROPERTIES TIMEOUT 60)
add_test(NAME abi2_sidecar_capture_tests COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/capture_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar>)
set_tests_properties(abi2_sidecar_capture_tests PROPERTIES TIMEOUT 90)
# A93 uses fixed localhost ports and Linux VmRSS; serialize with other tests.
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  add_test(NAME abi2_sidecar_patch_switch_tests COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/patch_switch_tests.py
    $<TARGET_FILE:wirescape_engine_sidecar>)
  set_tests_properties(abi2_sidecar_patch_switch_tests PROPERTIES TIMEOUT 180 RUN_SERIAL TRUE)
  # Opt-in long diagnostic: ctest -C OBH3Long -R ^ob_h3_patch_switch_1000$ -V.
  # Excluded from normal Release and sanitizer inventories; the 200-switch gate stays mandatory.
  add_test(NAME ob_h3_patch_switch_1000 COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/patch_switch_tests.py
    $<TARGET_FILE:wirescape_engine_sidecar> --switches 1000 CONFIGURATIONS OBH3Long)
  set_tests_properties(ob_h3_patch_switch_1000 PROPERTIES TIMEOUT 600 RUN_SERIAL TRUE)
endif()
add_test(NAME sidecar_golden COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/golden_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar> ${CMAKE_CURRENT_SOURCE_DIR}/../tests/protocol/golden_v0.ndjson)
set_tests_properties(sidecar_golden PROPERTIES TIMEOUT 180)
# P1-e A110: the held-writer graph-commit witness exercises the actual Session.
add_executable(sidecar_protocol_unit_tests ../host/sidecar/protocol_unit_tests.cpp ../host/sidecar/protocol.cpp ../host/sidecar/devices.cpp ../tests/native/abi2/allocation_watch.cpp ../host/sidecar/session.cpp)
target_include_directories(sidecar_protocol_unit_tests PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
target_compile_definitions(sidecar_protocol_unit_tests PRIVATE WIRESCAPE_ENGINE_SHA="${engine_sha}")
target_link_libraries(sidecar_protocol_unit_tests PRIVATE wirescape_runtime_document wirescape_audio_service
  wirescape_midi_host wirescape_osc_host nlohmann_json::nlohmann_json Threads::Threads)
add_test(NAME abi2_sidecar_unit_tests COMMAND sidecar_protocol_unit_tests)
set_tests_properties(abi2_sidecar_unit_tests PROPERTIES TIMEOUT 30)
add_executable(sidecar_audio_recovery_tests ../host/sidecar/audio_recovery_tests.cpp ../host/sidecar/session.cpp ../host/audio/device_identity.cpp
  ../host/sidecar/protocol.cpp ../host/sidecar/devices.cpp)
target_include_directories(sidecar_audio_recovery_tests PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
target_compile_definitions(sidecar_audio_recovery_tests PRIVATE WIRESCAPE_ENGINE_SHA="${engine_sha}")
# Deliberately omit wirescape_audio_service: the test supplies its fake boundary.
target_link_libraries(sidecar_audio_recovery_tests PRIVATE wirescape_runtime_document
  wirescape_midi_host wirescape_osc_host nlohmann_json::nlohmann_json Threads::Threads)
add_test(NAME abi2_sidecar_audio_recovery_tests COMMAND sidecar_audio_recovery_tests)
set_tests_properties(abi2_sidecar_audio_recovery_tests PROPERTIES TIMEOUT 30)

# M1 S0: snapshot the real Session serializer with a test-only fixed token.
# Do NOT add a production token option or change any runtime/protocol source.
# The generated translation unit differs only in that constructor assignment
# and its include resolution from the binary directory.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/session.cpp" _s0_session_source)
set(_s0_random_token "token_ = std::to_string(random()) + \"-\" + std::to_string(app_engine_clock_ns());")
string(FIND "${_s0_session_source}" "${_s0_random_token}" _s0_token_pos)
if(_s0_token_pos LESS 0)
  message(FATAL_ERROR "M1 S0 test-only token seam drifted: cannot freeze the session")
endif()
string(REPLACE "${_s0_random_token}" "token_ = \"s0-fixture-session\";"
  _s0_session_source "${_s0_session_source}")
string(REPLACE "#include \"../document/runtime_module_config.h\""
  "#include \"runtime_module_config.h\"" _s0_session_source "${_s0_session_source}")
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/s0_snapshot_session.cpp" "${_s0_session_source}")
add_executable(sidecar_s0_snapshot_tests
  ../host/sidecar/snapshot_tests.cpp "${CMAKE_CURRENT_BINARY_DIR}/s0_snapshot_session.cpp"
  ../host/sidecar/protocol.cpp ../host/sidecar/devices.cpp)
target_include_directories(sidecar_s0_snapshot_tests PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar" "${CMAKE_CURRENT_SOURCE_DIR}/../host/document"
  "${CMAKE_CURRENT_BINARY_DIR}")
target_compile_definitions(sidecar_s0_snapshot_tests PRIVATE WIRESCAPE_ENGINE_SHA="s0-fixture-build")
target_link_libraries(sidecar_s0_snapshot_tests PRIVATE wirescape_runtime_document wirescape_audio_service
  wirescape_midi_host wirescape_osc_host nlohmann_json::nlohmann_json Threads::Threads)
add_test(NAME abi2_sidecar_snapshot_tests COMMAND sidecar_s0_snapshot_tests
  "${CMAKE_CURRENT_SOURCE_DIR}/../host/sidecar/testdata")
set_tests_properties(abi2_sidecar_snapshot_tests PROPERTIES TIMEOUT 90)
 
# M1 S2: fail closed on ABI1 links, recursively following direct and INTERFACE
# dependencies of the app facade and the production sidecar at configure time.
# Generated link commands on each CI platform remain required acceptance proof.
function(s2_assert_native_only target_name)
  get_property(_checked GLOBAL PROPERTY "S2_NATIVE_LINK_CHECKED_${target_name}")
  if(_checked)
    return()
  endif()
  set_property(GLOBAL PROPERTY "S2_NATIVE_LINK_CHECKED_${target_name}" TRUE)
  get_target_property(_direct "${target_name}" LINK_LIBRARIES)
  get_target_property(_interface "${target_name}" INTERFACE_LINK_LIBRARIES)
  message(STATUS "S2 link audit ${target_name}: direct=${_direct}; interface=${_interface}")
  foreach(_item IN LISTS _direct _interface)
    if(_item MATCHES "(^|[^a-zA-Z0-9_])wirescape_engine($|[^a-zA-Z0-9_])")
      message(FATAL_ERROR "S2 native-only target ${target_name} links ABI1: ${_item}")
    endif()
    if(TARGET "${_item}")
      s2_assert_native_only("${_item}")
    endif()
  endforeach()
endfunction()
s2_assert_native_only(wirescape_app_engine)
s2_assert_native_only(wirescape_engine_sidecar)

# P1-h (#749): watch the actual callback of the statically linked production
# audio service through the existing fake dynamic backend. Test-only target.
add_executable(real_callback_rt_watch_tests
  ../host/audio/real_callback_rt_watch_tests.cpp ../tests/native/abi2/allocation_watch.cpp)
target_link_libraries(real_callback_rt_watch_tests PRIVATE
  wirescape_audio_service Threads::Threads ${CMAKE_DL_LIBS})
add_dependencies(real_callback_rt_watch_tests qt_free_fake_portaudio)
set(_rt_watch_args "$<TARGET_FILE_DIR:qt_free_fake_portaudio>"
  "$<TARGET_FILE:qt_free_fake_portaudio>" "$<TARGET_FILE_DIR:wirescape_engine_sidecar>")
# Raw --inject-* modes intentionally fail (red-first evidence on 952057f).
# Normal CI runs the unchanged zero-count check and independent witnesses,
# each of which must detect exactly its own injected violation in every block.
add_test(NAME abi2_real_callback_rt_watch_clean
  COMMAND real_callback_rt_watch_tests ${_rt_watch_args})
add_test(NAME abi2_real_callback_rt_watch_allocation
  COMMAND real_callback_rt_watch_tests ${_rt_watch_args} --expect-allocation)
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  target_compile_definitions(real_callback_rt_watch_tests PRIVATE WS_CALLBACK_LOCK_WATCH=1)
  target_link_options(real_callback_rt_watch_tests PRIVATE
    "-Wl,--wrap=pthread_mutex_lock" "-Wl,--wrap=pthread_mutex_trylock")
  add_test(NAME abi2_real_callback_rt_watch_lock
    COMMAND real_callback_rt_watch_tests ${_rt_watch_args} --expect-lock)
  set_tests_properties(abi2_real_callback_rt_watch_lock PROPERTIES TIMEOUT 30)
endif()
set_tests_properties(abi2_real_callback_rt_watch_clean abi2_real_callback_rt_watch_allocation PROPERTIES TIMEOUT 30)

