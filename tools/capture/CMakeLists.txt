# SPDX-License-Identifier: GPL-3.0-only
# Synthetic device-free analysis tests survive the ABI1 manual runner.
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
add_test(NAME capture_offline_selftests COMMAND ${Python3_EXECUTABLE}
  ${PROJECT_SOURCE_DIR}/../tools/capture/test_capture.py)
set_tests_properties(capture_offline_selftests PROPERTIES TIMEOUT 60)
