#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""A12/M7r1.2: offline reanalysis of immutable #44229365015 ZIPs ONLY.

Never invokes a renderer, sidecar, Git, Callgrind or audio hardware. Phase one
classifies pitch from independently verified identical 48k original float PCM.
Phase two compares only originally recorded, unchanged estimator frequencies at
44.1/96 kHz for the rows already defined by their 48k spectrum.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import zipfile
from collections import Counter
import numpy as np

BASE_SHA = 'cdd608d517ffe3106897de7d80274768375d0e3c'
HEAD_SHA = '7bde1ee9603ae7f231d8d20ac130856b97fa8994'
RUN = 44229365015
ARTIFACTS = {
  'linux-x64': (14396920224,'cc241b117810eb323c0b3a6330ff8b454b8a80dfe31db23cd0a96753cb01a959'),
  'linux-arm64': (14394124427,'06e4a12199b9953007bae464d6aafe9c9b7016eb253820c3b56948fe8bfb15b3'),
}
METRICS_HASH='6fdeed51e121b62b6ef4b9fa16b773f4c5b42cc4d28db0d643697390bae09efe'
RATE=48000
HZS=(110,440,1760,3520,7040)
OFF=(44100,96000)
DOMINANCE_DB=1.0
MAX_DOWN_DB=40.0
PITCH_TOLERANCE_CENTS=2.0
MODEL_NAMES=(
  'Virtual Analog VCF','Phase Distortion','Six-op FM A','Six-op FM B',
  'Six-op FM C','Wave Terrain','String Machine','Chiptune',
  'Virtual Analog','Waveshaping','FM','Grain','Additive','Wavetable',
  'Chords','Speech','Swarm','Noise','Particle','String','Modal',
  'Bass Drum','Snare Drum','Hi-hat',
)


def digest(data): return hashlib.sha256(data).hexdigest()


def classify_spectrum(spec, hz, target, bin_radius=3):
    """Original estimator selects discrete peak in [0.8,1.2] target.

    Dominance is 20*log10(selected mag / biggest OTHER mag in the
    original 80-120% window excluding selected index +/-3). Level is
    20*log10(selected mag / global max non-DC mag).
    """
    arr=np.asarray(spec,dtype=np.float64)
    freq=np.asarray(hz,dtype=np.float64)
    if arr.ndim!=1 or freq.shape!=arr.shape or len(arr)<3 or not np.isfinite(arr).all() or np.any(arr<0):
        raise ValueError('invalid FFT magnitude and frequency input')
    if not (0 < target < float(freq[-1]) and len(freq)>4):
        raise ValueError('invalid note target')
    in_range = (freq >= max(1, target*0.8)) & (freq <= min(RATE*0.49,target*1.2))
    choices = np.flatnonzero(in_range)
    # Mirror original estimator's fallback, if the near-window has no FFT bins.
    peak=int(choices[np.argmax(arr[choices])]) if choices.size else int(np.argmax(arr[1:])+1)
    rival_mask=in_range.copy()
    rival_mask[max(0,peak-bin_radius):min(len(arr),peak+bin_radius+1)]=False
    rival_idx=np.flatnonzero(rival_mask)
    strongest = float(np.max(arr[rival_idx])) if rival_idx.size else None
    magnitude=float(arr[peak]); whole_max=float(np.max(arr[1:]))
    def db_ratio(a,b):
        if not np.isfinite(a) or not np.isfinite(b) or a<=0: return None
        if b == 0: return None # no meaningful finite measured rival, not guessed pass
        return 20*math.log10(a/b)
    dominance=db_ratio(magnitude,strongest) if strongest is not None else None
    level=db_ratio(magnitude,whole_max)
    dominance_margin=dominance-DOMINANCE_DB if dominance is not None else None
    level_margin=level+MAX_DOWN_DB if level is not None else None
    defined=(dominance_margin is not None and dominance_margin>=-1e-12 and
             level_margin is not None and level_margin>=-1e-12)
    reason='defined' if defined else ('no_valid_comparison_bin' if dominance is None else
       ('dominance_below_1dB' if dominance_margin<0 else 'level_more_than_40dB_below_global'))
    return {
      'pitch_defined':bool(defined), 'status':'pitch_defined' if defined else 'pitch_not_defined',
      'reason':reason,'selected_fft_bin':peak,'selected_bin_hz':float(freq[peak]),
      'selected_magnitude':magnitude, 'largest_competing_magnitude':strongest,
      'global_max_excluding_dc':whole_max,
      'dominance_db':dominance,'dominance_margin_vs_1dB':dominance_margin,
      'level_vs_global_db':level,'level_margin_vs_minus40dB':level_margin,
      'rival_excludes_bins_plusminus':bin_radius,
      'window_lower_hz':target*0.8,'window_upper_hz':target*1.2,
    }


def classify_pcm_48(pcm, target):
    x=np.frombuffer(pcm,dtype='<f4')
    if x.size!=RATE*2*2: raise ValueError('original two-second stereo 48k PCM size mismatch')
    if not np.isfinite(x).all(): raise ValueError('nonfinite original PCM')
    x=x.reshape(-1,2)[:,0].astype(np.float64)
    # Exact pre-existing bench/offline/metrics.py::oscillator_metrics FFT input:
    x=x[len(x)//5:]
    taper=np.hanning(len(x))
    magnitude=np.abs(np.fft.rfft(x*taper))
    hz=np.fft.rfftfreq(len(x),1./RATE)
    return classify_spectrum(magnitude,hz,target)


def pitch_decision(reference_classification, delta_cents):
    """A12: a defined row must pass +/-2 cents; missing data is not a pass."""
    if not reference_classification['pitch_defined']:
        return 'pitch_not_defined'
    if (not isinstance(delta_cents,(int,float)) or
        not math.isfinite(delta_cents)):
        return 'fail'
    return 'pass' if abs(delta_cents)<=PITCH_TOLERANCE_CENTS else 'fail'


def original_raw(zipf,entry,rate):
    if entry['status']!='measured_output':
        raise ValueError('unmeasured original PCM cannot certify pitch')
    info=entry['pcm'];path=info['file']
    data=zipf.read(path)
    if len(data)!=info['bytes_gzip'] or digest(data)!=info['sha256_gzip']:
        raise ValueError('compressed archive raw digest mismatch '+path)
    pcm=gzip.decompress(data)
    if len(pcm)!=info['bytes_original_pcm'] or digest(pcm)!=info['sha256_original_pcm']:
        raise ValueError('original 32-bit PCM digest mismatch '+path)
    if len(pcm)!=2*rate*2*4: raise ValueError('unexpected original PCM frame count '+path)
    return pcm


def source_row_key(entry): return (entry['model'],entry['sample_rate_hz'],entry['target_hz'])


def analysis_for(architecture,archive):
    artifact_id,expected_zip_sha=ARTIFACTS[architecture]
    blob=Path(archive).read_bytes()
    if digest(blob)!=expected_zip_sha: raise ValueError('ZIP SHA mismatch on '+architecture)
    with zipfile.ZipFile(archive) as zipf:
        if zipf.testzip() is not None: raise ValueError('bad ZIP CRC')
        bef=json.loads(zipf.read('pitch-before.json'))
        head=json.loads(zipf.read('pitch-head.json'))
        summ=json.loads(zipf.read('summary.json'))
        if (bef['source']['source_commit']!=BASE_SHA or head['source']['source_commit']!=HEAD_SHA or
            summ['source']!={'before':BASE_SHA,'head':HEAD_SHA}):
            raise ValueError('source pins mismatch')
        for doc in (bef,head):
            if doc['source']['source_hashes']['bench/offline/metrics.py']!=METRICS_HASH:
                raise ValueError('original estimator source SHA mismatch')
        rows_b={source_row_key(r):r for r in bef['rows']}
        rows_h={source_row_key(r):r for r in head['rows']}
        if len(rows_b)!=120 or len(rows_h)!=360 or set(rows_b)!={(m,48000,t) for m in range(24) for t in HZS} or set(rows_h)!={(m,rate,t) for m in range(24) for rate in (44100,48000,96000) for t in HZS}:
            raise ValueError('row matrix incomplete/duplicate')
        # Phase 1: read/check original 48k before and head, independently classify only identical bytes.
        reference={}; raw_hashes={}
        for m in range(24):
            for t in HZS:
                b,h=rows_b[m,48000,t],rows_h[m,48000,t]
                bp=original_raw(zipf,b,48000)
                hp=original_raw(zipf,h,48000)
                if bp!=hp: raise ValueError('48k before/head not byte identical')
                classification=classify_pcm_48(bp,t)
                reference[m,t]=classification
                raw_hashes[m,t]=b['pcm']['sha256_original_pcm']
        # Phase 2: verify every off-rate raw byte stream and use ORIGINAL recorded estimator.
        rows=[]
        for m in range(24):
            for t in HZS:
                ref=reference[m,t]
                f48=rows_h[m,48000,t]['estimator']['observed_hz']
                for r in OFF:
                    off=rows_h[m,r,t]
                    original_raw(zipf,off,r)
                    f=off['estimator']['observed_hz']
                    delta=(1200*math.log2(f/f48) if isinstance(f,(float,int)) and isinstance(f48,(float,int)) and f>0 and f48>0 else None)
                    decision=pitch_decision(ref,delta)
                    rows.append({
                        'architecture':architecture,'model':m,'model_name':MODEL_NAMES[m],
                        'target_hz':t,'rate_hz':r,'status':decision,
                        'selected_bin':ref['selected_fft_bin'],'selected_bin_hz_48':ref['selected_bin_hz'],
                        'dominance_db':ref['dominance_db'],
                        'dominance_margin_vs_1dB':ref['dominance_margin_vs_1dB'],
                        'level_vs_global_db':ref['level_vs_global_db'],
                        'level_margin_vs_minus40dB':ref['level_margin_vs_minus40dB'],
                        'classification_reason':ref['reason'],
                        'original_estimator_48_hz':f48,'original_estimator_off_hz':f,
                        'original_estimator_delta_cents':delta,
                        'sha256_48k_original_pcm':raw_hashes[m,t],
                        'sha256_off_original_pcm':off['pcm']['sha256_original_pcm'],
                        'original_pcm_file':off['pcm']['file'],
                    })
        return {'schema':'wirescape/macro-a12-applicability/1','source_run':RUN,
                'artifact_id':artifact_id,'zip_sha256':expected_zip_sha,
                'sources':{'before':BASE_SHA,'head':HEAD_SHA},
                'original_estimator_sha256':METRICS_HASH,
                'method':{'48k_input':'identical before/head source bytes 2s float32 stereo, left channel, last 80%',
                          'fft':'original Hann window rfft, selected near-bin maximum in 80-120% of target',
                          'selected_bin_dominance_min_db':DOMINANCE_DB,
                          'dominance_excludes_plusminus_bins':3,
                          'selected_bin_global_margin_db':MAX_DOWN_DB,
                          'defined_rows_max_abs_delta_cents':PITCH_TOLERANCE_CENTS},
                'rows':rows,'classifications_48k':[
                  {'model':m,'model_name':MODEL_NAMES[m],'target_hz':t,
                   **reference[m,t],'sha256_original_pcm':raw_hashes[m,t]}
                  for m in range(24) for t in HZS],
                'classifications':dict(Counter(r['status'] for r in rows))}


def aggregate(analyses):
    totals=Counter()
    models=[]
    for a in analyses:totals.update(a['classifications'])
    for m,name in enumerate(MODEL_NAMES):
        per_arch=[]
        for a in analyses:
            rr=[r for r in a['rows'] if r['model']==m]
            per_arch.append({'architecture':rr[0]['architecture'],**Counter(r['status'] for r in rr),
                'defined_48k_target_hz':sorted({r['target_hz'] for r in rr if r['status']!='pitch_not_defined'}),
                'failed_positions':[[r['target_hz'],r['rate_hz'],r['original_estimator_delta_cents']] for r in rr if r['status']=='fail']})
        models.append({'model':m,'model_name':name,'architectures':per_arch,
                       'no_defined_pitch_either_arch':all(not x['defined_48k_target_hz'] for x in per_arch)})
    return {'source_run':RUN,'counts_total':dict(totals),'per_model':models,
            'any_failed_defined_pitch':totals['fail']>0,
            'no_defined_pitch_models':[f"{r['model']:02d} {r['model_name']}" for r in models if r['no_defined_pitch_either_arch']]}


def fnum(x,places=3):return '—' if x is None else f'{x:.{places}f}'


def row_markdown(arch):
    rows=['| Model | Target Hz | Rate Hz | Dom dB | Dom margin dB | Level rel max dB | Level margin dB | Δ cents | A12 |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for x in arch['rows']:
        rows.append('| %02d %s | %d | %d | %s | %s | %s | %s | %s | **%s** |'%(
            x['model'],x['model_name'],x['target_hz'],x['rate_hz'],fnum(x['dominance_db']),
            fnum(x['dominance_margin_vs_1dB']),fnum(x['level_vs_global_db']),
            fnum(x['level_margin_vs_minus40dB']),fnum(x['original_estimator_delta_cents']),x['status']))
    return '\n'.join(rows)+'\n'


def summary_markdown(agg,analyses):
    out=['# A12 Macro pitch applicability — original run 44229365015 (no recapture)',
         '',f'Before `{BASE_SHA}`; after `{HEAD_SHA}`. Original estimator SHA256 `{METRICS_HASH}`.',
         '', 'A12 48k reference rows selected only from byte-identical before/head render. Dominance ≥1 dB; level ≥−40 dB relative to non-DC global peak. Original FFT peak estimator and ±2 cents unchanged.',
         '', '| Arch | Defined pass | Defined fail | Pitch not defined | Original ZIP SHA256 |',
         '|---|---:|---:|---:|---|']
    for a in analyses:
        out.append('| %s | %s | %s | %s | `%s` |' %(
          a['rows'][0]['architecture'],a['classifications'].get('pass',0),a['classifications'].get('fail',0),
          a['classifications'].get('pitch_not_defined',0),a['zip_sha256']))
    out+=['', '| Model / pinned Plaits voice.cc registration order | x64 defined Hz | x64 pass/fail/undefined | ARM64 defined Hz | ARM64 pass/fail/undefined |',
          '|---|---|---|---|---|']
    for r in agg['per_model']:
        a,b=r['architectures']
        fmt=lambda z: f"{z.get('pass',0)}/{z.get('fail',0)}/{z.get('pitch_not_defined',0)}"
        out.append('| %02d %s | %s | %s | %s | %s |'%(
           r['model'],r['model_name'],','.join(map(str,a['defined_48k_target_hz'])) or 'none',fmt(a),
           ','.join(map(str,b['defined_48k_target_hz'])) or 'none',fmt(b)))
    out+=['','**Models with no defined 48k pitch target in either architecture:** '+(', '.join(agg['no_defined_pitch_models']) or 'none'),
          '', '**Defined-pitch failure rows are real S7.4 defects for the #210 writer, not noise-model exceptions.**',
          '']
    for a in analyses:
        errors=[r for r in a['rows'] if r['status']=='fail']
        out+=['### '+a['rows'][0]['architecture']+' defined-pitch failures','',
              '| Model | Target | Rate | Dominance margin | Level margin | Δ cents |',
              '|---|---:|---:|---:|---:|---:|']
        for r in errors:
            out.append(f"| {r['model']:02d} {r['model_name']} | {r['target_hz']} | {r['rate_hz']} | {fnum(r['dominance_margin_vs_1dB'])} | {fnum(r['level_margin_vs_minus40dB'])} | {fnum(r['original_estimator_delta_cents'])} |")
        if not errors:out.append('| none | — | — | — | — | — |')
        out+=['']
    return '\n'.join(out)+'\n'


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--x64',type=Path,required=True)
    p.add_argument('--arm64',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    arg=p.parse_args(argv)
    arg.out.mkdir(parents=True,exist_ok=True)
    runs=[analysis_for('linux-x64',arg.x64),analysis_for('linux-arm64',arg.arm64)]
    agg=aggregate(runs)
    for a in runs:
        arch=a['rows'][0]['architecture']
        (arg.out/f'A12_{arch}_rows.json').write_text(json.dumps(a,indent=2,sort_keys=True,allow_nan=False)+'\n')
        (arg.out/f'A12_{arch}_rows.md').write_text(row_markdown(a))
    (arg.out/'A12_model_summary.json').write_text(json.dumps(agg,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (arg.out/'A12_summary.md').write_text(summary_markdown(agg,runs))
    print(json.dumps({'per_arch':{r['rows'][0]['architecture']:r['classifications'] for r in runs},
           'total':agg['counts_total'], 'no_defined_models':agg['no_defined_pitch_models'],
           'failed':{a['rows'][0]['architecture']:[(r['model'],r['target_hz'],r['rate_hz'],round(r['original_estimator_delta_cents'],4)) for r in a['rows'] if r['status']=='fail'] for a in runs}},indent=2))

if __name__=='__main__':main()
