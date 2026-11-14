# SPDX-License-Identifier: GPL-3.0-only
"""Device-free audio metrics, detectors, alignment, plots and report rendering."""
import json
import math
from pathlib import Path


def _np():
    import numpy as np
    return np


def _mono(samples):
    np=_np()
    a=np.asarray(samples,dtype=np.float64)
    if a.ndim==2:
        a=np.max(np.abs(a),axis=1)*np.sign(a[:,0]+1e-20)
    if a.ndim!=1 or not np.isfinite(a).all():
        raise ValueError("audio must contain finite mono/stereo samples")
    return a


def metrics(samples):
    np=_np()
    x=np.asarray(samples,dtype=np.float64)
    if not x.size:return {"rms":0.,"peak":0.,"dc":0.}
    return {"rms":round(float(np.sqrt(np.mean(x*x))),9),
            "peak":round(float(np.max(np.abs(x))),9),
            "dc":round(float(np.mean(x)),9)}


def detect_clicks(samples,rate,threshold=.18):
    """Isolated high-passed first-difference outliers; merge clusters within 2ms."""
    np=_np()
    x=_mono(samples)
    if len(x)<5:return []
    from scipy.ndimage import uniform_filter1d
    delta=np.diff(x)
    hp=delta-uniform_filter1d(delta,size=max(5,round(rate*.003)),mode="nearest")
    mad=float(np.median(np.abs(hp-np.median(hp))))
    cutoff=max(threshold,14*1.4826*mad)
    points=np.flatnonzero(np.abs(hp)>cutoff)+1
    result=[]
    last=-rate
    for idx in points:
        if idx-last>=max(2,round(rate*.002)):
            result.append(round(float(idx/rate),6))
        last=int(idx)
    return result


def detect_dropouts(samples,rate,min_ms=8,floor=1e-7,context_ms=30):
    """Silence runs bounded by active audio (not legitimate start/end silence)."""
    np=_np()
    x=_mono(samples)
    if not x.size:return []
    silent=np.abs(x)<=floor
    changes=np.diff(np.r_[False,silent,False].astype("int8"))
    starts=np.flatnonzero(changes==1)
    ends=np.flatnonzero(changes==-1)
    length=max(2,round(rate*min_ms/1000))
    context=max(4,round(rate*context_ms/1000))
    result=[]
    for start,end in zip(starts,ends):
        if end-start<length or start==0 or end>=len(x):continue
        a=x[max(0,start-context):start]
        b=x[end:min(len(x),end+context)]
        if a.size and b.size and max(float(np.sqrt(np.mean(a*a))),float(np.sqrt(np.mean(b*b))))>.002:
            result.append({"start_s":round(start/rate,6),"duration_ms":round(1000*(end-start)/rate,3)})
    return result


def detect_discontinuities(samples,rate,threshold=.25):
    np=_np()
    x=_mono(samples)
    return [round((i+1)/rate,6) for i in np.flatnonzero(np.abs(np.diff(x))>threshold)]


def detect_stuck_notes(samples,rate,note_off_s,release_s=.5,threshold_ratio=.22,floor=.004):
    """Energy remaining after release; a diagnostic only, not certain stuck MIDI."""
    np=_np()
    x=_mono(samples)
    pos=round((note_off_s+release_s)*rate)
    before=x[max(0,round((note_off_s-.1)*rate)):max(0,round(note_off_s*rate))]
    after=x[max(0,pos):min(len(x),pos+round(.15*rate))]
    if not len(before) or not len(after):return False
    early=math.sqrt(float(np.mean(before**2)))
    late=math.sqrt(float(np.mean(after**2)))
    return early>=floor and late>=max(floor,early*threshold_ratio)


def align_reference(reference,observed,rate,observed_rate=None,max_latency_s=.75):
    np=_np()
    from scipy import signal
    x=_mono(reference)
    y=_mono(observed)
    if observed_rate and observed_rate!=rate:
        from math import gcd
        g=gcd(rate,observed_rate)
        y=signal.resample_poly(y,rate//g,observed_rate//g)
    size=min(len(x),round(rate*1.0))
    limit=min(round(rate*max_latency_s),len(y)-size)
    if size<10 or limit<0:
        return {"available":False,"reason":"insufficient signal for alignment"}
    template=x[:size]-np.mean(x[:size])
    corr=signal.correlate(y[:size+limit],template,mode="valid",method="fft")
    lag=int(np.argmax(np.abs(corr)))
    segment=y[lag:lag+size]-np.mean(y[lag:lag+size])
    denom=float(np.linalg.norm(template)*np.linalg.norm(segment))
    confidence=float(abs(np.dot(template,segment))/denom) if denom>1e-10 else 0.
    gain=float(np.dot(template,segment)/max(np.dot(template,template),1e-12))
    diff=segment-gain*template
    return {"available":True,"latency_ms":round(1000*lag/rate,3),
            "correlation":round(confidence,5),"gain":round(gain,5),
            "difference_rms":metrics(diff)["rms"],
            "extra_clicks":max(0,len(detect_clicks(segment,rate))-len(detect_clicks(template,rate)))}


def analyse(path,events,rate,start_offset_s=0.,references=None):
    """Analyse FLAC in bounded chunks, including long 60-minute owner recordings."""
    import bisect
    import soundfile as sf
    import numpy as np
    with sf.SoundFile(str(path)) as source:
        sr,channels,total=source.samplerate,source.channels,len(source)
        duration=total/sr
        timeline=[e for e in events if e.get("direction")=="step"]
        boundaries=[min(total,max(0,round((float(e.get("elapsed_s",0))+start_offset_s)*sr)))
                    for e in timeline]
        sums=[{"n":0,"sq":0.,"sum":0.,"peak":0.} for _ in timeline]
        allsum={"n":0,"sq":0.,"sum":0.,"peak":0.}
        clicks=[]
        dropouts=[]
        discontinuities=[]
        seen_dropouts=set()
        history=np.empty(0,dtype=np.float64)
        overlap=max(10,round(.12*sr))

        def accumulate(bucket,segment):
            if not len(segment):return
            a=np.asarray(segment,dtype=np.float64)
            bucket["n"]+=a.size
            bucket["sq"]+=float(np.sum(a*a))
            bucket["sum"]+=float(np.sum(a))
            bucket["peak"]=max(bucket["peak"],float(np.max(np.abs(a))))

        frame=0
        while frame<total:
            block=source.read(min(65536,total-frame),dtype="float32",always_2d=True)
            if not len(block):break
            mono=_mono(block)
            accumulate(allsum,block)
            at=frame
            i=bisect.bisect_right(boundaries,at)-1
            while at<frame+len(block):
                next_boundary=(boundaries[i+1] if i+1<len(boundaries) else total)
                end=min(frame+len(block),max(at+1,next_boundary))
                if i>=0:accumulate(sums[i],block[at-frame:end-frame])
                at=end
                i=bisect.bisect_right(boundaries,at)-1
            joined=np.concatenate((history,mono))
            begin=frame-len(history)
            for t in detect_clicks(joined,sr):
                pos=round(t*sr)+begin
                if frame<=pos<frame+len(block) and len(clicks)<50000:
                    sec=round(pos/sr,6)
                    clicks.append(sec)
            for d in detect_dropouts(joined,sr):
                pos=round(d["start_s"]*sr)+begin
                if pos>=0 and pos not in seen_dropouts:
                    seen_dropouts.add(pos)
                    if len(dropouts)<50000:
                        dropouts.append({"start_s":round(pos/sr,6),
                                         "duration_ms":d["duration_ms"]})
            for t in detect_discontinuities(joined,sr):
                pos=round(t*sr)+begin
                if frame<=pos<frame+len(block) and len(discontinuities)<50000:
                    discontinuities.append(round(pos/sr,6))
            history=joined[-overlap:]
            frame+=len(block)

        def finish(bucket):
            if not bucket["n"]:return {"rms":0.,"peak":0.,"dc":0.}
            return {"rms":round(math.sqrt(bucket["sq"]/bucket["n"]),9),
                    "peak":round(bucket["peak"],9),
                    "dc":round(bucket["sum"]/bucket["n"],9)}

        steps=[]
        for i,event in enumerate(timeline):
            at=boundaries[i]/sr
            out=finish(sums[i])
            following=boundaries[i+1]/sr if i+1<len(boundaries) else duration
            out.update({"at_s":round(at,4),"action":event.get("action"),
                        "clicks_s":[t for t in clicks if at<=t<following],
                        "dropouts":[d for d in dropouts if at<=d["start_s"]<following]})
            if event.get("action")=="patch_switch" and steps:
                out["loudness_jump_db"]=round(
                    20*math.log10(max(out["rms"],1e-9)/max(steps[-1]["rms"],1e-9)),3)
            if event.get("action")=="noteOff":
                def window_rms(left,right):
                    a=max(0,min(total,round(left*sr)))
                    b=max(a,min(total,round(right*sr)))
                    source.seek(a)
                    data=source.read(b-a,dtype="float32")
                    return finish_from_audio(data)
                def finish_from_audio(data):
                    if not len(data):return 0.
                    return math.sqrt(float(np.mean(np.asarray(data,dtype=np.float64)**2)))
                rel=float(event.get("release_s",.5))
                early=window_rms(at-.1,at)
                late=window_rms(at+rel,at+rel+.15)
                out["possible_stuck_note"]=early>=.004 and late>=max(.004,early*.22)
            steps.append(out)
        result={"recording":Path(path).name,"rate":sr,"channels":channels,
                "duration_s":round(duration,3),"overall":finish(allsum),
                "clicks_s":clicks,"dropouts":dropouts,
                "discontinuities_s":discontinuities,"steps":steps}
    if references:
        result["references"]=[]
        for item in references:
            f=Path(item["audio"])
            if not f.is_file():continue
            start=max(0,round((item["start_s"]+start_offset_s)*sr))
            with sf.SoundFile(str(path)) as capture, sf.SoundFile(str(f)) as ref:
                capture.seek(start)
                expected=ref.read(dtype="float32",always_2d=True)
                observed=capture.read(len(expected)+round(sr*.75),dtype="float32",
                                      always_2d=True)
                result["references"].append({"file":f.name,
                    **align_reference(expected,observed,ref.samplerate,sr)})
    return result


def plot(folder,audio_path):
    if not audio_path or not Path(audio_path).exists():return []
    try:
        import soundfile as sf
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        with sf.SoundFile(str(audio_path)) as source:
            stride=max(1,len(source)//3000)
            times=[]
            amplitudes=[]
            frame=0
            while True:
                a=source.read(65536,dtype="float32",always_2d=True)
                if not len(a):break
                first=(-frame)%stride
                positions=np.arange(first,len(a),stride)
                times.extend((frame+positions)/source.samplerate)
                amplitudes.extend(a[positions,0])
                frame+=len(a)
        fig,ax=plt.subplots(figsize=(8,2),dpi=70)
        ax.plot(times,amplitudes,linewidth=.4)
        ax.set(xlabel="Seconds",ylabel="Amplitude",title="Recorded waveform")
        fig.tight_layout()
        name=Path(folder)/"waveform.png"
        fig.savefig(name,dpi=70)
        plt.close(fig)
        if name.stat().st_size<=200000:return ["waveform.png"]
        name.unlink()
    except (ImportError,RuntimeError,ValueError):
        pass
    return []


def report(folder,manifest,analysis,events,audio_path=None):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"analysis.json").write_text(json.dumps(analysis,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    acks=[e["latency_ms"] for e in events if "latency_ms" in e]
    status=[e["payload"]["status"]["audio"] for e in events
            if e.get("direction")=="out" and e.get("payload",{}).get("type")=="status"
            and "audio" in e.get("payload",{}).get("status",{})]
    cpu=[x["cpuPercent"] for x in status if isinstance(x.get("cpuPercent"),(int,float))]
    drop=[x["dropouts"] for x in status if isinstance(x.get("dropouts"),(int,float))]
    def percentile(v,p):
        if not v:return "n/a"
        v=sorted(v)
        return f"{v[round((len(v)-1)*p)]:.3f}"
    lines=["# Device stress harness report","",
           "Mode: **"+("DRY RUN (no hardware evidence)" if manifest.get("dry_run") else "owner device run")+"**","",
           f"Commit: {manifest['commit']} · Rate: {manifest['rate']} Hz · Block: {manifest['block']} frames",
           f"Platform: {manifest['os']} · CPU: {manifest['cpu']} · Device: {manifest.get('audio_device','unknown')}","",
           "## Protocol and device metrics","","| Metric | Value |","|---|---:|",
           f"| Acknowledged commands | {len(acks)} |",
           f"| Ack p50/p95/p99 (ms) | {percentile(acks,.5)} / {percentile(acks,.95)} / {percentile(acks,.99)} |",
           f"| CPU max (%) | {max(cpu) if cpu else 'n/a'} |",
           f"| Dropouts (latest counter) | {drop[-1] if drop else 'n/a'} |",
           f"| Refused replies | {sum(e.get('payload',{}).get('ok') is False for e in events if e.get('direction')=='out')} |",
           f"| Status/telemetry pushes | {sum(e.get('payload',{}).get('type')=='status' for e in events)} / {sum(e.get('payload',{}).get('type')=='telemetry' for e in events)} |",""]
    if "overall" in analysis:
        a=analysis["overall"]
        lines+=["## Recorded signal","","| RMS | Peak | DC | Clicks | Dropouts |",
                "|---:|---:|---:|---:|---:|",
                f"| {a['rms']} | {a['peak']} | {a['dc']} | {len(analysis['clicks_s'])} | {len(analysis['dropouts'])} |",
                "","## Per-step audio metrics","","| Time (s) | Action | RMS | Peak | DC | Clicks | Dropouts |",
                "|---:|---|---:|---:|---:|---:|---:|"]
        if len(analysis["steps"])>500:
            lines.append("| ... | Remaining per-step metrics in analysis.json | ... | ... | ... | ... | ... |")
        for a in analysis["steps"][:500]:
            lines.append(f"| {a['at_s']} | {a['action']} | {a['rms']:.5f} | {a['peak']:.5f} | {a['dc']:.5f} | {len(a['clicks_s'])} | {len(a['dropouts'])} |")
    else:
        lines+=["## Recording","","No audio recorded; signal metrics are unavailable.",""]
    if manifest.get("warnings"):
        lines+=["## Limitations","",*["- "+w for w in manifest["warnings"]],""]
    for name in plot(folder,audio_path):
        lines.append(f"![Waveform]({name})")
    (folder/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return folder/"report.md"
