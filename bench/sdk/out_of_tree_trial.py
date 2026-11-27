# SPDX-License-Identifier: GPL-3.0-only
"""Device-free SDK documentation trial; core edits exist only in disposable CI checkouts."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def new_york_date():
    """New York date without adding tzdata on stock Windows Python.

    US DST since 2007: second Sunday of March 07:00 UTC until the first
    Sunday of November 06:00 UTC. Unix runner dates are post-2007.
    """
    try:
        return dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except ZoneInfoNotFoundError:
        utc = dt.datetime.now(dt.timezone.utc)
        year = utc.year
        start_day = 8 + (6 - dt.date(year, 3, 1).weekday()) % 7
        end_day = 1 + (6 - dt.date(year, 11, 1).weekday()) % 7
        start = dt.datetime(year, 3, start_day, 7, tzinfo=dt.timezone.utc)
        end = dt.datetime(year, 11, end_day, 6, tzinfo=dt.timezone.utc)
        hours = -4 if start <= utc < end else -5
        return (utc + dt.timedelta(hours=hours)).date().isoformat()

ROOT = Path(__file__).resolve().parents[2]
PRESENTATION = "apps/studio/public/catalogue-presentation.json"
GENERATED = ("apps/studio/public/wirescape_modules.json",
             "tools/foundation/fixtures/known_module_ids.txt",
             "tools/mb1/descriptor_inventory.json")
MEMBERSHIP = "bench/module_sets.json"
MODULE = "modules/trial_gain"
DOC = "docs/MODULE_BUILD_GUIDE.md"
SDK = "docs/SDK_AUTHOR_GUIDE.md"


class Trial:
    def __init__(self, platform, output):
        self.platform, self.output = platform, output
        self.rows, self.modified = [], []

    def step(self, label, section, command, out, func, files=()):
        t = time.monotonic()
        code, stderr, stdout = 0, "", ""
        try:
            result = func()
            if isinstance(result, subprocess.CompletedProcess):
                code, stderr, stdout = result.returncode, result.stderr or "", result.stdout or ""
            elif result is not None:
                stdout = str(result)
        except Exception as error:
            code, stderr = -1, f"{type(error).__name__}: {error}"
        row = dict(n=len(self.rows)+1, label=label, doc_section=section, command=command,
                   location="out-of-tree" if out else "CI checkout",
                   status="pass" if code == 0 else "fail", returncode=code,
                   duration_seconds=round(time.monotonic()-t, 3),
                   repository_files=list(files), stderr_exact=stderr, stdout_tail=stdout[-1600:])
        self.rows.append(row)
        self.modified.extend(files)
        print(f"TRIAL STEP {row['n']:02}: {row['status']} {row['duration_seconds']:.3f}s "
              f"{label}", flush=True)
        if code: print("TRIAL EXACT ERROR:\n" + stderr[-6000:], flush=True)
        return code == 0

    def run(self, label, section, command, out=False, files=(), timeout=2300, cwd=ROOT):
        return self.step(label, section, " ".join(map(str,command)), out,
                         lambda: subprocess.run(command,cwd=cwd,text=True,capture_output=True,
                                                errors="replace",timeout=timeout), files)

    def write(self, sha):
        self.output.mkdir(parents=True,exist_ok=True)
        oot = [s for s in self.rows if s["location"] == "out-of-tree"]
        passed = sum(s["status"] == "pass" for s in oot)
        modified = list(dict.fromkeys(self.modified))
        core = [path for path in modified if path != MODULE]
        record = dict(date_ny=new_york_date(),
                      commit=sha, os=self.platform, architecture=os.environ.get("RUNNER_ARCH","unknown"),
                      audio_device="none", rate_hz=48000, block_frames=256, total_steps=len(self.rows),
                      outside_passed=passed, outside_attempted=len(oot),
                      first_outside_failure=next((s["n"] for s in oot if s["status"]=="fail"),None),
                      ephemeral_files=modified, core_files=core, module_folder_created=MODULE, steps=self.rows)
        (self.output/"trial.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
        lines=["<!-- SPDX-License-Identifier: GPL-3.0-only -->","# SDK out-of-tree module trial","",
               "| Field | Result |","|---|---|",
               f"| OS | {self.platform} |",f"| Commit | {sha} |",
               f"| Date NY | {record['date_ny']} |",
               f"| Total steps | {len(self.rows)} |",
               f"| Out-of-tree completed | {passed}/{len(oot)} |",
               f"| First out-of-tree failure step | {record['first_outside_failure']} |",
               f"| Existing core files edited in disposable checkout | {len(core)} |",
               "| Core file paths | "+", ".join(core)+" |",
               "| New module folder staged | "+MODULE+" |",
               "| Audio and MIDI devices | none |","",
               "## Steps (wall-clock durations from CI log)","",
               "| Step | Doc section | Location | Result | Seconds | Repository files needed | Command |",
               "|---|---|---|---|---:|---|---|"]
        for s in self.rows:
            command=s["command"].replace("|","&#124;")
            lines.append(f"| {s['n']} {s['label']} | {s['doc_section']} | {s['location']} | "
                         f"{s['status']} | {s['duration_seconds']:.3f} | "
                         f"{', '.join(s['repository_files']) or 'none'} | {command} |")
        lines+=["","## Exact failed commands and stderr",""]
        for s in self.rows:
            if s["status"]=="fail":
                lines += [f"### Step {s['n']} {s['label']}","", "~~~text",
                          s["stderr_exact"].rstrip() or "(no stderr)", "~~~", ""]
        lines += ["## Scope","",
                  "The module folder is discovered automatically: no engine build or registry files",
                  "are edited. Presentation, generated files, experimental membership and patch",
                  "guide edits exist in the CI checkout only; no changes are committed",
                  "to the native engine, app, Studio or documentation product tree.",
                  "CI output includes one TRIAL STEP record per row with elapsed seconds.",""]
        (self.output/"out_of_tree_trial.md").write_text("\n".join(lines),encoding="utf-8")
        print("TRIAL SUMMARY "+json.dumps({k:v for k,v in record.items() if k not in ("steps","ephemeral_files")}),flush=True)


def prepare_template(destination, template):
    shutil.copytree(template,destination)
    cpp=(destination/"module.cpp").read_text(encoding="utf-8")
    header=cpp.replace('#include "wirescape_sdk.h"',
                       '#pragma once\n#include "wirescape_sdk.h"')
    header=header.replace("example.gain2","trial.gain").replace("Example Gain","Trial Gain")
    header=header.replace("WS_REGISTER_MODULE(Gain)","")
    (destination/"dsp.h").write_text(header,encoding="utf-8")
    (destination/"module.cpp").write_text(
        '// SPDX-License-Identifier: MIT\n#include "dsp.h"\nWS_REGISTER_MODULE(Gain)\n',
        encoding="utf-8")
    # The SDK template may ship an optional external-tool manifest. It is not
    # an input to the built-in registry.
    (destination/"module.json").unlink(missing_ok=True)
    (destination/"README.md").write_text(
        "<!-- SPDX-License-Identifier: MIT -->\n# trial.gain\n"
        "Signal input audio: poly, unpatched zero. Signal output audio: poly. "
        "Parameter gain: 0..2, default 1 (unitless, linear). No saved state.\n",
        encoding="utf-8")
    (destination/"DESIGN.md").write_text(
        "<!-- SPDX-License-Identifier: MIT -->\nOriginal SDK template code. "
        "MIT licence. No upstream or external dependencies.\n",encoding="utf-8")


def add_presentation():
    path=ROOT/PRESENTATION
    data=json.loads(path.read_text(encoding="utf-8"))
    data["modules"].append(dict(id="trial.gain",name="Trial Gain",category="Utility",
        ports=[dict(id="audio",name="Audio",direction=direction,kind="signal",
                    hint="audio",poly="poly",stereo_pair=None) for direction in ("input","output")],
        parameters=[dict(id="gain",name="Gain",minimum=0,maximum=2,default=1,
                         unit="",taper="linear",step=0,decimals=3,modulatable=True)]))
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    membership=ROOT/MEMBERSHIP
    tiers=json.loads(membership.read_text(encoding="utf-8"))
    if "trial.gain" in tiers["golden_set"] or "trial.gain" in tiers["experimental"]:
        raise ValueError("trial.gain already registered")
    tiers["experimental"].append("trial.gain")
    membership.write_text(json.dumps(tiers,indent=2)+"\n",encoding="utf-8")


def describe_binary():
    candidates=[ROOT/"build/native"/sub/name for sub in ("Release","")
                for name in ("wire-describe.exe","wire-describe")]
    return next((p for p in candidates if p.is_file()),candidates[0])


def add_patch_doc():
    with (ROOT/"docs/PATCH_DESIGNER_GUIDE.md").open("a",encoding="utf-8") as f:
        f.write("\n## Trial gain (CI only)\n\n"
                "trial.gain has audio signal input (poly, unpatched zero), audio signal"
                " output (poly) and gain parameter 0..2, default 1. "
                "Wire trial.gain audio output to essentials.output audio input.\n")


def sidecar_check(out):
    possible=(ROOT/"build/native/Release/wirescape-engine.exe",
              ROOT/"build/native/wirescape-engine",
              ROOT/"build/native/wirescape-engine.exe")
    binary=next((p for p in possible if p.is_file()),possible[0])
    if not binary.is_file(): raise FileNotFoundError(binary)
    patch=dict(format="wirescape.native.patch",version=2,
               modules=[dict(id=1,module="trial.gain"),dict(id=2,module="essentials.output")],
               connections=[dict(kind="signal",**{"from":dict(module=1,port="audio")},
                                 to=dict(module=2,port="audio"))],
               outputs=[dict(module=2,port="audio",bus_channel=x) for x in (0,1)])
    process=subprocess.Popen([str(binary.resolve()),"--null-audio","--rate","48000",
                              "--block","256","--settings",str(out/"settings.json")],
                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,cwd=ROOT,bufsize=0)
    messages=[]
    def reader():
        for line in process.stdout:
            messages.append(json.loads(line))
    worker=threading.Thread(target=reader,daemon=True)
    worker.start()
    try:
        command=dict(v=0,id="trial-load",type="loadGraph",patch=patch)
        process.stdin.write(json.dumps(command).encode()+b"\n")
        process.stdin.flush()
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and not any(x.get("re")=="trial-load" for x in messages):
            if process.poll() is not None: break
            time.sleep(.04)
        hello=next((m for m in messages if m.get("type")=="hello"),None)
        reply=next((m for m in messages if m.get("re")=="trial-load"),None)
        if not hello or not reply: raise RuntimeError("Missing hello/reply: "+repr(messages[-3:]))
        if "trial.gain" not in {m["id"] for m in hello["catalogue"]["modules"]}:
            raise RuntimeError("hello did not advertise trial.gain")
        if reply.get("ok") is not True: raise RuntimeError("loadGraph refused: "+repr(reply))
        return "hello lists trial.gain and loadGraph ok=true"
    finally:
        process.stdin.close()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill();process.wait()
        worker.join(timeout=1)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform",required=True,choices=("linux-x64","windows-x64"))
    p.add_argument("--results",type=Path,default=ROOT/"bench/sdk/results")
    args=p.parse_args()
    # The trial deliberately edits engine/, modules/, apps/ and docs/ inside its working
    # tree. Never permit accidental use against an owner's local checkout.
    workspace=os.environ.get("GITHUB_WORKSPACE")
    if os.environ.get("GITHUB_ACTIONS") != "true" or not workspace:
        p.error("transient product edits are permitted only in a GitHub Actions checkout")
    if Path(workspace).resolve() != ROOT.resolve():
        p.error("GITHUB_WORKSPACE must match the CI checkout being modified")
    sha=subprocess.check_output(["git","rev-parse","HEAD"],text=True,cwd=ROOT).strip()
    out=args.results.resolve()/args.platform
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    trial=Trial(args.platform,out)
    with tempfile.TemporaryDirectory(prefix="wirescape-sdk-trial-") as tmp:
        outside=Path(tmp)
        trial.step("Copy native SDK to external directory",DOC+" §B.0 / "+SDK+" §1",
                   "copy sdk <external>/sdk",True,
                   lambda: shutil.copytree(ROOT/"sdk",outside/"sdk"))
        trial.step("Rename template to trial.gain",DOC+" §B.1-B.2 / "+SDK+" §1-§2",
                   "copy sdk/template and rename descriptor; no built-in manifest",True,
                   lambda: prepare_template(outside/"trial_gain",outside/"sdk/template"))
        (outside/"CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.20)\n"
            "project(TrialGain LANGUAGES CXX)\nenable_testing()\n"
            "set(CMAKE_CXX_STANDARD 17)\nset(CMAKE_CXX_STANDARD_REQUIRED ON)\n"
            "add_library(ws2_trial_gain SHARED trial_gain/module.cpp)\n"
            "target_include_directories(ws2_trial_gain PRIVATE sdk sdk/include)\n"
            "add_executable(trial_gain_callbacks trial_gain/tests.cpp)\n"
            "target_include_directories(trial_gain_callbacks PRIVATE sdk sdk/include)\n"
            "add_test(NAME trial_gain_callbacks COMMAND trial_gain_callbacks)\n",encoding="utf-8")
        configured=trial.run("Configure documented CMake targets outside checkout",
                  DOC+" §B.2 / "+SDK+" §1,§12",
                  ["cmake","-S",str(outside),"-B",str(outside/"build"),
                   "-DCMAKE_BUILD_TYPE=Release"],True,timeout=90,cwd=outside)
        if configured and trial.run("Build standalone SDK module and callbacks", DOC+" §B.2",
                     ["cmake","--build",str(outside/"build"),"--config","Release"],
                     True,timeout=240,cwd=outside):
            trial.run("Run standalone callback test", DOC+" §B.2",
                      ["ctest","--test-dir",str(outside/"build"),"-C","Release",
                       "--output-on-failure"],True,timeout=120,cwd=outside)
        # Stop out of tree at the first inability; run remaining tasks in a
        # disposable checkout. The committed repository is never modified.
        trial.step("Copy trial source into modules",DOC+" §B.2 / "+SDK+" §1",
                   "copy <external>/trial_gain modules/trial_gain",False,
                   lambda: shutil.copytree(outside/"trial_gain",ROOT/MODULE),files=(MODULE,))
        trial.step("Add UI presentation and experimental membership",DOC+" §B.3 / "+SDK+" §1",
                   "edit presentation sidecar and append experimental ID; no engine registration edits",
                   False,add_presentation,files=(PRESENTATION,MEMBERSHIP))
        trial.step("Add patch-facing documentation",DOC+" §B.4 / "+SDK+" §12",
                   "append trial.gain to docs/PATCH_DESIGNER_GUIDE.md",False,
                   add_patch_doc,files=("docs/PATCH_DESIGNER_GUIDE.md",))
        trial.run("Build Release engine and discover SDK module",DOC+" §B.5 / "+SDK+" §12",
                  [sys.executable,"tools/dev.py","build","--headless","--config","Release"],
                  timeout=2400)
        trial.run("Generate UI catalogue and native projection from built descriptor",DOC+" §B.3",
                  [sys.executable,"tools/gen_ui_catalogue.py","--describe",str(describe_binary())],
                  files=GENERATED)
        trial.run("Verify generated catalogue",DOC+" §B.5",
                  [sys.executable,"tools/gen_ui_catalogue.py","--check","--describe",str(describe_binary())])
        trial.run("Run native module callback tests",DOC+" §B.2,§B.5 / "+SDK+" §12",
                  ["ctest","--test-dir","build/native","-C","Release",
                   "-R","^abi2_trial_gain_tests$","--output-on-failure"],timeout=240)
        trial.step("Confirm hello and loadGraph using null sink",DOC+" §B.3,§B.5 / "+SDK+" §12",
                   "wirescape-engine --null-audio and v0 loadGraph trial.gain",False,
                   lambda: sidecar_check(out))
    trial.write(sha)
    print(out/"out_of_tree_trial.md",flush=True)
    return 0


if __name__=="__main__":
    sys.exit(main())
