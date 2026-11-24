# SPDX-License-Identifier: GPL-3.0-only
add_library(ws2_poly_merge SHARED module.cpp)
target_link_libraries(ws2_poly_merge PRIVATE wirescape_sdk2)
add_executable(abi2_poly_merge_tests tests.cpp ../../tests/native/abi2/allocation_watch.cpp)
target_link_libraries(abi2_poly_merge_tests PRIVATE wirescape_sdk2)
add_dependencies(abi2_poly_merge_tests ws2_poly_merge)
add_test(NAME abi2_poly_merge_tests COMMAND abi2_poly_merge_tests)
