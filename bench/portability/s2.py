# SPDX-License-Identifier: GPL-3.0-only
"""S2 measurements; ARM object-only, host state writer after prepare/reset."""
import hashlib
import json
import platform
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.portability.probe import run, sources, SHA256_TOOLCHAIN, symbol_flags

REPORT = ROOT / "build_reports/portability"


def is_double_or_softfloat(name):
    return bool(symbol_flags([name])["double_or_softfloat_symbols"] or
                re.fullmatch(r"__aeabi_(?:[ul]*[il]2[df]|[df]2[ul]*[il])", name))


def relocations(output, names):
    result = {name: [] for name in sorted(names)}
    section = None
    for line in output.splitlines():
        match = re.match(r"RELOCATION RECORDS FOR \[(.+)\]:", line)
        if match:
            section = match[1]
            continue
        fields = line.split()
        if section and len(fields) >= 3 and re.fullmatch(r"[0-9a-fA-F]+", fields[0]):
            symbol = re.sub(r"[+-]0x[0-9a-fA-F]+$", "", fields[2])
            if symbol in result:
                result[symbol].append(f"{section}+0x{int(fields[0],16):x}")
    return result


def object_size(output):
    values = [int(p[1]) for line in output.splitlines()
              if len(p := line.split()) == 4 and p[-1] == "ws_s2_dsp_size"]
    if len(values) != 1 or values[0] <= 0:
        raise ValueError("expected one nonzero DSP-size symbol")
    return values[0]


def checked(args, timeout=240):
    result = run(args, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed: {result.stderr[-4000:]}")
    return result.stdout


def compiler_info(exe):
    path = Path(shutil.which(exe)).resolve()
    return {"version": checked([exe, "--version"]).splitlines()[0],
            "executable_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def flags(source):
    result = ["-std=c++17", "-Os", "-DWS_SIMD_SCALAR", "-I", "sdk", "-I",
              "sdk/include", "-I", "sdk/examples", "-I", "."]
    if source.parent.name == "chord":
        result.append("-DWS_S2_CHORD")
    if "macro_oscillator" in source.parts:
        result += ["-I", ".tools/portability-context/eurorack",
                   "-I", ".tools/portability-context", "-I", "modules/macro_oscillator", "-DTEST", "-include",
                   "modules/macro_oscillator/rng_scope.hpp"]
    return result


def measure_symbols(obj):
    undefined = checked(["arm-none-eabi-nm", "--undefined-only", str(obj)])
    names = {p[-1] for line in undefined.splitlines() if
             len(p := line.split()) >= 2 and p[-2] in ("U", "w", "W")
             and is_double_or_softfloat(p[-1])}
    locations = relocations(checked(["arm-none-eabi-objdump", "-r", str(obj)]), names)
    demangled = {name: checked(["arm-none-eabi-c++filt", name]).strip() for name in names}
    return [{"raw": n, "demangled": demangled[n], "relocations": locations[n]}
            for n in sorted(names)]


def measure_arm_size(label, common):
    arm = REPORT / (label + ".size.o")
    checked(["arm-none-eabi-g++", "-mcpu=cortex-m7", "-mthumb", "-mfpu=fpv5-d16",
             "-mfloat-abi=hard", "-fno-exceptions", "-fno-rtti", "-DWS_S2_ARM",
             *common, "-c", "-o", str(arm)])
    return object_size(checked(["arm-none-eabi-nm", "--defined-only",
                                "--print-size", "--radix=d", str(arm)]))


def measure_host(source, rel, label, common):
    exe = REPORT / (label + ".memory")
    extras = []
    if source.parent.name in ("host_keyboard", "notes_to_cv", "midi_to_cv"):
        extras.append("engine/voice/allocator.cpp")
    if "macro_oscillator" in source.parts:
        upstream = ROOT / ".tools/portability-context"
        extras += [str(p) for p in sorted((upstream / "eurorack/plaits/dsp").rglob("*.cc"))]
        extras += [str(upstream / "eurorack/plaits/resources.cc"),
                   str(upstream / "stmlib/dsp/units.cc")]
    checked(["g++", *common, *extras, "-o", str(exe)], timeout=600)
    output = checked([str(exe)])
    lines = output.splitlines()
    if len(lines) != 5 or not lines[0].startswith("DSP "):
        raise ValueError(f"{rel}: unexpected probe output {output!r}")
    memory = []
    for line in lines[1:]:
        tag, *values = line.split()
        if tag != "MEM" or len(values) != 7:
            raise ValueError(line)
        rate, channels, large, alignment, prepared, status, written = map(int, values)
        memory.append(dict(rate=rate, channels=channels, large_bytes=large,
                           alignment=alignment, prepare_status=prepared,
                           save_status=status, written_bytes=written))
    if [(x["rate"],x["channels"]) for x in memory] != [(48000,1),(48000,8),(96000,1),(96000,8)]:
        raise ValueError(f"{rel}: incomplete matrix")
    return {"host_dsp_bytes": int(lines[0].split()[1]), "memory": memory}


def measure(source, compile_row):
    rel = source.relative_to(ROOT).as_posix()
    label = rel.replace("/", "_").removesuffix(".cpp")
    common = [*flags(source), '-DWS_S2_MODULE="' + rel + '"',
              "bench/portability/s2_memory.cpp"]
    row = {}
    errors = {}
    def capture(key, fn):
        try:
            return fn()
        except (RuntimeError, ValueError, OSError) as exc:
            errors[key] = str(exc).replace(str(ROOT), "<repo>")
            return None
    # Never turn a missing cross-object into zero symbol references. Preserve
    # the original compiler error and still attempt both sizeof and host data.
    if compile_row["compiles"]:
        obj = REPORT / "objects/fpv5-d16" / (label + ".o")
        row["symbols"] = capture("symbols", lambda: measure_symbols(obj))
    else:
        errors["symbols"] = compile_row["first_error"]
        row["symbols"] = None
    row["arm_dsp_bytes"] = capture("arm_size", lambda: measure_arm_size(label, common))
    host = capture("host", lambda: measure_host(source, rel, label, common))
    row.update(host if host is not None else {"host_dsp_bytes": None, "memory": []})
    row["errors"] = errors
    return row


def header(title, metadata):
    return ["<!-- SPDX-License-Identifier: GPL-3.0-only -->", "# " + title, "",
            *[f"- {key}: {value}" for key, value in metadata.items()], ""]


def main():
    original = json.loads((REPORT / "modules.json").read_text())
    meta = {"Commit": original["commit"], "Date (New York)": original["date_et"],
            "Machine": platform.machine() + " hosted Linux; Cortex-M7 object target",
            "Host compiler": compiler_info("g++"),
            "ARM compiler": compiler_info("arm-none-eabi-g++"),
            "ARM archive SHA-256": SHA256_TOOLCHAIN}
    result = {}
    inputs, count = sources()
    for source in inputs:
        rel = source.relative_to(ROOT).as_posix()
        if source.parent.name == "template":
            continue
        result[rel] = measure(source, original["modules"][rel]["fpv5-d16"])
        errors = result[rel]["errors"]
        print("S2", rel, "partial" if errors else "measured", flush=True)
        for stage, error in errors.items():
            print(f"S2_ERROR {rel} {stage}: {error[:1000]}", flush=True)
    if len(result) != count:
        raise RuntimeError("catalogue row count mismatch")
    (REPORT / "s2.json").write_text(json.dumps({"metadata":meta,"modules":result},indent=2)+"\n")
    symbols = header("Cortex-M7 fpv5-d16 double and soft-float references", meta)
    symbols += ["Object relocations, section + hexadecimal byte offset; no linked firmware.",
                "", "| Source | Symbol (demangled) | Relocations |", "|---|---|---|"]
    memory = header("Module memory measurements", meta)
    memory += ["DSP sizeof excludes SDK wrapper. Host extra memory hook at block 256, seed 1,",
               "empty config except Chord LE instance tag 1; alignment defaults to SDK 32 if no hook.",
               "State measured after prepare/reset",
               "with capped counting writer; status: 0 OK, 1 INVALID, 2 CAPACITY, 3 UNSUPPORTED,",
               "4 EXCEPTION, 5 STATE. Non-success statuses are not saved-state sizes.", "",
               "| Source | DSP x64 B | DSP M7 B | Hz | Ch | LARGE B | Alignment B | Prepare status | Save status | Written B | Cap |",
               "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for rel, row in result.items():
        if row["symbols"] is None:
            symbols.append(f"| {rel} | unmeasured | compiler/tool failure; see s2.json |")
        else:
            for s in row["symbols"] or [{"demangled":"none", "relocations":[]}]:
                symbols.append(f"| {rel} | {s['demangled']} | {', '.join(s['relocations']) or 'none shown'} |")
        arm = row["arm_dsp_bytes"] if row["arm_dsp_bytes"] is not None else "unmeasured"
        if not row["memory"]:
            memory.append(f"| {rel} | unmeasured | {arm} | — | — | — | — | — | — | — | host unmeasured |")
        for m in row["memory"]:
            status = m["save_status"]
            cap = "under/equal" if status == 0 else "not saved"
            if rel == "modules/delay/module.cpp" and m["rate"] == 96000 and status == 2 and m["prepare_status"] == 0 and m["written_bytes"] == 0:
                declared = 144 + 8 * (2 * m["rate"] + 8)
                cap = f"over (formula {declared:,} B; preflight refusal)"
            memory.append(f"| {rel} | {row['host_dsp_bytes']} | {arm} | "
                          f"{m['rate']} | {m['channels']} | {m['large_bytes']} | {m['alignment']} | "
                          f"{m['prepare_status']} | {status} | {m['written_bytes']} | {cap} |")
    (REPORT / "s2_symbols.md").write_text("\n".join(symbols)+"\n")
    (REPORT / "module_memory.md").write_text("\n".join(memory)+"\n")
    return int(any(row["errors"] for row in result.values()))


if __name__ == "__main__":
    sys.exit(main())
