# SPDX-License-Identifier: GPL-3.0-only
cmake_minimum_required(VERSION 3.20)
project(e5_block_cost LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT IS_ABSOLUTE "${WS_ENGINE_SOURCE}" OR NOT EXISTS "${WS_ENGINE_SOURCE}/native/CMakeLists.txt")
  message(FATAL_ERROR "WS_ENGINE_SOURCE must be the absolute pinned source checkout")
endif()
find_package(Threads REQUIRED)
find_path(VALGRIND_INCLUDE valgrind/callgrind.h REQUIRED)
# Use the pinned, unchanged native target graph, not a second module registry.
# Build only the runtime document and its dependencies via the target below.
add_subdirectory("${WS_ENGINE_SOURCE}/native" source-native EXCLUDE_FROM_ALL)
add_executable(e5_block_cost block_cost.cpp)
target_include_directories(e5_block_cost PRIVATE "${VALGRIND_INCLUDE}")
target_link_libraries(e5_block_cost PRIVATE wirescape_runtime_document nlohmann_json::nlohmann_json Threads::Threads)
