#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Capture resolved CMake target closure and generated commands for M1."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ABI1 = re.compile(r"(?<![A-Za-z0-9_])(?:lib)?wirescape_engine(?![A-Za-z0-9_])", re.I)
TARGETS = ("wirescape_app_engine", "wirescape_engine_sidecar")


def capture(build, allow_abi1_baseline=False):
    reply = build / ".cmake/api/v1/reply"
    indexes = sorted(reply.glob("index-*.json"))
    if not indexes:
        raise ValueError("missing CMake codemodel index")
    index = json.loads(indexes[-1].read_text())
    codemodel = index["reply"]["codemodel-v2"]["jsonFile"]
    configurations = json.loads((reply / codemodel).read_text())["configurations"]
    config = next((c for c in configurations if c.get("name") == "Release"), configurations[0])
    entries = {t["id"]: t for t in config["targets"]}
    detail = {key: json.loads((reply / value["jsonFile"]).read_text())
              for key, value in entries.items()}
    names = {key: value["name"] for key, value in entries.items()}
    result = {"generator": index.get("cmake", {}).get("generator", {}),
              "configuration": config.get("name"),
              "revision_role": "base" if allow_abi1_baseline else "head",
              "abi1_observations": [], "closure": {}}
    for target in TARGETS:
        starts = [key for key, value in names.items() if value == target]
        if len(starts) != 1:
            raise ValueError("target missing or ambiguous: " + target)
        seen, todo, closure = set(), starts[:], []
        while todo:
            key = todo.pop()
            if key in seen:
                continue
            seen.add(key)
            node = detail[key]
            deps = [d["id"] for d in node.get("dependencies", [])]
            name = names[key]
            if name == "wirescape_engine":
                result["abi1_observations"].append(target + ": codemodel wirescape_engine")
                if not allow_abi1_baseline:
                    raise ValueError("ABI1 link dependency: " + target)
            closure.append({"name": name, "type": node.get("type"),
                            "dependencies": [names.get(d, "UNRESOLVED") for d in deps],
                            "link": node.get("link"), "artifacts": node.get("artifacts")})
            todo.extend(deps)
        result["closure"][target] = closure
    if (build / "build.ninja").is_file():
        p = subprocess.run(["ninja", "-C", str(build), "-t", "commands",
                            "wirescape_engine_sidecar"], capture_output=True,
                           text=True, check=True)
        lines = p.stdout.splitlines()
        result["generated_commands"] = [line for line in lines
                                        if any(name in line for name in TARGETS)]
        if not result["generated_commands"]:
            raise ValueError("missing generated Ninja commands")
        if any(ABI1.search(line) for line in result["generated_commands"]):
            result["abi1_observations"].append("generated Ninja command")
            if not allow_abi1_baseline:
                raise ValueError("ABI1 in generated Ninja command")
    else:
        projects = {p.stem: p for p in build.rglob("*.vcxproj") if p.stem in TARGETS}
        if set(projects) != set(TARGETS):
            raise ValueError("missing generated MSBuild projects")
        result["generated_projects"] = {
            name: {"path": str(path.relative_to(build)),
                   "xml": path.read_text(errors="replace")}
            for name, path in projects.items()}
        logs = {str(p.relative_to(build)): p.read_text(errors="replace")
                for p in build.rglob("*.tlog")
                if "link.command" in p.name.lower() and "sidecar" in str(p).lower()}
        result["sidecar_link_tlogs"] = logs
        if not logs:
            raise ValueError("missing generated sidecar link.command tlog")
        if any(ABI1.search(x["xml"]) for x in result["generated_projects"].values()):
            result["abi1_observations"].append("generated MSBuild project")
            if not allow_abi1_baseline:
                raise ValueError("ABI1 in generated MSBuild project")
        if any(ABI1.search(x) for x in logs.values()):
            result["abi1_observations"].append("generated MSBuild link command")
            if not allow_abi1_baseline:
                raise ValueError("ABI1 in generated MSBuild link command")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--allow-abi1-baseline", action="store_true",
                   help="Record expected pre-S2 ABI1 links; head remains fail-closed")
    a = p.parse_args()
    try:
        record = {"verdict": "passed", **capture(a.build.resolve(), a.allow_abi1_baseline)}
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        record = {"verdict": "failed", "error": str(exc)}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(record["verdict"], record.get("error", ""), flush=True)
    return int(record["verdict"] != "passed")


if __name__ == "__main__":
    sys.exit(main())
