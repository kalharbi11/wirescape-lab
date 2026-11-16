# SPDX-License-Identifier: GPL-3.0-only
"""Neutral registry-to-render inventory, without assuming node presence is contribution."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2]


def registry(root):
    catalogue=(root/"native/control/module_catalog.inc").read_text(encoding="utf-8")
    count=len(re.findall(r"(?m)^WS_APP_MODULE\(",catalogue))
    modules=sorted((root/"native/modules2").glob("*/module.cpp")) + \
            sorted((root/"native/sdk/examples").glob("*/module.cpp"))
    if count!=34 or len(modules)!=count:
        raise ValueError(f"registry/source inventory mismatch: catalog={count}, translation_units={len(modules)}")
    result={}
    for source in modules:
        descriptor=source.parent/"dsp.h"
        text=descriptor.read_text(encoding="utf-8")
        match=re.search(r'ws::Info\s+info\s*\{\s*"([^"]+)"',text)
        if not match:
            raise ValueError(f"descriptor has no module ID: {descriptor}")
        module_id=match.group(1)
        if module_id in result:
            raise ValueError(f"duplicate runtime ID: {module_id}")
        result[module_id]={
            "descriptor_source":descriptor.relative_to(root).as_posix(),
            "translation_unit":source.relative_to(root).as_posix(),
            "bundled_patch_names":[],
            "bundled_connected_pair_names":[],
            "coverage_fixture_names":[],
            "coverage_measurements":[],
            "contribution_status":"unverified",
        }
    return result


def render_inventory(root, rendered, run_url):
    modules=registry(root)
    patches=sorted((root/"apps/studio/patches").glob("*.json"))
    if len(patches)!=24:
        raise ValueError(f"expected 24 bundled patches, found {len(patches)}")
    observed=rendered.get("patches",{})
    pairs={}
    for path in patches:
        name=path.name
        doc=json.loads(path.read_text(encoding="utf-8"))
        ids={m["id"]:m["module"] for m in doc["modules"]}
        for module_id in sorted(set(ids.values())):
            if module_id not in modules:
                raise ValueError(f"{name}: unregistered module {module_id}")
            modules[module_id]["bundled_patch_names"].append(name)
        for connection in doc.get("connections",[]):
            a=ids[connection["from"]["module"]]
            b=ids[connection["to"]["module"]]
            pair=f'{a}.{connection["from"]["port"]} -> {b}.{connection["to"]["port"]}'
            pairs.setdefault(pair,[]).append(name)
            for module_id in (a,b):
                modules[module_id]["bundled_connected_pair_names"].append(pair)
        key="bundled/"+name
        if key not in observed:
            raise ValueError(f"golden report missing bundled patch {key}")
    manifest=json.loads((root/"bench/golden/coverage_manifest.json").read_text(encoding="utf-8"))
    cases=manifest["cases"]
    for case in cases:
        key="coverage/"+case["fixture"]
        output=observed.get(key)
        if output is None:
            raise ValueError(f"golden report missing coverage case {key}")
        path=root/"bench/patches/coverage"/case["fixture"]
        control=root/"bench/patches/coverage"/case["control"]
        if not path.is_file() or not control.is_file():
            raise ValueError(f"missing fixture/control {key}")
        for kind, input_path in (("fixture_sha256",path),("control_sha256",control)):
            actual=hashlib.sha256(input_path.read_bytes()).hexdigest()
            if output.get(kind)!=actual:
                raise ValueError(f"reported {kind} does not match fixture bytes: {key}")
        for module_id in case["targets"]:
            if module_id not in modules:
                raise ValueError(f"unregistered coverage target {module_id}")
            if module_id not in {m["module"] for m in json.loads(path.read_text())["modules"]}:
                raise ValueError(f"target missing from {key}: {module_id}")
            record={
                "fixture":key,
                "control":case["control"],
                "fixture_sha256":output["fixture_sha256"],
                "control_sha256":output["control_sha256"],
                "output_peak_fs":output["peak_fs"],
                "output_rms_fs":output["rms_fs"],
                "control_peak_difference_fs":output["control_peak_difference_fs"],
                "contribution_verified":output["contribution_verified"],
                "run_url":run_url,
            }
            modules[module_id]["coverage_measurements"].append(record)
            modules[module_id]["coverage_fixture_names"].append(key)
            if (record["contribution_verified"] and record["output_rms_fs"]>1e-8
                    and record["control_peak_difference_fs"]>1e-8):
                modules[module_id]["contribution_status"]="measured_audio_bypass_intervention"
    for row in modules.values():
        row["bundled_patch_names"].sort()
        row["bundled_connected_pair_names"]=sorted(set(row["bundled_connected_pair_names"]))
        if row["contribution_status"]=="unverified":
            row["contribution_status"]=("bundled_presence_unverified" if row["bundled_patch_names"]
                                         else "not_exercised_offline")
    return {
        "SPDX-License-Identifier":"GPL-3.0-only",
        "schema":1,
        "source_commit":rendered["engine_source_commit"],
        "fixture_source_commit":rendered["fixture_source_commit"],
        "date_et":dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
        "machine":rendered["machine"],
        "cpu":rendered["cpu"],
        "run_url":run_url,
        "bundled_patch_count":len(patches),
        "coverage_fixture_count":len(cases),
        "modules":dict(sorted(modules.items())),
        "bundled_connected_pairs":dict(sorted(
            (key,sorted(set(value))) for key,value in pairs.items())),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--render",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--run-url",required=True)
    args=p.parse_args()
    data=render_inventory(args.root.resolve(),
                          json.loads(args.render.read_text(encoding="utf-8")),args.run_url)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("COVERAGE_SUMMARY",data["machine"],"registry",len(data["modules"]),
          "bundled",data["bundled_patch_count"],"fixture",data["coverage_fixture_count"],
          "measured",sum(v["contribution_status"]=="measured_audio_bypass_intervention"
                         for v in data["modules"].values()),flush=True)
    compact=json.dumps(data,separators=(",",":"),allow_nan=False)
    for i in range(0,len(compact),1400):
        print(f"COVERAGE_CHUNK {i//1400:04d} {compact[i:i+1400]}",flush=True)
    print("COVERAGE_END",flush=True)


if __name__=="__main__":
    main()
