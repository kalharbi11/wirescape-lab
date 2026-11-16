# SPDX-License-Identifier: GPL-3.0-only
"""Measure causal bundled-module PCM contribution by removing its signal path.

This script renders temporary control patch bytes with the existing device-free
renderer; no source patch or product file is modified. Failed interventions
remain explicit unavailable evidence, never reclassified as successful coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

from render import ROOT, binary, events_for_patch, read_pcm, render_one

# One structurally connected bundled patch per historically present runtime ID.
# osc.out has no signal output and is handled as unmeasurable PCM side effect.
CASES = {
    "essentials.vco": "basics-01-first-tone.json",
    "essentials.lfo": "basics-02-fm-filter-lfo.json",
    "essentials.vcf": "basics-02-fm-filter-lfo.json",
    "essentials.adsr": "basics-01-first-tone.json",
    "essentials.vca": "basics-01-first-tone.json",
    "essentials.clock": "basics-04-sequencer-and-quantizer.json",
    "essentials.function_envelope": "chaos-03-orbiting-iron-fx.json",
    "essentials.ladder": "scene-01-hollow-chapel.json",
    "essentials.mixer": "scene-01-hollow-chapel.json",
    "essentials.noise": "basics-05-random-melody.json",
    "essentials.output": "basics-01-first-tone.json",
    "essentials.scale_offset": "basics-08-clocked-groove.json",
    "essentials.slew": "scene-02-breathing-walls.json",
    "host.keyboard": "basics-01-first-tone.json",
    "essentials.chaos_lite": "basics-06-chaos-keys.json",
    "ports.macro_oscillator": "basics-07-macro-keys.json",
    "sequencing.groove": "basics-08-clocked-groove.json",
    "sound.blend": "scene-06-dust-reactor.json",
    "essentials.resonator": "basics-05-random-melody.json",
    "fx.delay": "basics-03-echo-and-reverb.json",
    "fx.reverb": "basics-03-echo-and-reverb.json",
    "essentials.quantizer": "basics-04-sequencer-and-quantizer.json",
    "essentials.quad_vca": "quad-vca-01-lpg-plucks.json",
    "example.random_source": "basics-05-random-melody.json",
    "example.step_sequencer": "basics-04-sequencer-and-quantizer.json",
}


def disable_module_edges(doc, target):
    """Return a source-identical graph except target-to-consumer (or Output input) cables."""
    nodes={m["id"] for m in doc["modules"] if m["module"]==target}
    if not nodes:
        raise ValueError(f"{target}: module not present")
    original=doc["connections"]
    if target=="essentials.output":
        kept=[c for c in original if c["to"]["module"] not in nodes]
        intervention="disconnect_inputs_to_output"
    else:
        kept=[c for c in original if c["from"]["module"] not in nodes]
        intervention="disconnect_module_output_edges"
    if len(original)==len(kept):
        raise ValueError(f"{target}: no removable observable cable")
    control=dict(doc)
    control["connections"]=kept
    return control, intervention, len(original)-len(kept)


def collect(root, baseline, wavs, renderer):
    if set(CASES) & {"osc.out","monitor"}:
        raise ValueError("non-PCM modules cannot be bundled-intervention targets")
    results={}
    with tempfile.TemporaryDirectory(prefix="ws-coverage-probe-") as tmp:
        work=Path(tmp)
        for index,(module,patch_name) in enumerate(sorted(CASES.items())):
            fixture=root/"apps/studio/patches"/patch_name
            record={"module_id":module,"fixture":"bundled/"+patch_name,
                    "intervention":"", "removed_cables":0, "status":"unavailable",
                    "reason":None, "control_peak_difference_fs":None}
            results[module]=record
            try:
                original_bytes=fixture.read_bytes()
                doc=json.loads(original_bytes)
                control,intervention,n=disable_module_edges(doc,module)
                record["intervention"]=intervention
                record["removed_cables"]=n
                record["fixture_sha256"]=hashlib.sha256(original_bytes).hexdigest()
                control_bytes=(json.dumps(control,sort_keys=True,separators=(",",":"))+"\n").encode()
                record["control_sha256"]=hashlib.sha256(control_bytes).hexdigest()
                control_patch=work/f"control-{index}.json"
                control_patch.write_bytes(control_bytes)
                script=work/f"events-{index}.json"
                script.write_text(json.dumps(events_for_patch(doc)),encoding="utf-8")
                row=baseline["patches"]["bundled/"+patch_name]
                if not row["rms_fs"]>1e-8:
                    raise ValueError("bundled source output is silent")
                original_wav=wavs/"bundled"/(Path(patch_name).stem+".wav")
                _,left=read_pcm(original_wav)
                _,right=render_one(renderer,control_patch,script,
                                   work/f"control-{index}.wav",root)
                delta=float(np.max(np.abs(left.astype(np.float64)-right.astype(np.float64))))
                record["output_peak_fs"]=row["peak_fs"]
                record["output_rms_fs"]=row["rms_fs"]
                record["control_peak_difference_fs"]=delta
                if delta>1e-8:
                    record["status"]="measured_pcm_intervention"
                else:
                    record["reason"]="intervention changed no output samples above 1e-8 FS"
            except (ValueError,OSError,RuntimeError,KeyError,AssertionError) as exc:
                record["reason"]=str(exc)[-350:]
            print(f"BUNDLED_PROBE {module} {patch_name} {record['status']}: "
                  f"delta={record['control_peak_difference_fs']} {record['reason'] or ''}",flush=True)
    return results


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--render",type=Path,required=True)
    p.add_argument("--wavs",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args(argv)
    root=args.root.resolve()
    exe=binary(root)
    if exe is None:
        p.error("native renderer unavailable")
    measured=json.loads(args.render.read_text(encoding="utf-8"))
    rows=collect(root,measured,args.wavs.resolve(),exe.resolve())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(rows,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(f"BUNDLED_PROBE_SUMMARY {sum(v['status']=='measured_pcm_intervention' for v in rows.values())}/{len(rows)} causally measured",flush=True)


if __name__=="__main__":
    sys.exit(main())
