# SPDX-License-Identifier: GPL-3.0-only
cmake_minimum_required(VERSION 3.20)
project(wirescape_device_capture LANGUAGES CXX)
if(NOT WIN32)
  message(FATAL_ERROR "WASAPI PID-targeted capture only builds on Windows")
endif()
add_executable(wirescape_device_capture capture_engine.cpp)
target_compile_features(wirescape_device_capture PRIVATE cxx_std_17)
target_compile_definitions(wirescape_device_capture PRIVATE _WIN32_WINNT=0x0A00)
target_link_libraries(wirescape_device_capture PRIVATE ole32 uuid mmdevapi)
# This binary is manual only: no add_test, and CI never launches it.
