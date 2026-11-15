#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compare PCM16 WAVE renders from apps/offline_render.cpp and JS reference.
Standard library only. Results are signal statistics, not a Praat or LUFS substitute.
"""
import argparse, array, math, pathlib, sys, wave
CASES=['plain','clean','weathered','raspy','chant_voice','growl','fry','ayn','ring','whisper','small','kargyraa','ensemble16']
def read(file):
    with wave.open(str(file),'rb') as f:
        if f.getnchannels()!=2 or f.getsampwidth()!=2:raise RuntimeError('expected PCM16 stereo '+str(file))
        rate=f.getframerate();a=array.array('h');a.frombytes(f.readframes(f.getnframes()))
    if sys.byteorder=='big':a.byteswap()
    return rate,a

def sums(a,b,frames):
    count=min(frames*2,len(a),len(b))
    aa=bb=ab=delta=0.
    for x,y in zip(a[:count],b[:count]):
        aa+=x*x;bb+=y*y;ab+=x*y;delta+=(x-y)*(x-y)
    ra=math.sqrt(aa/count)/32767;rb=math.sqrt(bb/count)/32767
    d=20*math.log10(max(1e-20,ra)/max(1e-20,rb))
    corr=ab/math.sqrt(max(1e-40,aa*bb))
    res=20*math.log10(max(1e-20,math.sqrt(delta/count))/max(1e-20,math.sqrt(bb/count)))
    return ra,rb,d,corr,res

def main():
    p=argparse.ArgumentParser();p.add_argument('cpp_dir');p.add_argument('js_dir');p.add_argument('--output');args=p.parse_args()
    rows=[]
    for c in CASES:
        ca=pathlib.Path(args.cpp_dir)/f'{c}.wav';jb=pathlib.Path(args.js_dir)/f'{c}.wav'
        if not ca.exists() or not jb.exists():continue
        rate,a=read(ca);other,b=read(jb)
        if rate!=other or len(a)!=len(b):raise RuntimeError(c+' shape/rate mismatch')
        sustain=sums(a,b,int(rate*.8));whole=sums(a,b,len(a)//2)
        rows.append((c,sustain,whole))
    lines=['| Case | JS RMS | C++ RMS | Sustain Δ dB | Whole Δ dB | Sustain correlation |',
           '|---|---:|---:|---:|---:|---:|']
    for c,s,w in rows:
        lines.append(f'| {c} | {w[1]:.5f} | {w[0]:.5f} | {s[2]:+.2f} | {w[2]:+.2f} | {s[3]:.3f} |')
    lines+=['',f'Plain deterministic residual: **{next(s[4] for c,s,w in rows if c=="plain"):.2f} dB** relative to reference (sustain).',
            'RMS dB differences are not LUFS or Praat measurements.']
    report='\n'.join(lines)+'\n'
    if args.output:pathlib.Path(args.output).write_text(report)
    print(report)
if __name__=='__main__':main()
