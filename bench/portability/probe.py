# SPDX-License-Identifier: GPL-3.0-only
"""Cortex-M7 compile-only ABI2 portability inventory; no linking or device access."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
FPUS = ("fpv5-d16", "fpv5-sp-d16")
SHA256_TOOLCHAIN = "62a63b981fe391a9cbad7ef51b17e49aeaa3e7b0d029b36ca1e9c3b2a9b78823"


def run(argv, timeout=120):
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True,
                          check=False, timeout=timeout)


def sources():
    catalog = (ROOT / "engine/control/module_catalog.inc").read_text(encoding="utf-8")
    n_catalog = len(re.findall(r"(?m)^\s*WS_APP_MODULE\(", catalog))
    modules = sorted((ROOT / "modules").glob("*/module.cpp"))
    examples = sorted((ROOT / "sdk/examples").glob("*/module.cpp"))
    if len(modules) + len(examples) != n_catalog:
        raise RuntimeError(f"catalog has {n_catalog} entries, found {len(modules)} module TUs "
                           f"and {len(examples)} SDK example TUs")
    template = ROOT / "sdk/template/module.cpp"
    if not template.is_file():
        raise RuntimeError("missing SDK template module.cpp")
    return modules + examples + [template], n_catalog


def symbol_flags(symbols):
    """Undefined symbols only, grouped without interpreting portability."""
    names = set(symbols)
    math_names = re.compile(r"^(?:sin|cos|tan|asin|acos|atan|atan2|exp|exp2|expm1|log|log2|log10|log1p|pow|sqrt|floor|ceil|round|fmod|hypot|fabs)(?:f|l)?$")
    return {
        "double_or_softfloat_symbols": sorted(n for n in names if
            n.startswith("__aeabi_d") or n.startswith("__aeabi_f") or
            (math_names.match(n) and not n.endswith("f"))),
        "float_libm_symbols": sorted(n for n in names if math_names.match(n) and n.endswith("f")),
        "heap_symbols": sorted(n for n in names if n in ("malloc", "calloc", "realloc", "free") or
                                n.startswith(("_Znwm", "_Znam", "_Znwj", "_Znaj", "_Zdl", "_Zda"))),
        "static_guard_symbols": sorted(n for n in names if n.startswith("__cxa_guard_")),
    }


def section_sizes(output):
    result = {"text_bytes": 0, "data_bytes": 0, "bss_bytes": 0}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 3 or not parts[1].isdigit():
            continue
        section, n = parts[0], int(parts[1])
        if section == ".text" or section.startswith(".text."):
            result["text_bytes"] += n
        elif section in (".data", ".sdata") or section.startswith((".data.", ".sdata.")):
            result["data_bytes"] += n
        elif section in (".bss", ".sbss") or section.startswith((".bss.", ".sbss.")):
            result["bss_bytes"] += n
    return result


def first_error(stderr):
    lines = [line.strip().replace(str(ROOT), "<repo>") for line in stderr.splitlines() if line.strip()]
    return next((line[:360] for line in lines if "error:" in line.lower()),
                lines[0][:360] if lines else "compiler returned nonzero with no stderr")


def compile_one(compiler, size_cmd, nm_cmd, source, fpu, object_dir):
    rel = source.relative_to(ROOT).as_posix()
    label = rel.replace("/", "_").removesuffix(".cpp")
    dest = object_dir / fpu / (label + ".o")
    dest.parent.mkdir(parents=True, exist_ok=True)
    flags = [
        "-std=c++17", "-mcpu=cortex-m7", "-mthumb", f"-mfpu={fpu}",
        "-mfloat-abi=hard", "-fno-exceptions", "-fno-rtti", "-Os",
        "-ffunction-sections", "-fdata-sections", "-DWS_SIMD_SCALAR",
        "-I", "sdk", "-I", "sdk/include", "-I", "sdk/examples",
    ]
    if "macro_oscillator" in source.parts:
        flags.extend(("-I", ".tools/portability-context/eurorack",
                      "-I", ".tools/portability-context",
                      "-DTEST", "-include", "modules/macro_oscillator/rng_scope.hpp"))
    outcome = run([compiler, *flags, "-c", rel, "-o", str(dest)], timeout=180)
    if outcome.returncode:
        return {"compiles": False, "first_error": first_error(outcome.stderr),
                "text_bytes": None, "data_bytes": None, "bss_bytes": None,
                **symbol_flags([])}
    size = run([size_cmd, "-A", str(dest)])
    nm = run([nm_cmd, "--undefined-only", str(dest)])
    if size.returncode or nm.returncode:
        raise RuntimeError(f"{rel}: cross-binutils failure: {size.stderr} {nm.stderr}")
    symbols = []
    for line in nm.stdout.splitlines():
        bits = line.split()
        if len(bits) >= 2 and bits[-2] in ("U", "w", "W"):
            symbols.append(bits[-1])
    return {"compiles": True, "first_error": None, **section_sizes(size.stdout),
            **symbol_flags(symbols)}


def table(data):
    rows = [
        "<!-- SPDX-License-Identifier: GPL-3.0-only -->",
        "# Cortex-M7 compile-only module measurements",
        "",
        f"Commit: {data['commit']}",
        f"Date (New York): {data['date_et']}",
        f"Compiler: {data['toolchain_version']}",
        "Target: Cortex-M7, hard float, -fno-exceptions, -fno-rtti, -Os; object only, no link.",
        "Section bytes are summed .text.*, .data.*, .bss.* entries from arm-none-eabi-size -A.",
        "",
        "| Source | FPU | Compiles | .text B | .data B | .bss B | double/softfloat refs | heap refs | static guards |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for source, result in data["modules"].items():
        for fpu, row in result.items():
            fmt = lambda n: "-" if n is None else str(n)
            rows.append(f"| {source} | {fpu} | {'yes' if row['compiles'] else 'no'} | "
                        f"{fmt(row['text_bytes'])} | {fmt(row['data_bytes'])} | {fmt(row['bss_bytes'])} | "
                        f"{len(row['double_or_softfloat_symbols'])} | {len(row['heap_symbols'])} | "
                        f"{len(row['static_guard_symbols'])} |")
    rows += ["", "First compile errors and symbol names are recorded in modules.json.", ""]
    return "\n".join(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("build_reports/portability/modules.json"))
    p.add_argument("--readme", type=Path, default=Path("build_reports/portability/README.md"))
    p.add_argument("--objects", type=Path, default=Path("build_reports/portability/objects"))
    p.add_argument("--emit-chunks", action="store_true")
    args = p.parse_args(argv)
    compiler, size_cmd, nm_cmd = ("arm-none-eabi-g++", "arm-none-eabi-size", "arm-none-eabi-nm")
    version = run([compiler, "--version"])
    if version.returncode:
        p.error("pinned Arm GNU compiler missing")
    commit = run(["git", "rev-parse", "HEAD"])
    if commit.returncode:
        p.error("git HEAD unavailable")
    inputs, catalog_n = sources()
    report = {
        "SPDX-License-Identifier": "GPL-3.0-only",
        "schema": 1,
        "commit": commit.stdout.strip(),
        "date_et": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine": "cortex-m7",
        "toolchain_version": version.stdout.splitlines()[0],
        "toolchain_archive_sha256": SHA256_TOOLCHAIN,
        "target_flags": "-mcpu=cortex-m7 -mthumb -mfloat-abi=hard -fno-exceptions -fno-rtti -Os",
        "fpu_variants": list(FPUS),
        "catalog_modules": catalog_n,
        "sdk_template_count": 1,
        "modules": {},
    }
    for source in inputs:
        rel = source.relative_to(ROOT).as_posix()
        report["modules"][rel] = {}
        for fpu in FPUS:
            result = compile_one(compiler, size_cmd, nm_cmd, source, fpu, args.objects)
            report["modules"][rel][fpu] = result
            print(f"PROBE {rel} {fpu}: {result['compiles']}; "
                  f"text={result['text_bytes']} data={result['data_bytes']} bss={result['bss_bytes']}",
                  flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.readme.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    args.readme.write_text(table(report), encoding="utf-8")
    if args.emit_chunks:
        compact = json.dumps(report, separators=(",", ":"), ensure_ascii=True)
        for i in range(0, len(compact), 1400):
            print(f"PORTABILITY_CHUNK {i//1400:04d} {compact[i:i+1400]}", flush=True)
        print("PORTABILITY_END", flush=True)
    print(f"PROBE_SUMMARY {catalog_n} catalog modules plus SDK template, {len(inputs)*len(FPUS)} compilations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
