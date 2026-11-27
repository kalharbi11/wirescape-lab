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
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.gate.instructions import (RATE, FRAMES, binary, difference, modules)  # noqa: E402
from bench.golden.inventory import registry  # noqa: E402

DUMMY_ID = "test.mb2_isolation_dummy"
DUMMY_FOLDER = ROOT / "modules/mb2_isolation_dummy"


def build_targets(build):
    subprocess.run(["cmake", "--build", str(build), "--config", "Release",
                    "--target", "wire-describe", "abi2_module_cpu_probe"],
                   cwd=ROOT, check=True, timeout=600)


def object_files(build, expected):
    found = {}
    for path in build.rglob("module.cpp.o"):
        target = next((part.removeprefix("ws_builtin_").removesuffix(".dir")
                       for part in path.parts
                       if part.startswith("ws_builtin_") and part.endswith(".dir")), None)
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


def measure(probe, ident, voices, valgrind):
    def command(n):
        return [probe, "--module", ident, "--rate", RATE, "--block", FRAMES,
                "--channels", voices, "--instances", 1,
                "--seconds", n * FRAMES / RATE]
    return difference(command, valgrind, module_probe={
        "module": ident, "channels": voices, "instances": 1,
        "sample_rate": RATE, "block": FRAMES})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build/native")
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true" or sys.platform != "linux":
        parser.error("requires an ephemeral Linux GitHub Actions checkout")
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
                                   equal=old["ir_per_block"] == new["ir_per_block"])
                    except (RuntimeError, ValueError, OSError) as error:
                        row.update(equal=False, error=str(error))
                    rows.append(row)
            failures = [row for row in rows if not row["equal"]]
            result = {"existing_modules": len(ids), "object_bytes_changed": changed,
                      "descriptor_rows_changed": descriptor_changes,
                      "instruction_rows": len(rows), "instruction_failures": failures,
                      "pass": not changed and not descriptor_changes and not failures}
            print("MB2_ISOLATION " + json.dumps(result, sort_keys=True), flush=True)
            return 0 if result["pass"] else 1
        finally:
            shutil.rmtree(DUMMY_FOLDER)


if __name__ == "__main__":
    sys.exit(main())
