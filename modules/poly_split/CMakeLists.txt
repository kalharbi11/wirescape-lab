# SPDX-License-Identifier: GPL-3.0-only
add_library(ws2_poly_split SHARED module.cpp)
target_link_libraries(ws2_poly_split PRIVATE wirescape_sdk2)
add_executable(abi2_poly_split_tests tests.cpp ../../tests/native/abi2/allocation_watch.cpp)
target_link_libraries(abi2_poly_split_tests PRIVATE wirescape_sdk2)
add_dependencies(abi2_poly_split_tests ws2_poly_split)
add_test(NAME abi2_poly_split_tests COMMAND abi2_poly_split_tests)
