# SPDX-License-Identifier: GPL-3.0-only
"""Compare per-architecture device-free golden JSONs; no audio data is committed."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np


def first_float32_difference(before, after):
    """Exact interleaved stereo sample index when both temporary WAVs exist."""
    def samples(path):
        raw=Path(path).read_bytes()
        if len(raw)<44 or raw[:4]!=b"RIFF" or raw[8:16]!=b"WAVEfmt " or raw[36:40]!=b"data":
            raise ValueError("expected float32 WAV for sample-index comparison")
        size=struct.unpack_from("<I",raw,40)[0]
        if size!=len(raw)-44 or size%4:
            raise ValueError("invalid PCM length in WAV")
        return np.frombuffer(raw,dtype="<u4",offset=44)
    a,b=samples(before),samples(after)
    n=min(len(a),len(b))
    unequal=np.flatnonzero(a[:n]!=b[:n])
    if len(unequal):
        return int(unequal[0])
    return n if len(a)!=len(b) else None


def compare(before,after,tolerance_db=0.0,raw_before=None,raw_after=None):
    if tolerance_db<0 or not math.isfinite(tolerance_db):
        raise ValueError("tolerance must be a finite nonnegative dB value")
    for key in ("machine","sample_rate_hz","block_frames","seconds","seed","channels"):
        if before.get(key)!=after.get(key):
            raise ValueError(f"incompatible golden reference: {key}")
    result={}
    first=before.get("patches",{})
    second=after.get("patches",{})
    for name in sorted(set(first)|set(second)):
        a,b=first.get(name),second.get(name)
        if a is None or b is None:
            result[name]=dict(status="different",largest_band_difference_db=None,
                              first_differing_sample_index=None,
                              reason="patch missing from one reference")
            continue
        ab=a["third_octave_bands"]
        bb=b["third_octave_bands"]
        if len(ab)!=31 or len(bb)!=31:
            raise ValueError(f"{name}: expected 31 one-third-octave bands")
        if any(x["center_hz"]!=y["center_hz"] for x,y in zip(ab,bb)):
            raise ValueError(f"{name}: incompatible band centers")
        largest=max(abs(x["level_dbfs"]-y["level_dbfs"]) for x,y in zip(ab,bb))
        identical=a["sha256_float32_pcm"]==b["sha256_float32_pcm"]
        if identical:
            status="identical"
        elif tolerance_db>0 and largest<=tolerance_db:
            status="within tolerance"
        else:
            status="different"
        index=None
        if not identical and raw_before is not None and raw_after is not None:
            wavname=Path(name).with_suffix(".wav")
            path_a=Path(raw_before)/wavname
            path_b=Path(raw_after)/wavname
            if path_a.is_file() and path_b.is_file():
                index=first_float32_difference(path_a,path_b)
        result[name]=dict(status=status,
                          largest_band_difference_db=round(largest,6),
                          first_differing_sample_index=index,
                          sample_index_scope="interleaved stereo float32; null when WAVs not supplied",
                          reason=None if identical or index is not None else
                                 "exact index unavailable from SHA-256 and band summaries alone")
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("before",type=Path)
    p.add_argument("after",type=Path)
    p.add_argument("--tolerance-db",type=float,default=0.0)
    p.add_argument("--before-wavs",type=Path,help="optional temporary WAV tree; never commit")
    p.add_argument("--after-wavs",type=Path,help="optional temporary WAV tree; never commit")
    args=p.parse_args(argv)
    try:
        before=json.loads(args.before.read_text(encoding="utf-8"))
        after=json.loads(args.after.read_text(encoding="utf-8"))
        rows=compare(before,after,args.tolerance_db,args.before_wavs,args.after_wavs)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        p.error(str(exc))
    changed=False
    for name,item in rows.items():
        largest=item["largest_band_difference_db"]
        diff=f"{largest:.6f} dB" if largest is not None else "n/a"
        index=item["first_differing_sample_index"]
        print(f"{name}: {item['status']}; largest band difference={diff}; "
              f"first differing sample index={index if index is not None else 'unavailable (hash only)'}")
        if item["status"]=="different":changed=True
    return 1 if changed else 0


if __name__=="__main__":
    sys.exit(main())
