# SPDX-License-Identifier: GPL-3.0-only
"""Owner-gated Wirescape sidecar stress runner; dry-run never opens devices."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from model import FAMILIES, Planner, ROOT, offline_events, read_scenario
from analyse import report

HERE=Path(__file__).resolve().parent


class EventLog:
    def __init__(self,path):
        self.file=Path(path).open("w",encoding="utf-8",buffering=1)
        self.lock=threading.Lock()
        self.events=[]
        self.epoch=time.monotonic()

    def add(self,direction,payload=None,**extra):
        event={"monotonic_ns":time.monotonic_ns(),
               "elapsed_s":round(time.monotonic()-self.epoch,6),
               "direction":direction,**extra}
        if payload is not None:event["payload"]=payload
        with self.lock:
            self.file.write(json.dumps(event,ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n")
            self.events.append(event)
        return event

    def close(self):
        self.file.close()


class Engine:
    """Request/reply correlation, status capture and clean owned-process shutdown."""
    def __init__(self,args,folder,log):
        self.args=args
        self.folder=folder
        self.log=log
        self.process=None
        self.pending={}
        self.lock=threading.Condition()
        self.hello=None
        self.closed=False
        self.counter=0
        self.fake=args.dry_run and not args.engine
        self.generation=0

    def start(self):
        if self.fake:
            self.hello={"v":0,"type":"hello","session":"fake-dry-run",
                        "catalogue":{"modules":[]},"capabilities":["setBufferFrames"],
                        "audio":{"state":"null"}}
            self.log.add("out",self.hello)
            self.log.add("out",{"v":0,"type":"status",
                      "status":{"audio":{"state":"null","cpuPercent":0.,
                                          "dropouts":0,"sampleRate":self.args.rate,
                                          "bufferFrames":self.args.block}}})
            self.log.add("out",{"v":0,"type":"telemetry","telemetry":{}})
            return
        cmd=[str(self.args.engine),"--settings",str(self.folder/"settings.json"),
             "--rate",str(self.args.rate),"--block",str(self.args.block)]
        if self.args.dry_run:
            cmd.append("--null-audio")
        else:
            cmd.append("--confirm-audio")
            if self.args.confirm_midi:cmd.append("--confirm-midi")
            if self.args.device:cmd+=["--device",self.args.device]
        self.process=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,bufsize=0)
        threading.Thread(target=self._read,daemon=True).start()
        threading.Thread(target=self._stderr,daemon=True).start()
        end=time.monotonic()+15
        with self.lock:
            while self.hello is None and time.monotonic()<end:
                if self.closed:break
                self.lock.wait(timeout=max(0,end-time.monotonic()))
            if self.hello is None:
                raise RuntimeError("engine did not emit hello; inspect engine-stderr.log")

    def _read(self):
        try:
            for raw in self.process.stdout:
                if len(raw)>2097153:
                    raise RuntimeError("protocol line over 2 MiB")
                payload=json.loads(raw.decode("utf-8"))
                self.log.add("out",payload)
                with self.lock:
                    if payload.get("type")=="hello":self.hello=payload
                    if "re" in payload:
                        item=self.pending.get(payload["re"])
                        if item is not None:
                            item["reply"]=payload
                            item["at"]=time.monotonic()
                    self.lock.notify_all()
        except (UnicodeError,json.JSONDecodeError,RuntimeError) as error:
            self.log.add("protocol-error",message=str(error))
        finally:
            with self.lock:
                self.closed=True
                self.lock.notify_all()

    def _stderr(self):
        # Driver diagnostics may contain paths; keep outside manifest and require redaction.
        with (self.folder/"engine-stderr.log").open("wb") as f:
            for line in self.process.stderr:f.write(line)

    def send(self,payload,timeout=25,*,on_write=None):
        self.counter+=1
        request={"v":0,"id":f"b{self.counter}","type":payload["type"],
                 **{k:v for k,v in payload.items() if k!="type"}}
        line=json.dumps(request,ensure_ascii=False,allow_nan=False,separators=(",",":"))
        if len(line.encode("utf-8"))>2097152:
            raise RuntimeError("command exceeded wire limit")
        started=time.monotonic()
        with self.lock:self.pending[request["id"]]={"sent":started}
        self.log.add("in",request)
        if self.fake:
            if on_write is not None:
                on_write(time.monotonic())
            if request["type"] in ("loadGraph","addModule","removeModule","connect",
                                   "disconnect","setModAmount"):
                self.generation+=1
            answer={"v":0,"session":"fake-dry-run","re":request["id"],
                    "ok":True,"gen":str(self.generation)}
            if request["type"] in ("listAudioDevices","listMidiDevices"):
                answer["result"]={"devices":[]}
            self.log.add("out",answer)
            if self.counter%150==0:
                self.log.add("out",{"v":0,"type":"status","status":{
                    "audio":{"state":"null","cpuPercent":0.,"dropouts":0,
                             "sampleRate":self.args.rate,"bufferFrames":self.args.block}}})
                self.log.add("out",{"v":0,"type":"telemetry","telemetry":{}})
            with self.lock:self.pending.pop(request["id"],None)
            self.log.add("ack",re=request["id"],latency_ms=round((time.monotonic()-started)*1000,4))
            return answer
        with self.lock:
            if self.closed:raise RuntimeError("engine closed stdout")
            if on_write is not None:
                # Timestamp the physical command write, not send() entry or ack.
                on_write(time.monotonic())
            self.process.stdin.write(line.encode("utf-8")+b"\n")
            self.process.stdin.flush()
            deadline=time.monotonic()+timeout
            while self.pending[request["id"]].get("reply") is None:
                if self.closed:raise RuntimeError("engine exited before reply")
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    raise TimeoutError("engine did not acknowledge "+request["type"])
                self.lock.wait(timeout=remaining)
            item=self.pending.pop(request["id"])
        answer=item["reply"]
        self.log.add("ack",re=request["id"],latency_ms=round((item["at"]-started)*1000,4))
        if not answer.get("ok"):
            raise RuntimeError(f"engine refused {request['type']}: {answer.get('code','?')} {answer.get('message','')}")
        return answer

    def stop(self):
        if not self.process:return
        try:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
            self.process.wait(timeout=12)
        except (subprocess.TimeoutExpired,OSError):
            self.process.kill()
            self.process.wait()
        if self.process.returncode!=0:
            self.log.add("engine-exit",code=self.process.returncode)


def locate(name):
    exe=name+(".exe" if os.name=="nt" else "")
    for parent in ("build/native","build/native/Release","build/native/Debug",
                   "build","build/Release"):
        path=ROOT/parent/exe
        if path.is_file():return path
    binary=shutil.which(name)
    return Path(binary) if binary else None


def commit_sha():
    try:
        return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True,
                                       stderr=subprocess.DEVNULL,timeout=3).strip()
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired):
        return os.environ.get("GITHUB_SHA","unknown")


def choose_scenarios(args,planner):
    t=0.
    if args.scenario in FAMILIES:
        t=planner.expand(args.scenario)
    elif args.scenario=="all":
        for family in FAMILIES:t=planner.expand(family,t)
    else:
        limit=900. if args.scenario=="quick" else 3600.
        while t<limit:
            for family in FAMILIES:
                if t>=limit:break
                duration=min(limit-t,read_scenario(family)["duration_s"])
                t=planner.expand(family,t,limit=duration)
    return t


def run_references(folder,index,rate,block,executable):
    if not executable:return []
    result=[]
    for item in index:
        script=folder/item["script"]
        patch=folder/item["patch"]
        dest=folder/(script.stem+".wav")
        cmd=[str(executable),"--patch",str(patch),"--script",str(script),
             "--out",str(dest),"--rate",str(rate),"--block",str(block),
             "--seconds",str(min(10,item["seconds"])),"--seed","37"]
        completed=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,text=True,timeout=25)
        if completed.returncode==0:
            result.append({**item,"audio":str(dest)})
        else:
            result.append({**item,"error":completed.stderr.strip()[:400]})
    return result


class MidiSource:
    def __init__(self,args,log):
        self.args=args
        self.log=log
        self.port=None

    def start(self):
        if self.args.dry_run or not self.args.confirm_midi:return
        import mido
        if self.args.manual_midi:
            if not self.args.midi_port:
                raise RuntimeError("--manual-midi requires --midi-port (controller input)")
            def callback(message):
                self.log.add("midi-in",message=str(message))
            self.port=mido.open_input(self.args.midi_port,callback=callback)
        elif os.name=="nt":
            if not self.args.midi_port:
                raise RuntimeError("Windows requires --midi-port (existing loopMIDI port)")
            self.port=mido.open_output(self.args.midi_port)
        else:
            self.port=mido.open_output(self.args.midi_port or "Wirescape Bench",virtual=True)

    def burst(self,notes):
        if self.args.dry_run:
            self.log.add("midi-fake",notes=notes)
            return
        if self.args.manual_midi:
            self.log.add("midi-manual",message="owner plays controller; no generated MIDI")
            return
        import mido
        for note in notes:
            self.port.send(mido.Message("note_on",note=int(note),velocity=80))
        time.sleep(.15)
        for note in notes:
            self.port.send(mido.Message("note_off",note=int(note),velocity=0))

    def close(self):
        if self.port:self.port.close()


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario",choices=["all","quick","full",*FAMILIES],default="quick")
    p.add_argument("--dry-run",action="store_true",help="null sink + fake MIDI; no device access")
    p.add_argument("--speaker-check",action="store_true",help="play an owner-confirmed 440 Hz calibration tone for five seconds; real playback requires --confirm-audio")
    p.add_argument("--engine",type=Path,help="sidecar executable; if absent in dry-run, simulate protocol")
    p.add_argument("--confirm-audio",action="store_true")
    p.add_argument("--confirm-midi",action="store_true")
    p.add_argument("--device",help="owner-selected real audio device ID")
    p.add_argument("--midi-port",help="existing loopMIDI output (Windows) or manual input")
    p.add_argument("--manual-midi",action="store_true")
    p.add_argument("--record",choices=["none","monitor","process-loopback","input"],default="none")
    p.add_argument("--monitor-target")
    p.add_argument("--input-device")
    p.add_argument("--process-helper",type=Path)
    p.add_argument("--rate",type=int,choices=(44100,48000,96000),default=48000)
    p.add_argument("--block",type=int,choices=(64,128,256,512,1024),default=256)
    p.add_argument("--machine",default="device",help="anonymous label, never hostname")
    p.add_argument("--results",type=Path,default=HERE/"results")
    p.add_argument("--render",type=Path,help="optional wirescape_render for offline WAV references")
    return p


def main(argv=None):
    p=parser()
    args=p.parse_args(argv)
    # Authorization must be checked before importing or opening any audio/MIDI backend.
    if not args.dry_run and not args.confirm_audio:
        p.error("--confirm-audio is required; no device has been opened")
    if args.dry_run and (args.confirm_audio or args.confirm_midi or args.manual_midi
                         or args.record!="none"):
        p.error("--dry-run prohibits authorization flags, manual MIDI and recording")
    if args.manual_midi and not args.confirm_midi:
        p.error("--manual-midi requires --confirm-midi")
    if args.speaker_check and (args.confirm_midi or args.manual_midi or args.record!="none"):
        p.error("--speaker-check does not use MIDI or capture; pass only --confirm-audio for real playback")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}",args.machine):
        p.error("--machine must be an anonymous 1-48 character label (letters, digits, _ or -)")
    if args.engine and not args.engine.is_file():
        p.error("--engine path does not exist")
    if args.dry_run and not args.engine:
        args.engine=locate("wirescape-engine")
    if not args.dry_run and not args.engine:
        args.engine=locate("wirescape-engine")
        if args.engine is None:
            p.error("wirescape-engine not found; specify --engine")
    date=dt.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    sha=commit_sha()
    base=args.results/args.machine/(date+"-"+sha[:7])
    folder=base
    suffix=1
    while folder.exists():
        folder=Path(str(base)+f"-{suffix}")
        suffix+=1
    folder.mkdir(parents=True)
    log=EventLog(folder/"events.ndjson")
    engine=source=recorder=None
    capture=None
    error=None
    manifest={"schema":1,"machine":args.machine,"os":platform.system(),
              "os_version":platform.release(),
              "cpu":platform.processor() or platform.machine(),"commit":sha,
              "rate":args.rate,"block":args.block,"audio_device":args.device or "default",
              "driver":"null" if args.dry_run else "unknown",
              "capture_backend":args.record,
              "dry_run":args.dry_run,"scenario":args.scenario,
              "engine_mode":("simulation" if args.dry_run and not args.engine
                             else "null-audio" if args.dry_run else "device"),
              "warnings":[]}
    if manifest["engine_mode"]=="simulation":
        manifest["warnings"].append(
            "No engine binary: simulated acknowledgements, not actual sidecar validation")
    if args.speaker_check:
        from speaker_check import run_check
        manifest["scenario"]="speaker-check"
        error=None
        try:
            observation=run_check(args,folder,log,Engine)
            manifest["speaker_check"]=observation
        except (RuntimeError, OSError, ValueError, TimeoutError) as exc:
            error=str(exc)
            log.add("speaker-check-error",message=error)
            manifest["warnings"].append("Speaker check incomplete: "+error)
        finally:
            manifest["completed"]=error is None
            (folder/"manifest.json").write_text(
                json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
            (folder/"report.md").write_text(
                "<!-- SPDX-License-Identifier: GPL-3.0-only -->\n# Speaker check\n\n"
                + "Mode: "+manifest["engine_mode"]+"\n\n"
                + "Owner observation: owner-observations.json\n\n"
                + ("Status: complete\n" if error is None else "Status: incomplete: "+error+"\n"),
                encoding="utf-8")
            log.close()
            print(folder/"report.md")
        if error:
            print("speaker check: "+error,file=sys.stderr)
            return 1
        return 0
    analysis={"recording":None,"signal_metrics":"not measured"}
    try:
        source=MidiSource(args,log)
        preliminary=Planner()
        choose_scenarios(args,preliminary)
        has_midi=any(i["action"]=="midi_burst" for i in preliminary.timeline)
        if has_midi and not args.dry_run and not args.confirm_midi:
            raise RuntimeError("MIDI scenario requires --confirm-midi; no MIDI device opened")
        if has_midi and not args.dry_run and not args.manual_midi and os.name=="nt" and not args.midi_port:
            raise RuntimeError("Windows MIDI scenario requires --midi-port loopMIDI port")
        source.start()
        engine=Engine(args,folder,log)
        engine.start()
        if has_midi and not args.dry_run and not args.manual_midi:
            devices=engine.send({"type":"listMidiDevices"}).get("result",{}).get("devices",[])
            wanted=args.midi_port or "Wirescape Bench"
            matches=[d for d in devices if wanted in (d.get("id"),d.get("name"),d.get("system_name"))
                     or wanted in str(d.get("name",""))]
            if len(matches)!=1:
                raise RuntimeError("MIDI output is not uniquely visible to engine; verify --midi-port")
            engine.send({"type":"setMidiEnabled","deviceId":matches[0]["id"],"on":True})
        planner=Planner(engine.hello.get("catalogue",{}))
        total=choose_scenarios(args,planner)
        timeline=planner.timeline
        scripts=offline_events(timeline,args.rate,folder/"offline_scripts")
        manifest["offline_script_count"]=len(scripts)
        manifest["planned_duration_s"]=total
        if not args.dry_run:
            from record import Recorder
            recorder=Recorder(args.record,folder,args.rate,args.input_device,
                              args.monitor_target,args.process_helper,engine.process.pid)
            recorder.start()
        started=time.monotonic()
        real_null_sink=args.dry_run and engine.process is not None
        # The null sink renders in real time. Running 600 seconds of events as
        # one instantaneous burst overfills its bounded event queue and tests
        # producer overload rather than the device-free scenario protocol.
        # Compress the nominal timeline but cap request rate at ~333/s.
        dry_run_scale=100.0
        dry_run_min_spacing=.003
        previous_dispatch=started-dry_run_min_spacing
        if real_null_sink:
            manifest["dry_run_clock_scale"]=dry_run_scale
            manifest["dry_run_min_command_interval_ms"]=dry_run_min_spacing*1000
        capture_offset=(log.epoch-recorder.started) if recorder and recorder.started else 0.
        reference_offset=(started-recorder.started) if recorder and recorder.started else 0.
        for item in timeline:
            if real_null_sink:
                target=max(started+item["at"]/dry_run_scale,
                           previous_dispatch+dry_run_min_spacing)
                pause=target-time.monotonic()
                if pause>0:time.sleep(pause)
                previous_dispatch=time.monotonic()
            elif not args.dry_run:
                pause=started+item["at"]-time.monotonic()
                if pause>0:time.sleep(pause)
            log.add("step",action=item["action"],planned_s=item["at"],
                    release_s=item.get("release_s",.5))
            if item["action"]=="midi_burst":
                source.burst(item["notes"])
            else:
                engine.send(item["wire"])
        if not args.dry_run:
            remaining=started+total-time.monotonic()
            if remaining>0:time.sleep(remaining)
        if recorder:
            capture=recorder.stop()
        references=[]
        if args.render:
            references=run_references(
                folder/"offline_scripts",scripts,args.rate,args.block,args.render)
            manifest["offline_references"]=references
        if capture:
            from analyse import analyse
            if references:
                references=[{**ref,"capture_start_s":reference_offset+ref["start_s"]}
                            for ref in references if ref.get("audio")]
            analysis=analyse(capture,log.events,args.rate,capture_offset,references)
    except (RuntimeError,ValueError,OSError,TimeoutError,ImportError) as exc:
        error=str(exc)
        log.add("runner-error",message=error)
        manifest["warnings"].append("Run incomplete: "+error)
    finally:
        if recorder and recorder.started and not capture:
            try:recorder.stop()
            except Exception as exc:
                manifest["warnings"].append("Recorder cleanup: "+str(exc))
        if source:source.close()
        if engine:
            engine.stop()
            if engine.process is not None:
                manifest["engine_exit_code"]=engine.process.returncode
                if engine.process.returncode != 0:
                    error=error or f"engine exited with status {engine.process.returncode}"
                    manifest["warnings"].append("Nonzero native engine exit code")
        if engine and not args.dry_run:
            audio_samples=[e["payload"]["status"]["audio"] for e in log.events
                           if e.get("direction")=="out" and e.get("payload",{}).get("type")=="status"
                           and "audio" in e.get("payload",{}).get("status",{})]
            if audio_samples:
                observed=next((a for a in reversed(audio_samples) if a.get("deviceId")),audio_samples[-1])
                device=observed.get("deviceId") or args.device
                if device:manifest["audio_device"]=device
                for entry in engine.hello.get("audioDevices",[]) if engine.hello else []:
                    if entry.get("id")==device:
                        manifest["driver"]=entry.get("hostApi","unknown")
                        break
        manifest["completed"]=error is None
        (folder/"manifest.json").write_text(
            json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        report(folder,manifest,analysis,log.events,capture)
        log.close()
        print(folder/"report.md")
    if error:
        print("device harness: "+error,file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    sys.exit(main())
