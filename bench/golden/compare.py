# SPDX-License-Identifier: GPL-3.0-only
"""Compare golden renders, preserving first changed PCM sample on same-runner A/B.

Primary PR gate: two checkouts rendered on one runner, bit-exact (tolerance 0).
Secondary archival check: architecture reference, spectral warning (0.01 dB).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import struct
import sys

import numpy as np


def _wav_samples(path):
    raw = Path(path).read_bytes()
    if len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:16] != b"WAVEfmt " or raw[36:40] != b"data":
        raise ValueError(f"{path}: expected stereo float32 RIFF WAV")
    fmt = struct.unpack_from("<IHHIIHH", raw, 16)
    if fmt[0] != 16 or fmt[1] != 3 or fmt[2] != 2 or fmt[-1] != 32 or fmt[-2] != 8:
        raise ValueError(f"{path}: unexpected float32 stereo WAV format")
    size = struct.unpack_from("<I", raw, 40)[0]
    if size != len(raw) - 44 or size % 8:
        raise ValueError(f"{path}: PCM length invalid")
    return raw[44:], fmt[3]


def wav_difference_metrics(before, after):
    """Exact interleaved sample, sample-frame time, peak absolute sample delta."""
    left, rate_a = _wav_samples(before)
    right, rate_b = _wav_samples(after)
    if rate_a != rate_b:
        raise ValueError("WAV sample rates differ")
    aa = np.frombuffer(left, dtype="<u4")
    bb = np.frombuffer(right, dtype="<u4")
    n = min(len(aa), len(bb))
    changed = np.flatnonzero(aa[:n] != bb[:n])
    index = int(changed[0]) if len(changed) else (n if len(aa) != len(bb) else None)
    values_a = np.frombuffer(left, dtype="<f4")[:n].astype(np.float64)
    values_b = np.frombuffer(right, dtype="<f4")[:n].astype(np.float64)
    peak = float(np.max(np.abs(values_a - values_b))) if n else 0.0
    return {
        "first_differing_sample_index": index,
        "first_differing_frame_index": index // 2 if index is not None else None,
        "first_differing_time_s": (index // 2) / rate_a if index is not None else None,
        "peak_sample_difference_fs": peak,
    }


def first_float32_difference(before, after):
    return wav_difference_metrics(before, after)["first_differing_sample_index"]


def parse_sound_changes(body, names):
    """Accept only explicit Sound-change: names — reason lines from PR description."""
    names = set(names)
    declared = set()
    for line in (body or "").splitlines():
        if not re.match(r"^\s*Sound-change\s*:", line, flags=re.I):
            continue
        parts = re.match(r"^\s*Sound-change\s*:\s*(.+?)\s+(?:—|–|-)\s+(\S.*)\s*$",
                         line, flags=re.I)
        if not parts:
            raise ValueError("Sound-change line requires patch names, em dash, and reason")
        value, reason = parts.groups()
        if not reason.strip():
            raise ValueError("Sound-change reason is required")
        tokens = [s.strip().strip("`") for s in value.split(",")]
        if not tokens or any(not s for s in tokens):
            raise ValueError("Sound-change contains an empty patch name")
        if len(tokens) == 1 and tokens[0].lower() == "all":
            declared.update(names)
            continue
        for token in tokens:
            if token in names:
                declared.add(token)
                continue
            matches = [name for name in names if Path(name).name == token]
            if len(matches) != 1:
                raise ValueError("Sound-change unknown or ambiguous patch: " + token)
            declared.add(matches[0])
    return declared


def compare(before, after, tolerance_db=0.0, raw_before=None, raw_after=None,
            declared=(), require_wavs=False, difference_wavs=None):
    if tolerance_db < 0 or not math.isfinite(tolerance_db):
        raise ValueError("tolerance must be finite, nonnegative dB")
    for key in ("machine", "sample_rate_hz", "block_frames", "seconds", "seed", "channels"):
        if before.get(key) != after.get(key):
            raise ValueError(f"incompatible golden reference: {key}")
    if bool(raw_before) != bool(raw_after):
        raise ValueError("both --before-wavs and --after-wavs are required together")
    if require_wavs and not (raw_before and raw_after):
        raise ValueError("--require-wavs needs both WAV directories")
    result = {}
    for name in sorted(set(before.get("patches", {})) | set(after.get("patches", {}))):
        a = before.get("patches", {}).get(name)
        b = after.get("patches", {}).get(name)
        wav_name = Path(name).with_suffix(".wav")
        path_a = Path(raw_before) / wav_name if raw_before else None
        path_b = Path(raw_after) / wav_name if raw_after else None
        identical = a is not None and b is not None and a["sha256_float32_pcm"] == b["sha256_float32_pcm"]
        if a is None or b is None:
            largest = None
            status = "different"
            reason = "patch missing from one reference"
        else:
            ab, bb = a["third_octave_bands"], b["third_octave_bands"]
            if len(ab) != 31 or len(bb) != 31:
                raise ValueError(f"{name}: expected 31 one-third-octave bands")
            if any(x["center_hz"] != y["center_hz"] for x, y in zip(ab, bb)):
                raise ValueError(f"{name}: incompatible band centers")
            largest = max(abs(x["level_dbfs"] - y["level_dbfs"]) for x, y in zip(ab, bb))
            status = ("identical" if identical else
                      "within tolerance" if tolerance_db > 0 and largest <= tolerance_db else
                      "different")
            reason = None
        pcm = dict(first_differing_sample_index=None, first_differing_frame_index=None,
                   first_differing_time_s=None, peak_sample_difference_fs=0.0 if identical else None)
        if path_a is not None and path_b is not None:
            if path_a.is_file() and path_b.is_file():
                pcm = wav_difference_metrics(path_a, path_b)
                # Hash mismatch but identical local WAV is an invalid artifact set.
                if not identical and a is not None and b is not None and pcm["first_differing_sample_index"] is None:
                    raise ValueError(f"{name}: hashes differ but WAVs are identical")
            elif require_wavs and a is not None and b is not None:
                raise ValueError(f"{name}: A/B WAV missing for existing patch")
        if difference_wavs and status != "identical" and status != "within tolerance":
            for path, folder in ((path_a, "before"), (path_b, "after")):
                if path and path.is_file():
                    dest = Path(difference_wavs) / folder / wav_name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, dest)
        if status == "different" and name in declared:
            status = "declared"
        result[name] = dict(status=status,
                            largest_band_difference_db=round(largest, 6) if largest is not None else None,
                            **pcm, reason=reason or (
                                "exact first sample unavailable from hash-only JSON" if not identical
                                and pcm["first_differing_sample_index"] is None else None))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--tolerance-db", type=float, default=0.0)
    parser.add_argument("--before-wavs", type=Path)
    parser.add_argument("--after-wavs", type=Path)
    parser.add_argument("--require-wavs", action="store_true")
    parser.add_argument("--difference-wavs", type=Path)
    parser.add_argument("--pr-event", type=Path, help="GitHub pull_request event JSON, never interpolated into shell")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        a = json.loads(args.before.read_text(encoding="utf-8"))
        b = json.loads(args.after.read_text(encoding="utf-8"))
        description = (json.loads(args.pr_event.read_text(encoding="utf-8"))
                       .get("pull_request", {}).get("body", "")) if args.pr_event else ""
        declared = parse_sound_changes(description, set(a.get("patches", {})) | set(b.get("patches", {})))
        rows = compare(a, b, args.tolerance_db, args.before_wavs, args.after_wavs,
                       declared, args.require_wavs, args.difference_wavs)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    different = False
    for name, row in rows.items():
        largest = row["largest_band_difference_db"]
        delta = f"{largest:.6f} dB" if largest is not None else "n/a"
        index = row["first_differing_sample_index"]
        print(f"{name}: {row['status']}; largest band difference={delta}; "
              f"first differing sample index={index if index is not None else 'unavailable (hash only)'}; "
              f"time={row['first_differing_time_s'] if row['first_differing_time_s'] is not None else 'n/a'} s; "
              f"peak sample difference={row['peak_sample_difference_fs']} FS")
        different |= row["status"] == "different"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps({
            "base_commit": a.get("commit"), "head_commit": b.get("commit"),
            "machine": b.get("machine"), "tolerance_db": args.tolerance_db,
            "declared": sorted(declared), "patches": rows,
            "different_count": sum(x["status"] == "different" for x in rows.values()),
            "declared_count": sum(x["status"] == "declared" for x in rows.values()),
        }, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 1 if different else 0


if __name__ == "__main__":
    sys.exit(main())
