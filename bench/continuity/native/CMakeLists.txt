# SPDX-License-Identifier: GPL-3.0-only
cmake_minimum_required(VERSION 3.20)
project(e5_native_capture LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT IS_ABSOLUTE "${WS_ENGINE_SOURCE}" OR NOT EXISTS "${WS_ENGINE_SOURCE}/tests/native/abi2/live_replan_tests.cpp")
  message(FATAL_ERROR "WS_ENGINE_SOURCE must be the absolute pinned source checkout")
endif()
find_package(Threads REQUIRED)
add_executable(e5_native_capture capture.cpp
  "${WS_ENGINE_SOURCE}/engine/engine2.cpp"
  "${WS_ENGINE_SOURCE}/engine/build.cpp"
  "${WS_ENGINE_SOURCE}/engine/render.cpp"
  "${WS_ENGINE_SOURCE}/engine/edit.cpp"
  "${WS_ENGINE_SOURCE}/tests/native/abi2/allocation_watch.cpp")
target_include_directories(e5_native_capture PRIVATE
  "${WS_ENGINE_SOURCE}/engine" "${WS_ENGINE_SOURCE}/engine/include"
  "${WS_ENGINE_SOURCE}/sdk" "${WS_ENGINE_SOURCE}/sdk/include"
  "${WS_ENGINE_SOURCE}/host/include" "${WS_ENGINE_SOURCE}/tests/native/abi2")
target_compile_definitions(e5_native_capture PRIVATE
  WS_FIXTURE_SOURCE="${WS_ENGINE_SOURCE}/tests/native/abi2/live_replan_tests.cpp")
target_link_libraries(e5_native_capture PRIVATE Threads::Threads)
