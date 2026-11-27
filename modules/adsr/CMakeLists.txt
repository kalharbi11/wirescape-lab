# SPDX-License-Identifier: GPL-3.0-only
# OB-g5 standalone exact-source/device-off test, separate from shared native build.
# Execute: cmake -S native/modules2/adsr -B /tmp/adsr-ob-g5 &&
#          cmake --build /tmp/adsr-ob-g5 && ctest --test-dir /tmp/adsr-ob-g5 --output-on-failure
cmake_minimum_required(VERSION 3.20)
if(TARGET wirescape_sdk2)
  # Native folder discovery: keep the original standalone test and shared ABI library.
  add_library(ws2_adsr SHARED module.cpp)
  target_link_libraries(ws2_adsr PRIVATE wirescape_sdk2)
  add_executable(adsr_ob_g5_tests tests.cpp)
  target_link_libraries(adsr_ob_g5_tests PRIVATE wirescape_sdk2)
  add_test(NAME adsr_ob_g5_tests COMMAND adsr_ob_g5_tests)
  return()
endif()
project(ADSR_OB_G5_Tests LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
enable_testing()
add_executable(adsr_ob_g5_tests tests.cpp)
target_include_directories(adsr_ob_g5_tests PRIVATE ../../sdk ../../sdk/include ../../engine/include ../../host/include)
add_test(NAME adsr_ob_g5_tests COMMAND adsr_ob_g5_tests)
