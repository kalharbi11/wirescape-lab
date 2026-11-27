# SPDX-License-Identifier: GPL-3.0-only
"""Repeatable MB3 drop-in trial. Never change the original checkout."""
import argparse
import difflib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

DROP_ID = "example.mb3_drop_in"
DROP_NAME = "MB3 Scratch Gain"
FOLDER = "mb3_drop_in"
ROOT = Path(__file__).resolve().parents[2]
PRESENTATION = Path("apps/studio/public/catalogue-presentation.json")

def run(args, cwd, capture=False):
    args = [str(a) for a in args]
    print("+", shlex.join(args), flush=True)
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout

def index(document):
    rows = {}
    for row in document["modules"]:
        if row["id"] in rows:
            raise ValueError("duplicate descriptor: " + row["id"])
        rows[row["id"]] = row
    return rows

def verify_discovery(document):
    rows = index(document)
    if DROP_ID not in rows:
        raise ValueError("template not discovered: " + DROP_ID)
    row = rows[DROP_ID]
    expected = {"name": DROP_NAME, "abi_version": 2, "version": 1,
                "inputs": {"audio": "signal"}, "outputs": {"audio": "signal"},
                "parameters": {"gain": 0}}
    for key, value in expected.items():
        if row.get(key) != value:
            raise ValueError("incorrect template " + key)
    details = row["parameter_details"]
    if len(details) != 1 or any(details[0].get(k) != v for k, v in
                              {"id": "gain", "minimum": 0, "maximum": 2, "default": 1}.items()):
        raise ValueError("incorrect gain range/default")
    return row

def status(root):
    return run(["git", "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"], root, True)

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def configure(source, build):
    run(["cmake", "-S", source / "native", "-B", build, "-G", "Ninja",
         "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON"], source)

def describe(source, build):
    run(["cmake", "--build", build, "--target", "wire-describe"], source)
    return json.loads(run([build / "wire-describe"], source, True))

def catalogue(source, build, overlay, report):
    # 0009 decision 7: presentation is still a separate input. The original
    # source is never edited, even in the scratch worktree. Generate in memory
    # using the production generator and a disposable presentation overlay.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "tools"))
    import gen_ui_catalogue as generator
    descriptors = generator.descriptor_index(build / "wire-describe")
    try:
        generator.generate(root=source, descriptors=descriptors)
    except ValueError as error:
        if "module ID mismatch" not in str(error):
            raise
        print("Expected presentation-sidecar mismatch (0009 decision 7):", error)
    else:
        raise ValueError("unmodified presentation unexpectedly accepted new ID")
    presentation = json.loads((source / PRESENTATION).read_text(encoding="utf-8"))
    presentation["modules"].append({
        "id": DROP_ID, "name": DROP_NAME, "category": "Utility",
        "ports": [{"id": "audio", "name": "Audio", "direction": direction,
                   "kind": "signal", "hint": "audio", "poly": "poly", "stereo_pair": None}
                  for direction in ("input", "output")],
        "parameters": [{"id": "gain", "name": "Gain", "minimum": 0,
                        "maximum": 2, "default": 1, "unit": "", "taper": "linear",
                        "step": 0, "decimals": 3, "modulatable": True}],
    })
    overlay_file = overlay / PRESENTATION
    overlay_file.parent.mkdir(parents=True)
    write_json(overlay_file, presentation)
    result = json.loads(generator.generate(root=overlay, descriptors=descriptors))
    row = index(result).get(DROP_ID)
    if row is None or row.get("legacy_parameters") != {"gain": 0} or row.get("name") != DROP_NAME:
        raise ValueError("template not discovered in generated Studio catalogue")
    write_json(report / "studio-catalogue.json", result)
    print("Generated Studio catalogue contains template using disposable presentation overlay")

def trial(source, build, overlay, report):
    if status(source):
        raise ValueError("scratch worktree is not clean")
    module = source / "modules" / FOLDER
    if module.exists():
        raise ValueError("scratch folder collides with tracked module")
    configure(source, build)
    before = describe(source, build)
    write_json(report / "before-descriptors.json", before)
    if DROP_ID in index(before):
        raise ValueError("scratch ID already registered")
    try:
        verify_discovery(before)
    except ValueError as error:
        if str(error) != "template not discovered: " + DROP_ID:
            raise
        print("Expected negative (actual compiled registry):", error)
    else:
        raise ValueError("negative discovery check did not fail")
    registry = build / "engine2/wirescape_app_engine_module_registry.cpp"
    registry_before = registry.read_text(encoding="utf-8")
    if status(source):
        raise ValueError("baseline build changed scratch source")
    # MB2 uses the descriptor only; the standalone SDK still ships a legacy
    # manifest. Do not stage that manifest as part of the native drop-in.
    shutil.copytree(source / "sdk/template", module, ignore=shutil.ignore_patterns("module.json"))
    cpp = module / "module.cpp"
    original = cpp.read_text(encoding="utf-8")
    identity = '"example.gain2","Example Gain"'
    if original.count(identity) != 1:
        raise ValueError("SDK template identity drift; review scratch rename")
    cpp.write_text(original.replace(identity, '"' + DROP_ID + '","' + DROP_NAME + '"'), encoding="utf-8")
    configure(source, build)
    after = describe(source, build)
    write_json(report / "after-descriptors.json", after)
    verify_discovery(after)
    existing = index(after)
    del existing[DROP_ID]
    if existing != index(before):
        raise ValueError("existing descriptor set or values changed")
    delta = "".join(difflib.unified_diff(registry_before.splitlines(True),
                   registry.read_text(encoding="utf-8").splitlines(True),
                   fromfile="registry-before", tofile="registry-after"))
    (report / "registry.diff").write_text(delta, encoding="utf-8")
    print(delta, end="")
    if "ws_module_entry_" + FOLDER not in delta:
        raise ValueError("generated registry did not add template symbol")
    run(["cmake", "--build", build, "--target", "ws2_" + FOLDER,
         "abi2_" + FOLDER + "_tests"], source)
    run(["ctest", "--test-dir", build, "--output-on-failure", "-R",
         "^abi2_" + FOLDER + "_tests$"], source)
    catalogue(source, build, overlay, report)
    changes = status(source)
    (report / "scratch-source-status.txt").write_text(changes, encoding="utf-8")
    print(changes, end="")
    if not changes or any(not line.startswith("?? modules/" + FOLDER + "/")
                          for line in changes.splitlines()):
        raise ValueError("source changes outside the template folder")
    shutil.rmtree(module)
    if status(source):
        raise ValueError("scratch source not clean after cleanup")
    print("PASS: native discovery and generated catalogue; existing descriptors unchanged; scratch cleaned")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    report = args.report_dir.resolve()
    if report == ROOT or ROOT in report.parents:
        parser.error("report directory must be outside checkout")
    report.mkdir(parents=True, exist_ok=True)
    initial = status(ROOT)
    with tempfile.TemporaryDirectory(prefix="mb3-") as temp:
        temp = Path(temp)
        source = temp / "source"
        run(["git", "worktree", "add", "--detach", source, "HEAD"], ROOT)
        try:
            trial(source, temp / "build", temp / "overlay", report)
        finally:
            run(["git", "worktree", "remove", "--force", source], ROOT)
            if status(ROOT) != initial:
                raise ValueError("original checkout changed")
    print("Original checkout unchanged; temporary worktree removed")

if __name__ == "__main__":
    main()
