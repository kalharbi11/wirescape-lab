# SPDX-License-Identifier: GPL-3.0-only
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
add_executable(wirescape_render main.cpp)
target_link_libraries(wirescape_render PRIVATE wirescape_runtime_document nlohmann_json::nlohmann_json)
foreach(case_name adsr-notes frequency-step blend-selection)
  string(REPLACE "-" "_" test_name "${case_name}")
  add_test(NAME render_evidence_${test_name}
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/evidence.py
      --render $<TARGET_FILE:wirescape_render>
      --case ${CMAKE_CURRENT_SOURCE_DIR}/cases/${case_name}.json
      --out ${CMAKE_BINARY_DIR}/render_evidence/${case_name}
      --compiler "${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}"
      --configuration "$<CONFIG>")
  set_tests_properties(render_evidence_${test_name} PROPERTIES TIMEOUT 90)
endforeach()
# #663: run the unchanged ADSR note case at Daisy-sized blocks.
foreach(block_size 16 17)
  add_test(NAME render_evidence_adsr_notes_block_${block_size}
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/evidence.py
      --render $<TARGET_FILE:wirescape_render>
      --case ${CMAKE_CURRENT_SOURCE_DIR}/cases/adsr-notes.json
      --block ${block_size}
      --out ${CMAKE_BINARY_DIR}/render_evidence/adsr-notes-block-${block_size}
      --compiler "${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}"
      --configuration "$<CONFIG>")
  set_tests_properties(render_evidence_adsr_notes_block_${block_size} PROPERTIES TIMEOUT 90)
endforeach()
# Device-free, real AppEngine regression for every published Studio patch.
# The existing evidence SILENT_PEAK threshold is reused by library_smoke.py.
add_test(NAME render_evidence_library_smoke
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/library_smoke.py
    --render $<TARGET_FILE:wirescape_render>
    --patches ${CMAKE_CURRENT_SOURCE_DIR}/../../apps/studio/patches)
set_tests_properties(render_evidence_library_smoke PROPERTIES TIMEOUT 240)
add_test(NAME render_evidence_late_negative
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/evidence.py
    --render $<TARGET_FILE:wirescape_render>
    --case ${CMAKE_CURRENT_SOURCE_DIR}/cases/adsr-notes.json
    --out ${CMAKE_BINARY_DIR}/render_evidence/late-negative --negative-late)
set_tests_properties(render_evidence_late_negative PROPERTIES TIMEOUT 90)
add_test(NAME render_evidence_negative COMMAND ${Python3_EXECUTABLE}
  ${CMAKE_CURRENT_SOURCE_DIR}/evidence.py --negative)
set_tests_properties(render_evidence_negative PROPERTIES TIMEOUT 30)

# OB-a3 pin 7: preserve v1 on real renderer refusal; valid v2 still renders.
# Test-only registration, with a separate disposable WAV output directory.
add_test(NAME abi2_ob_a3_renderer_no_write COMMAND ${Python3_EXECUTABLE}
  "${CMAKE_CURRENT_SOURCE_DIR}/ob_a3_no_write.py"
  $<TARGET_FILE:wirescape_render>
  "${PROJECT_SOURCE_DIR}/../host/examples/Six_Essentials_Demo.json"
  "${CMAKE_CURRENT_SOURCE_DIR}/cases/frequency-step.json")
set_tests_properties(abi2_ob_a3_renderer_no_write PROPERTIES TIMEOUT 120)

# OB-h6: device-free actual renderer and patch-folder checker contract.
add_test(NAME abi2_ob_h6_patch_check
  COMMAND ${CMAKE_COMMAND} -E env "WIRESCAPE_TEST_RENDERER=$<TARGET_FILE:wirescape_render>"
    ${Python3_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/test_patch_check.py")
set_tests_properties(abi2_ob_h6_patch_check PROPERTIES TIMEOUT 240)
