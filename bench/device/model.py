# SPDX-License-Identifier: GPL-3.0-only
"""Scenario expansion and device-free ABI2 renderer script export."""
import copy
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCHES = ROOT / "apps/studio/patches"
SCENARIOS = Path(__file__).resolve().parent / "scenarios"
FAMILIES = ("basics", "chaos", "scene", "groove", "extreme", "endurance")


def read_scenario(name):
    if name not in FAMILIES:
        raise ValueError("unknown scenario: " + name)
    data = json.loads((SCENARIOS / (name + ".json")).read_text(encoding="utf-8"))
    if data["duration_s"] <= 0 or any(s["at"] < 0 or s["at"] >= data["duration_s"] for s in data["steps"]):
        raise ValueError("scenario step outside duration")
    return data


def load_patch(name):
    if Path(name).name != name or not name.endswith(".json"):
        raise ValueError("patch must be a bundled JSON basename")
    data = json.loads((PATCHES / name).read_text(encoding="utf-8"))
    if data.get("format") != "wirescape.native.patch" or data.get("version") != 2:
        raise ValueError("requires native patch v2")
    return data


def bounds(catalogue, module_type, param):
    for mod in catalogue.get("modules", []):
        if mod.get("id") == module_type:
            for d in mod.get("parameters", []):
                if d.get("id") == param:
                    return float(d["minimum"]), float(d["maximum"]), float(d.get("step", 0))
    return None


def quantize(x, lo, hi, step):
    x = min(hi, max(lo, x))
    if step > 0:
        x = lo + round((x-lo)/step)*step
    return round(min(hi, max(lo, x)), 7)


class Planner:
    def __init__(self, catalogue=None):
        self.catalogue = catalogue or {}
        self.patch = None
        self.patch_name = None
        self.timeline = []

    def emit(self, at, action, wire=None, **extra):
        item = {"at": round(at, 6), "action": action, **extra}
        if wire is not None:
            item["wire"] = wire
        self.timeline.append(item)

    def set_param(self, at, module, param, fraction):
        m = next((m for m in self.patch["modules"] if m["id"] == module), None)
        if m is None:
            raise ValueError("module not in patch")
        meta = bounds(self.catalogue, m["module"], param)
        if meta is None:
            if param not in m.get("parameters", {}):
                raise ValueError("unknown parameter without catalogue")
            value = float(m["parameters"][param])
        else:
            lo, hi, step = meta
            value = quantize(lo+(hi-lo)*fraction, lo, hi, step)
        self.emit(at, "setParam", {"type":"setParam","moduleId":module,"paramId":param,"value":value})

    def step(self, base, step):
        at = base+step["at"]
        op = step["action"]
        if op in ("load_patch", "patch_switch"):
            self.patch_name = step["patch"]
            self.patch = load_patch(self.patch_name)
            self.emit(at, op, {"type":"loadGraph","patch":copy.deepcopy(self.patch)}, patch=self.patch_name)
        elif op == "panic":
            self.emit(at, op, {"type":"panic"})
        elif op == "param_jumps":
            pairs = ([(m["id"], key) for m in self.patch["modules"] for key in m.get("parameters", {})]
                     if step.get("all_params") else [(step["module_id"],step["param"])])
            spacing = float(step.get("spacing_s", .05))
            for i,(node,param) in enumerate(pairs):
                self.set_param(at+2*i*spacing,node,param,0)
                self.set_param(at+(2*i+1)*spacing,node,param,1)
        elif op == "ramp":
            count = max(2,round(step["duration_s"]*step.get("hz",200))+1)
            for i in range(count):
                self.set_param(at+i*step["duration_s"]/(count-1),step["module_id"],step["param"],i/(count-1))
        elif op == "random_walk":
            m = next(m for m in self.patch["modules"] if m["id"] == step["module_id"])
            keys = list(m.get("parameters", {}))
            rng = random.Random(step["seed"])
            values = {key:.5 for key in keys}
            for i in range(max(1,round(step["duration_s"]*step["hz"]))):
                for key in keys:
                    values[key] = min(1,max(0,values[key]+rng.uniform(-.28,.28)))
                    self.set_param(at+i/step["hz"],m["id"],key,values[key])
        elif op == "connect_cycle":
            c = copy.deepcopy(self.patch["connections"][step["index"]])
            self.emit(at,"disconnect",{"type":"disconnect","connection":c})
            self.emit(at+.16,"connect",{"type":"connect","connection":c})
        elif op == "add_remove":
            node,kind=step["module_id"],step["module_type"]
            self.emit(at,"addModule",{"type":"addModule","moduleId":node,"moduleType":kind})
            self.emit(at+.25,"removeModule",{"type":"removeModule","moduleId":node})
        elif op == "mod_sweep":
            c=copy.deepcopy(self.patch["connections"][step["index"]])
            if c["kind"] != "modulation":
                raise ValueError("mod_sweep requires modulation cable")
            for i in range(step["steps"]):
                amount=round(-1+2*i/(step["steps"]-1),5)
                self.emit(at+step["duration_s"]*i/(step["steps"]-1),"setModAmount",
                          {"type":"setModAmount","connection":c,"amount":amount})
        elif op == "note_storm":
            for chord in range(step.get("chords",1)):
                start=at+chord*(.5 if step.get("legato") else .65)
                keys=[48+(chord*5+i)%32 for i in range(16)]
                for i,key in enumerate(keys):
                    self.emit(start+i*.006,"noteOn",{"type":"noteOn","note":key,"velocity":.8})
                for i,key in enumerate(keys):
                    self.emit(start+(.48 if step.get("legato") else .35)+i*.006,"noteOff",
                              {"type":"noteOff","note":key},release_s=.5)
            self.emit(at+step.get("chords",1)*.7+.1,"unheld-note-off",{"type":"noteOff","note":117})
        elif op == "buffer_change":
            self.emit(at,"setBufferFrames",{"type":"setBufferFrames","frames":step["frames"]})
        elif op == "midi_burst":
            self.emit(at,"midi_burst",notes=step.get("notes",[48,52,55,60]))
        else:
            raise ValueError("unknown scenario action: " + op)

    def expand(self,name,start=0.,limit=None):
        spec=read_scenario(name)
        length=float(limit if limit is not None else spec["duration_s"])
        repeat=spec.get("repeat_every_s",spec["duration_s"])
        for n in range(math.ceil(length/repeat)):
            for step in spec["steps"]:
                if n*repeat+step["at"]<length:
                    self.step(start+n*repeat,step)
        self.timeline.sort(key=lambda item:item["at"])
        return start+length


def offline_events(timeline, rate, folder):
    """Export <=128-event, <=10-second parameter/note scripts and matching source patches."""
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    files=[]
    patch=None
    patch_name=None
    events=[]

    def flush():
        if not events or patch is None:
            return
        base=events[0]["at"]
        if events[-1]["at"]-base>9:
            return
        name=f"reference-{len(files):04d}"
        script=[dict(event["entry"],frame=max(0,round((event["at"]-base)*rate))) for event in events]
        (folder/(name+".json")).write_text(json.dumps(script,indent=2),encoding="utf-8")
        (folder/(name+"-patch.json")).write_text(json.dumps(patch),encoding="utf-8")
        files.append({"script":name+".json","patch":name+"-patch.json",
                      "start_s":base,"seconds":max(.1,events[-1]["at"]-base+.15),
                      "patch_name":patch_name})

    for item in sorted(timeline,key=lambda x:x["at"]):
        wire=item.get("wire",{})
        typ=wire.get("type")
        if typ=="loadGraph":
            flush()
            events=[]
            patch=wire["patch"]
            patch_name=item.get("patch")
        elif typ in ("connect","disconnect","addModule","removeModule","setModAmount","setBufferFrames"):
            flush()
            events=[]
        elif typ in ("setParam","noteOn","noteOff") and patch is not None:
            if events and (item["at"]-events[0]["at"]>9 or len(events)>=128):
                flush()
                events=[]
            if typ=="setParam":
                entry={"node":wire["moduleId"],"type":typ,"parameter":wire["paramId"],"value":wire["value"]}
            else:
                node=next((m["id"] for m in patch["modules"] if m["module"]=="host.keyboard"),0)
                entry={"node":node,"type":typ,"key":wire["note"]}
            if entry["node"]:
                events.append({"at":item["at"],"entry":entry})
    flush()
    (folder/"index.json").write_text(json.dumps(files,indent=2),encoding="utf-8")
    return files
