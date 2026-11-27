# SPDX-License-Identifier: GPL-3.0-only
# Keep built-in wrapper code generation isolated by translation unit.
# Native and Web both call this function; shared-library tests retain the
# default ABI entry names, while these static targets use unique symbols.
function(ws_builtin_registry target root)
  file(GLOB module_sources CONFIGURE_DEPENDS "${root}/modules/*/module.cpp"
    "${root}/sdk/examples/*/module.cpp")
  set(WS_REGISTRY_DECLARATIONS "")
  set(WS_REGISTRY_ENTRIES "")
  foreach(source IN LISTS module_sources)
    get_filename_component(folder_path "${source}" DIRECTORY)
    get_filename_component(folder "${folder_path}" NAME)
    if(NOT folder MATCHES "^[A-Za-z_][A-Za-z0-9_]*$")
      message(FATAL_ERROR "Invalid module folder for static entry symbol: ${folder}")
    endif()
    set(module_target "ws_builtin_${folder}")
    if(TARGET "${module_target}")
      message(FATAL_ERROR "Duplicate module folder for static entry symbol: ${folder}")
    endif()
    add_library("${module_target}" STATIC "${source}")
    target_compile_definitions("${module_target}" PRIVATE
      WS_MODULE2_ENTRY_NAME=ws_module_entry_${folder}
      WS_MODULE2_VERSION_NAME=ws_module_version_${folder})
    target_link_libraries("${module_target}" PRIVATE ${ARGN})
    # Optional folder-local additions for built-in compilation, on both targets.
    if(EXISTS "${folder_path}/module.cmake")
      include("${folder_path}/module.cmake")
    endif()
    target_link_libraries("${target}" PRIVATE "${module_target}")
    string(APPEND WS_REGISTRY_DECLARATIONS "extern \"C\" const ws2_descriptor *WS2_CALL ws_module_entry_${folder}(void);\n")
    string(APPEND WS_REGISTRY_ENTRIES "        ws_module_entry_${folder}(),\n")
  endforeach()
  set(generated "${CMAKE_CURRENT_BINARY_DIR}/${target}_module_registry.cpp")
  configure_file("${root}/engine/control/module_registry.cpp.in" "${generated}" @ONLY)
  target_sources("${target}" PRIVATE "${generated}")
endfunction()
