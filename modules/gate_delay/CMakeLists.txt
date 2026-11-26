# SPDX-License-Identifier: GPL-3.0-only
add_library(ws2_gate_delay SHARED module.cpp)
target_link_libraries(ws2_gate_delay PRIVATE wirescape_sdk2)
add_executable(abi2_gate_delay_tests tests.cpp ../../tests/native/abi2/allocation_watch.cpp)
target_link_libraries(abi2_gate_delay_tests PRIVATE wirescape_sdk2)
add_dependencies(abi2_gate_delay_tests ws2_gate_delay)
add_test(NAME abi2_gate_delay_tests COMMAND abi2_gate_delay_tests)
