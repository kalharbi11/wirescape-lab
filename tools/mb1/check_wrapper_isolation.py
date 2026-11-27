# SPDX-License-Identifier: GPL-3.0-only
"""MB2/CAT-1: device-off scratch add/remove test for per-module codegen.

Run only on an ephemeral Linux Actions checkout with a Release build. Recompile
every existing module after adding a new folder; compare actual object bytes,
complete compiled descriptor rows and the existing two-length Callgrind module
workload. No threshold, workload, module set or golden fixture is changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.gate.instructions import (RATE, FRAMES, COUNTS, binary, callgrind, modules)  # noqa: E402
from bench.golden.inventory import registry  # noqa: E402

DUMMY_ID = "test.mb2_isolation_dummy"
DUMMY_FOLDER = ROOT / "modules/mb2_isolation_dummy"


def build_targets(build):
    subprocess.run(["cmake", "--build", str(build), "--config", "Release",
                    "--target", "wire-describe", "abi2_module_cpu_probe"],
                   cwd=ROOT, check=True, timeout=600)


def object_files(build, expected):
    found = {}
    for path in build.rglob("*.cpp.o"):
        # Fallback uses the archive's generated, separate wrapper objects.
        # The old per-folder target shape is also understood for diagnosis.
        if ("wirescape_app_engine_builtin_modules.dir" in path.parts
                and "wirescape_app_engine_generated_modules" in path.parts):
            target = path.name.removesuffix(".cpp.o")
        elif path.name == "module.cpp.o":
            target = next((part.removeprefix("ws_builtin_").removesuffix(".dir")
                           for part in path.parts
                           if part.startswith("ws_builtin_") and part.endswith(".dir")), None)
        else:
            target = None
        if target is None:
            continue
        if target in found:
            raise RuntimeError(f"multiple built-in wrapper objects for {target}")
        found[target] = path
    if set(found) != expected:
        raise RuntimeError(f"wrapper inventory mismatch: missing={sorted(expected-set(found))}, "
                           f"extra={sorted(set(found)-expected)}")
    return found


def hashes(files):
    return {name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in files.items()}


def descriptors(executable):
    result = subprocess.run([str(executable)], cwd=ROOT, check=True,
                            text=True, capture_output=True, timeout=30)
    rows = json.loads(result.stdout)["modules"]
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise RuntimeError("duplicate live module ID")
    if list(by_id) != sorted(by_id):
        raise RuntimeError("live registry not ordered by ID")
    return by_id


def wrapper_cost(path):
    """Inclusive Ir of the one actual descriptor process callback.

    Callgrind cost lines following calls= belong to the caller's inclusive
    cost, as do its ordinary self-cost lines. Inline frames are still the
    enclosing function. Do not count nested lambda functions a second time.
    """
    names = {}
    costs = {}
    current = None
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        if line.startswith("positions:") and line.split()[1:] != ["line"]:
            raise ValueError("unexpected Callgrind positions")
        if line.startswith("events:") and line.split()[1:] != ["Ir"]:
            raise ValueError("unexpected Callgrind events")
        if line.startswith(("fn=", "cfn=")):
            key, name = line.split("=", 1)
            match = re.fullmatch(r"\((\d+)\)(?: (.*))?", name)
            if match:
                index, label = match.groups()
                if label is not None:
                    names[index] = label
                if index not in names:
                    raise ValueError("undefined Callgrind function reference")
                name = names[index]
            if key == "fn":
                current = name
        elif current and re.fullmatch(r"(?:\d+|[+-]\d+|\*)(?:\s+\d+)?", line):
            fields = line.split()
            costs[current] = costs.get(current, 0) + (int(fields[1]) if len(fields) == 2 else 0)
    candidates = []
    for name, ir in costs.items():
        if name.startswith("_ZN2ws6Module"):
            name = subprocess.run(["c++filt", name], check=True, text=True,
                                  capture_output=True, timeout=10).stdout.strip()
        if re.fullmatch(r"ws::Module<.*>::process\([^)]*\)(?: \[clone [^\]]+\])?", name) and ir:
            candidates.append((name, ir))
    if len(candidates) != 1 or candidates[0][1] <= 0:
        raise ValueError(f"expected one measured wrapper process callback, got {candidates}")
    return candidates[0]


def measure(probe, ident, voices, valgrind):
    # The exact same two probe commands and validation as instructions.difference;
    # retain their raw files long enough to measure the wrapper independently.
    totals, wrapper_totals, names = [], [], []
    with tempfile.TemporaryDirectory(prefix="ws-mb2-wrapper-ir-") as tmp:
        for index, n in enumerate(COUNTS):
            duration = n * FRAMES / RATE
            output = Path(tmp) / f"{index}.callgrind"
            command = [probe, "--module", ident, "--rate", RATE,
                       "--block", FRAMES, "--channels", voices,
                       "--instances", 1, "--seconds", duration]
            expected = {"module": ident, "channels": voices, "instances": 1,
                        "sample_rate": RATE, "block": FRAMES, "blocks": n,
                        "seconds": duration}
            totals.append(callgrind(command, output, valgrind, expected_probe=expected))
            name, ir = wrapper_cost(output)
            names.append(name)
            wrapper_totals.append(ir)
    delta = totals[1] - totals[0]
    wrapper_delta = wrapper_totals[1] - wrapper_totals[0]
    if names[0] != names[1] or delta <= 0 or wrapper_delta <= 0 or wrapper_delta > delta:
        raise ValueError("invalid wrapper/whole-probe two-length difference")
    blocks = COUNTS[1] - COUNTS[0]
    return {"ir_per_block": delta / blocks, "totals": totals,
            "wrapper_ir_per_block": wrapper_delta / blocks,
            "wrapper_totals": wrapper_totals, "wrapper_function": names[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build/native")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true" or sys.platform != "linux":
        parser.error("requires an ephemeral Linux GitHub Actions checkout")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    build = args.build_dir.resolve()
    if not (build / "CMakeCache.txt").is_file():
        parser.error("configure and build Release targets first")
    if DUMMY_FOLDER.exists():
        parser.error("dummy module folder already exists; refusing to modify it")
    valgrind = shutil.which("valgrind")
    if not valgrind:
        parser.error("valgrind not installed")
    ids = modules()
    folders = {Path(row["translation_unit"]).parent.name for row in registry(ROOT).values()}
    if len(ids) != len(folders):
        raise RuntimeError("descriptor/folder mapping is not one-to-one")
    build_targets(build)
    before_files = object_files(build, folders)
    before_hashes = hashes(before_files)
    before_desc = descriptors(binary(build, "wire-describe"))
    if set(before_desc) != set(ids):
        raise RuntimeError("before registry does not match gate IDs")
    with tempfile.TemporaryDirectory(prefix="ws-mb2-isolation-") as temp:
        baseline = Path(temp) / "baseline_probe"
        shutil.copy2(binary(build, "abi2_module_cpu_probe"), baseline)
        try:
            DUMMY_FOLDER.mkdir()
            source = (ROOT / "sdk/template/module.cpp").read_text(encoding="utf-8")
            if source.count("example.gain2") != 1:
                raise RuntimeError("SDK template ID changed; update scratch witness explicitly")
            (DUMMY_FOLDER / "module.cpp").write_text(
                source.replace("example.gain2", DUMMY_ID), encoding="utf-8")
            # Force a genuine rebuild of each old module, not merely a comparison
            # of objects that the incremental build happened not to touch.
            for path in before_files.values():
                path.unlink()
            build_targets(build)
            after_files = object_files(build, folders | {DUMMY_FOLDER.name})
            after_hashes = hashes(after_files)
            changed = sorted(name for name in folders
                             if before_hashes[name] != after_hashes[name])
            after_desc = descriptors(binary(build, "wire-describe"))
            if set(after_desc) != set(ids) | {DUMMY_ID}:
                raise RuntimeError("scratch module was not uniquely discovered")
            descriptor_changes = sorted(ident for ident in ids
                                        if before_desc[ident] != after_desc[ident])
            probe = binary(build, "abi2_module_cpu_probe")
            rows = []
            for ident in ids:
                for voices in (1, 8):
                    row = {"module": ident, "voices": voices}
                    try:
                        old = measure(baseline, ident, voices, valgrind)
                        new = measure(probe, ident, voices, valgrind)
                        row.update(before_ir=old["ir_per_block"],
                                   after_ir=new["ir_per_block"],
                                   before_totals=old["totals"], after_totals=new["totals"],
                                   before_wrapper_ir=old["wrapper_ir_per_block"],
                                   after_wrapper_ir=new["wrapper_ir_per_block"],
                                   before_wrapper_totals=old["wrapper_totals"],
                                   after_wrapper_totals=new["wrapper_totals"],
                                   before_wrapper_function=old["wrapper_function"],
                                   after_wrapper_function=new["wrapper_function"],
                                   wrapper_equal=(old["wrapper_ir_per_block"] == new["wrapper_ir_per_block"]
                                                  and old["wrapper_function"] == new["wrapper_function"]),
                                   probe_equal=old["ir_per_block"] == new["ir_per_block"],
                                   equal=(old["wrapper_ir_per_block"] == new["wrapper_ir_per_block"]
                                          and old["wrapper_function"] == new["wrapper_function"]
                                          and old["ir_per_block"] == new["ir_per_block"]))
                    except (RuntimeError, ValueError, OSError) as error:
                        row.update(equal=False, error=str(error))
                    rows.append(row)
            failures = [row for row in rows if not row["equal"]]
            result = {"existing_modules": len(ids), "object_bytes_changed": changed,
                      "descriptor_rows_changed": descriptor_changes,
                      "instruction_rows": len(rows), "instruction_failures": failures,
                      "pass": not changed and not descriptor_changes and not failures}
            # Persist the entire table, including unchanged rows and raw length totals.
            result["object_rows"] = [{"folder": name, "before": before_hashes[name],
                                      "after": after_hashes[name],
                                      "equal": before_hashes[name] == after_hashes[name]}
                                     for name in sorted(folders)]
            result["descriptor_rows"] = [{"id": ident, "before": before_desc[ident],
                                          "after": after_desc[ident],
                                          "equal": before_desc[ident] == after_desc[ident]}
                                         for ident in sorted(ids)]
            result["instruction_table"] = rows
            result["head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                             text=True, capture_output=True,
                                             check=True, timeout=10).stdout.strip()
            output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
            print("MB2_ISOLATION " + json.dumps(
                {k: v for k, v in result.items() if k not in
                 ("object_rows", "descriptor_rows", "instruction_table")}, sort_keys=True),
                flush=True)
            return 0 if result["pass"] else 1
        finally:
            shutil.rmtree(DUMMY_FOLDER)


if __name__ == "__main__":
    sys.exit(main())
