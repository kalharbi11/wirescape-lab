cmake_minimum_required(VERSION 3.20)
project(WirescapeNative VERSION 1.0.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
add_library(wirescape_engine SHARED src/engine.cpp)
target_compile_definitions(wirescape_engine PRIVATE WS_ENGINE_BUILD)
target_include_directories(wirescape_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(wirescape_engine PRIVATE ${CMAKE_DL_LIBS})
if(MSVC)
  target_compile_options(wirescape_engine PRIVATE /W4 /permissive-)
else()
  target_compile_options(wirescape_engine PRIVATE -Wall -Wextra -Wpedantic)
endif()
function(wirescape_add_module target)
  add_library(${target} SHARED module.cpp)
  target_include_directories(${target} PRIVATE ${PROJECT_SOURCE_DIR}/include)
  add_custom_command(TARGET ${target} POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy_if_different
    ${CMAKE_CURRENT_SOURCE_DIR}/module.json $<TARGET_FILE_DIR:${target}>/${target}.module.json)
endfunction()
# A new ordinary module needs its own folder and CMakeLists, not a host switch.
file(GLOB module_directories CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/modules/*")
foreach(module_directory ${module_directories})
  if(IS_DIRECTORY "${module_directory}" AND EXISTS "${module_directory}/CMakeLists.txt")
    add_subdirectory("${module_directory}")
  endif()
endforeach()
add_executable(wirescape_cli cli/main.cpp)
enable_testing()
add_subdirectory(document)
find_package(Threads REQUIRED)
# Compile the same engine into the test process so operator-new instrumentation
# observes engine allocations on Windows as well as Linux.
add_executable(native_engine_tests tests/engine_tests.cpp src/engine.cpp)
target_compile_definitions(native_engine_tests PRIVATE WS_ENGINE_BUILD)
target_include_directories(native_engine_tests PRIVATE include)
target_link_libraries(native_engine_tests PRIVATE ${CMAKE_DL_LIBS} Threads::Threads)
foreach(module vco adsr vca output)
  add_library(ws_test_${module} OBJECT modules/${module}/module.cpp)
  target_include_directories(ws_test_${module} PRIVATE include)
  target_compile_definitions(ws_test_${module} PRIVATE WS_MODULE_ENTRY_NAME=ws_test_${module}_entry)
  target_sources(native_engine_tests PRIVATE $<TARGET_OBJECTS:ws_test_${module}>)
endforeach()
add_test(NAME native_engine_tests COMMAND native_engine_tests $<TARGET_FILE_DIR:ws_vco>)
set_tests_properties(native_engine_tests PROPERTIES TIMEOUT 60)
add_library(ws_test_mixer OBJECT modules/mixer/module.cpp)
target_include_directories(ws_test_mixer PRIVATE include)
target_compile_definitions(ws_test_mixer PRIVATE WS_MODULE_ENTRY_NAME=ws_test_mixer_entry)
add_executable(native_module_tests tests/module_tests.cpp $<TARGET_OBJECTS:ws_test_mixer>
  $<TARGET_OBJECTS:ws_test_vco> $<TARGET_OBJECTS:ws_test_vca> $<TARGET_OBJECTS:ws_test_adsr>)
target_link_libraries(native_module_tests PRIVATE wirescape_engine)
add_test(NAME native_module_tests COMMAND native_module_tests $<TARGET_FILE_DIR:ws_mixer>)
set_tests_properties(native_module_tests PROPERTIES TIMEOUT 30)
add_library(ws_test_scale_offset OBJECT modules/scale_offset/module.cpp)
target_include_directories(ws_test_scale_offset PRIVATE include)
target_compile_definitions(ws_test_scale_offset PRIVATE WS_MODULE_ENTRY_NAME=ws_test_scale_offset_entry)
add_executable(native_scale_offset_tests tests/scale_offset_tests.cpp
  $<TARGET_OBJECTS:ws_test_scale_offset> $<TARGET_OBJECTS:ws_test_vco>
  $<TARGET_OBJECTS:ws_test_adsr> $<TARGET_OBJECTS:ws_test_vca> $<TARGET_OBJECTS:ws_test_output>)
target_link_libraries(native_scale_offset_tests PRIVATE wirescape_engine)
add_dependencies(native_scale_offset_tests ws_scale_offset)
add_test(NAME native_scale_offset_tests COMMAND native_scale_offset_tests $<TARGET_FILE_DIR:ws_scale_offset>)
set_tests_properties(native_scale_offset_tests PROPERTIES TIMEOUT 30)
add_library(ws_test_lfo OBJECT modules/lfo/module.cpp)
target_include_directories(ws_test_lfo PRIVATE include)
target_compile_definitions(ws_test_lfo PRIVATE WS_MODULE_ENTRY_NAME=ws_test_lfo_entry)
add_executable(native_lfo_tests tests/lfo_tests.cpp $<TARGET_OBJECTS:ws_test_lfo>
  $<TARGET_OBJECTS:ws_test_vco> $<TARGET_OBJECTS:ws_test_vca> $<TARGET_OBJECTS:ws_test_output>)
target_link_libraries(native_lfo_tests PRIVATE wirescape_engine)
add_dependencies(native_lfo_tests ws_lfo)
add_test(NAME native_lfo_tests COMMAND native_lfo_tests $<TARGET_FILE_DIR:ws_lfo>)
set_tests_properties(native_lfo_tests PROPERTIES TIMEOUT 30)
foreach(module noise slew function_envelope clock vcf ladder)
  add_executable(essentials_${module}_tests modules/${module}/tests.cpp)
  target_link_libraries(essentials_${module}_tests PRIVATE wirescape_engine)
  add_dependencies(essentials_${module}_tests ws_${module})
  add_test(NAME essentials_${module}_tests COMMAND essentials_${module}_tests $<TARGET_FILE:ws_${module}>)
  set_tests_properties(essentials_${module}_tests PROPERTIES TIMEOUT 30)
endforeach()
add_executable(returned_filter_stress tests/returned_filter_stress.cpp)
target_link_libraries(returned_filter_stress PRIVATE wirescape_engine)
add_dependencies(returned_filter_stress ws_vcf ws_ladder)
add_test(NAME returned_filter_stress COMMAND returned_filter_stress $<TARGET_FILE_DIR:ws_vcf>)
set_tests_properties(returned_filter_stress PROPERTIES TIMEOUT 30)

# Isolated experimental ABI2 foundation; ABI1 app/engine/module sources stay unchanged.
add_subdirectory(engine2)
# Production ABI2 device-free renderer and behavioral CTests.
add_subdirectory(tools/render)

# Offline analysis tests only; real endpoint capture is always a manual command.
add_subdirectory(tools/capture)

# Independent localhost UDP worker; production Session integration follows in OSC B.
add_library(wirescape_osc_service STATIC io/net/osc_service.cpp)
target_include_directories(wirescape_osc_service PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(wirescape_osc_service PUBLIC Threads::Threads)
if(WIN32)
  target_link_libraries(wirescape_osc_service PUBLIC ws2_32)
endif()
add_executable(abi2_osc_host_service_tests io/net/tests.cpp)
target_include_directories(abi2_osc_host_service_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/sdk)
target_link_libraries(abi2_osc_host_service_tests PRIVATE wirescape_osc_service)
add_test(NAME abi2_osc_host_service_tests COMMAND abi2_osc_host_service_tests)
set_tests_properties(abi2_osc_host_service_tests PROPERTIES TIMEOUT 30)

# Offline real engine route: measured worker timestamp, one-block lead and
# no audio-thread allocation. Only binds a loopback ephemeral UDP socket.
add_executable(abi2_osc_graph_ingress_tests io/net/graph_tests.cpp tests2/allocation_watch.cpp)
target_include_directories(abi2_osc_graph_ingress_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/sdk)
target_link_libraries(abi2_osc_graph_ingress_tests PRIVATE
  wirescape_runtime_document wirescape_osc_service nlohmann_json::nlohmann_json)
add_test(NAME abi2_osc_graph_ingress_tests COMMAND abi2_osc_graph_ingress_tests)
set_tests_properties(abi2_osc_graph_ingress_tests PROPERTIES TIMEOUT 30)


# Always compile the two harness translation units for Static ownership coverage.
# This OBJECT library never links or runs libFuzzer in the standard build.
add_library(abi2_osc_fuzz_compile OBJECT io/osc/fuzz.cpp)
# Opt-in device-free OSC libFuzzer executables; disabled in normal builds.
option(WIRESCAPE_OSC_FUZZ "Build Clang libFuzzer OSC packet/pattern targets" OFF)
if(WIRESCAPE_OSC_FUZZ)
  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(FATAL_ERROR "WIRESCAPE_OSC_FUZZ requires Clang with libFuzzer")
  endif()
  foreach(kind codec pattern)
    add_executable(abi2_osc_${kind}_fuzz io/osc/fuzz.cpp)
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
execute_process(COMMAND git rev-parse --short=12 HEAD WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
  OUTPUT_VARIABLE engine_sha OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
add_library(wirescape_osc_host STATIC control/osc_host.cpp control/osc_out_host.cpp)
target_include_directories(wirescape_osc_host PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/control)
target_link_libraries(wirescape_osc_host PUBLIC wirescape_osc_service wirescape_runtime_document
  nlohmann_json::nlohmann_json)
add_executable(wirescape_engine_sidecar sidecar/main.cpp sidecar/protocol.cpp sidecar/session.cpp sidecar/devices.cpp)
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
add_test(NAME abi2_sidecar_protocol_tests COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/sidecar/protocol_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar> ${PROJECT_SOURCE_DIR}/examples)
set_tests_properties(abi2_sidecar_protocol_tests PROPERTIES TIMEOUT 90)
add_test(NAME abi2_sidecar_apply_graph_tests COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/sidecar/apply_graph_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar>)
set_tests_properties(abi2_sidecar_apply_graph_tests PROPERTIES TIMEOUT 120)
add_test(NAME abi2_sidecar_capture_tests COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/sidecar/capture_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar>)
set_tests_properties(abi2_sidecar_capture_tests PROPERTIES TIMEOUT 90)
add_test(NAME sidecar_golden COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/sidecar/golden_tests.py
  $<TARGET_FILE:wirescape_engine_sidecar> ${CMAKE_CURRENT_SOURCE_DIR}/../tests/protocol/golden_v0.ndjson)
set_tests_properties(sidecar_golden PROPERTIES TIMEOUT 180)
add_executable(sidecar_protocol_unit_tests sidecar/protocol_unit_tests.cpp sidecar/protocol.cpp sidecar/devices.cpp tests2/allocation_watch.cpp)
target_link_libraries(sidecar_protocol_unit_tests PRIVATE wirescape_runtime_document wirescape_audio_service
  wirescape_midi_host wirescape_osc_host nlohmann_json::nlohmann_json Threads::Threads)
add_test(NAME abi2_sidecar_unit_tests COMMAND sidecar_protocol_unit_tests)
set_tests_properties(abi2_sidecar_unit_tests PROPERTIES TIMEOUT 30)
add_executable(sidecar_audio_recovery_tests sidecar/audio_recovery_tests.cpp sidecar/session.cpp io/audio/device_identity.cpp
  sidecar/protocol.cpp sidecar/devices.cpp)
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
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/sidecar/session.cpp" _s0_session_source)
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
  sidecar/snapshot_tests.cpp "${CMAKE_CURRENT_BINARY_DIR}/s0_snapshot_session.cpp"
  sidecar/protocol.cpp sidecar/devices.cpp)
target_include_directories(sidecar_s0_snapshot_tests PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/sidecar" "${CMAKE_CURRENT_SOURCE_DIR}/document"
  "${CMAKE_CURRENT_BINARY_DIR}")
target_compile_definitions(sidecar_s0_snapshot_tests PRIVATE WIRESCAPE_ENGINE_SHA="s0-fixture-build")
target_link_libraries(sidecar_s0_snapshot_tests PRIVATE wirescape_runtime_document wirescape_audio_service
  wirescape_midi_host wirescape_osc_host nlohmann_json::nlohmann_json Threads::Threads)
add_test(NAME abi2_sidecar_snapshot_tests COMMAND sidecar_s0_snapshot_tests
  "${CMAKE_CURRENT_SOURCE_DIR}/sidecar/testdata")
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
