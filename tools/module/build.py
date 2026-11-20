# SPDX-License-Identifier: GPL-3.0-only
"""Offline, in-place module compiler used by check and the later matrix/render drivers."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess


def located(root: Path, layout: dict, name: str) -> Path:
    return root / layout["paths"][name]


def load_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("helper module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toolchain(root: Path, layout: dict) -> dict:
    return load_file(located(root, layout, "foundation_helpers"), "wsmod_foundation_helpers").discover_toolchain()


def clean_error(output: str, root: Path, folder: Path, build_dir: Path) -> str:
    """Quote the first compiler error, not a machine-specific file-system path."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    first = next((line for line in lines if re.search(r"\berror\s*[:(]|fatal error|undefined reference|unresolved external", line, re.I)),
                 lines[-1] if lines else "compiler returned failure without diagnostics")
    for path in sorted((root, folder, build_dir), key=lambda p: len(str(p)), reverse=True):
        first = first.replace(str(path), "<source>")
        first = first.replace(path.as_posix(), "<source>")
    # Remove other absolute compiler/system paths, including Windows drive names.
    first = re.sub(r"(?<![\w])(?:[A-Za-z]:)?(?:[/\\][^\s:/\\]+){2,}", "<path>", first)
    return first[:350]


def build_dir_for(root: Path, folder: Path, layout: dict, keep: Path | None) -> Path:
    if keep is not None:
        return keep.resolve()
    digest = hashlib.sha256(str(folder).encode("utf-8")).hexdigest()[:16]
    return located(root, layout, "build_root") / digest


def _cmake_string(path: Path) -> str:
    return path.resolve().as_posix().replace(";", "\\;").replace('"', '\\"')


def _add(paths: list[Path]) -> str:
    return "\n".join('  "' + _cmake_string(p) + '"' for p in paths)


def generate_project(root: Path, folder: Path, layout: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    try:
        relative = folder.relative_to(root).as_posix()
    except ValueError:
        relative = None
    stock = layout.get("stock", {}).get(relative, {})
    extras = [root / item for item in stock.get("extra_sources", [])]
    sources = [folder / "module.cpp", *extras]
    runner = Path(__file__).with_name("runner")
    runner_sources = [runner / "main.cpp", runner / "matrix.cpp", runner / "render.cpp"]
    alloc = located(root, layout, "allocation_counter")
    include = [located(root, layout, "sdk"), located(root, layout, "abi"), folder,
               located(root, layout, "allocation_include")]
    text = '''# SPDX-License-Identifier: GPL-3.0-only
cmake_minimum_required(VERSION 3.20)
project(wsmod_offline LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_library(wsmod_shared SHARED
''' + _add(sources) + '''
)
add_executable(wsmod_runner
''' + _add([*runner_sources, *sources, alloc]) + '''
)
foreach(target IN ITEMS wsmod_shared wsmod_runner)
  target_include_directories(${target} PRIVATE
''' + _add(include) + '''
  )
  if(MSVC)
    target_compile_options(${target} PRIVATE /O2)
  else()
    target_compile_options(${target} PRIVATE -O2)
  endif()
endforeach()
# Module sources are restricted; the reused test-only allocation counter may
# use exceptions because its existing global-new implementation throws bad_alloc.
if(MSVC)
  set_source_files_properties("''' + _cmake_string(folder / "module.cpp") + '''" PROPERTIES COMPILE_OPTIONS "/EHs-c;/GR-")
else()
  set_source_files_properties("''' + _cmake_string(folder / "module.cpp") + '''" PROPERTIES COMPILE_OPTIONS "-fno-exceptions;-fno-rtti")
endif()
# MT2: raw heap wrappers supplement the existing new/delete counter on Linux.
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  target_link_options(wsmod_runner PRIVATE
    "-Wl,--wrap=malloc" "-Wl,--wrap=calloc"
    "-Wl,--wrap=realloc" "-Wl,--wrap=aligned_alloc")
endif()
'''
    (directory / "CMakeLists.txt").write_text(text, encoding="utf-8")


def run_command(command: list[str], timeout: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(command, text=True, capture_output=True, check=False,
                          timeout=timeout, stdin=subprocess.DEVNULL)


def build(root: Path, folder: Path, layout: dict, keep: Path | None = None) -> dict:
    try:
        tools = toolchain(root, layout)
    except (OSError, ValueError, ImportError) as error:
        return {"state": "environment", "detail": type(error).__name__}
    if not tools.get("cmake") or not tools.get("generator"):
        return {"state": "environment", "detail": "CMake or a supported C++17 generator is missing"}
    try:
        relative = folder.relative_to(root).as_posix()
    except ValueError:
        relative = ""
    if relative in layout.get("stock", {}) and "build_unsupported" in layout["stock"][relative]:
        return {"state": "unsupported", "detail": layout["stock"][relative]["build_unsupported"]}
    target = build_dir_for(root, folder, layout, keep)
    try:
        generate_project(root, folder, layout, target)
        configure = [tools["cmake"], "-S", str(target), "-B", str(target / "compiled"),
                     "-G", tools["generator"], "-DCMAKE_BUILD_TYPE=Release"]
        if os.name == "nt" and tools["generator"].startswith("Visual Studio"):
            configure += ["-A", "x64"]
        for command in (configure, [tools["cmake"], "--build", str(target / "compiled"),
                                    "--config", "Release", "--parallel", "2",
                                    "--target", "wsmod_shared", "wsmod_runner"]):
            result = run_command(command)
            if result.returncode:
                return {"state": "build", "detail": clean_error(result.stderr + "\n" + result.stdout,
                                                                    root, folder, target)}
        name = "wsmod_runner.exe" if os.name == "nt" else "wsmod_runner"
        candidates = [p for p in (target / "compiled").rglob(name) if p.is_file()]
        if not candidates:
            return {"state": "build", "detail": "runner executable absent after successful CMake build"}
        candidates.sort()
        return {"state": "ok", "runner": candidates[0], "directory": target}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"state": "build", "detail": type(error).__name__ + " while compiling"}


def portable_symbols(root: Path, folder: Path, layout: dict, directory: Path) -> dict:
    """C6 compile-only; any failure or unavailable toolchain remains advisory."""
    result = {"native": "unavailable", "cross": "unavailable", "symbols": {}}
    compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    nm = shutil.which("nm") or shutil.which("llvm-nm")
    if not compiler or not nm:
        return result
    directory.mkdir(parents=True, exist_ok=True)
    includes = [str(located(root, layout, name)) for name in ("sdk", "abi")]
    object_file = directory / "portable_module.o"
    command = [compiler, "-std=c++17", "-O2", "-fno-exceptions", "-fno-rtti", "-c",
               str(folder / "module.cpp"), "-o", str(object_file)]
    for include in includes:
        command += ["-I", include]
    try:
        built = run_command(command, timeout=90)
        if built.returncode:
            result["native"] = "compile_error: " + clean_error(built.stderr, root, folder, directory)
        else:
            nm_result = run_command([nm, "-u", str(object_file)], timeout=30)
            if nm_result.returncode:
                result["native"] = "symbols_unavailable"
            else:
                symbols = [line.split()[-1] for line in nm_result.stdout.splitlines()
                           if line.split() and (len(line.split()) == 1 or line.split()[-2] in ("U", "w", "W"))]
                flags = load_file(located(root, layout, "portable_probe"), "wsmod_symbol_probe").symbol_flags(symbols)
                result.update(native="compiled", symbols=flags)
        cross_compiler = shutil.which("arm-none-eabi-g++")
        if cross_compiler:
            cross_obj = directory / "arm_module.o"
            cross = [cross_compiler, "-std=c++17", "-Os", "-fno-exceptions", "-fno-rtti",
                     "-mcpu=cortex-m7", "-mthumb", "-mfpu=fpv5-d16", "-mfloat-abi=hard",
                     "-c", str(folder / "module.cpp"), "-o", str(cross_obj)]
            for include in includes:
                cross += ["-I", include]
            c = run_command(cross, timeout=90)
            result["cross"] = "compiled" if c.returncode == 0 else (
                "compile_error: " + clean_error(c.stderr, root, folder, directory))
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        result["native"] = "unavailable: " + type(error).__name__
    return result
